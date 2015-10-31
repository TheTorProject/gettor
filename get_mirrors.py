# -*- coding: utf-8 -*-
#
# This file is part of GetTor
#
# :authors: Israel Leiva <ilv@torproject.org>
#           see also AUTHORS file
#
# :license: This is Free Software. See LICENSE for license information.

"""get_mirrors -- Download the list of tpo's mirrors for GetTor."""

import os
import json
import codecs
import logging
import argparse


from OpenSSL import SSL
from OpenSSL import crypto

from twisted.web import client
from twisted.python import log
from twisted.internet import ssl
from twisted.internet import defer
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.error import TimeoutError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import ConnectionRefusedError

from gettor import utils

# Associate each protocol with its column name in tor-mirrors.csv
PROTOS = {
    'https': 'httpsWebsiteMirror',
    'http': 'httpWebsiteMirror',
    'rsync': 'rsyncWebsiteMirror',
    'https-dist': 'httpsDistMirror',
    'http-dist': 'httpDistMirror',
    'rsync-dist': 'rsyncDistMirror',
    'ftp': 'ftpWebsiteMirror',
    'onion': 'hiddenServiceMirror',
}

# Tor Project's website certificate
# $ openssl s_client -showcerts -connect tpo:443 < /dev/null > tpo.pem
CERT_TPO = '/path/to/gettor/tpo.pem'


# Taken from get-tor-exits (BridgeDB)
class FileWriter(protocol.Protocol):
    """Read a downloaded file incrementally and write to file."""
    def __init__(self, finished, file):
        """Create a FileWriter.

        .. warning:: We currently only handle the first 2MB of a file. Files
            over 2MB will be truncated prematurely. *note*: this should be
            enough for the mirrors file.

        :param finished: A :class:`~twisted.internet.defer.Deferred` which
            will fire when another portion of the download is complete.
        """
        self.finished = finished
        self.remaining = 1024 * 1024 * 2
        self.fh = file

    def dataReceived(self, bytes):
        """Write a portion of the download with ``bytes`` size to disk."""
        if self.remaining:
            display = bytes[:self.remaining]
            self.fh.write(display)
            self.fh.flush()
            self.remaining -= len(display)

    def connectionLost(self, reason):
        """Called when the download is complete."""
        logging.info('Finished receiving mirrors list: %s'
                     % reason.getErrorMessage())
        self.finished.callback(None)


# Based in tor2web.utils.ssl (Tor2web)
class HTTPSVerifyingContextFactory(ssl.ClientContextFactory):
    def __init__(self, cn):
        self.cn = cn
        #
        # From https://docs.python.org/2/library/ssl.html#ssl-security
        #
        # "SSL versions 2 and 3 are considered insecure and are therefore
        # dangerous to use. If you want maximum compatibility between clients
        # and servers, it is recommended to use PROTOCOL_SSLv23 as the protocol
        # version and then disable SSLv2 and SSLv3 explicitly"
        #
        self.method = SSL.SSLv23_METHOD

    def getContext(self, hostname, port):
        """Get this connection's OpenSSL context.

        We disable SSLv2 and SSLv3. We also check the certificate received
        is the one we expect (using the "common name").

        """
        ctx = self._contextFactory(self.method)
        ctx.set_options(SSL.OP_NO_SSLv2)
        ctx.set_options(SSL.OP_NO_SSLv3)
        ctx.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
            self.verifyCN
        )

        return ctx

    def verifyCN(self, connection, x509, errno, depth, preverifyOK):
        # DEBUG: print "%s == %s ?" % (self.cn, x509.get_subject().commonName)

        # Somehow, if I don't set this to true, the verifyCN doesn't go
        # down in the chain, I don't know if this is OK
        verify = True
        if depth == 0:
            if self.cn == x509.get_subject().commonName:
                verify = True
            else:
                verify = False
        return verify


# Based in get-tor-exits (BridgeDB)
def handle(failure):
    """Handle a **failure**."""
    if failure.type == ConnectionRefusedError:
        logging.error("Couldn't download file; connection was refused.")
    elif failure.type == DNSLookupError:
        logging.error("Couldn't download file; domain resolution failed.")
    elif failure.type == TimeoutError:
        logging.error("Couldn't download file; connection timed out.")
    else:
        logging.error("Couldn't download file.")

    print "Couldn't download file. Check the log."
    os._exit(-1)


# Taken from get-tor-exits (BridgeDB)
def writeToFile(response, filename):
    """Write requested content to filename."""
    finished = defer.Deferred()
    response.deliverBody(FileWriter(finished, filename))
    return finished


def is_json(my_json):
    """Check if json generated is valid."""
    try:
        json_object = json.loads(my_json)
    except ValueError, e:
        return False
    return True


def add_tpo_link(url):
    """Add the download link for Tor Browser."""
    uri = 'projects/torbrowser.html.en#downloads'
    if url.endswith('/'):
        return "%s%s" % (url, uri)
    else:
        return "%s/%s" % (url, uri)


def add_entry(mirrors, columns, elements):
    """Add entry to mirrors list."""
    entry = {}
    count = 0
    for e in elements:
        e = e.replace("\n", '')
        entry[columns[count]] = e
        count = count + 1

    mirrors.append(entry)


def add_mirror(file, entry, proto):
    """Add mirror to mirrors list."""
    # if proto requested is http(s), we add link to download section
    if PROTOS[proto] == 'http' or PROTOS[proto] == 'https':
        uri = add_tpo_link(entry[proto])
    else:
        uri = entry[proto]
    
    file.write(
        "%s - by %s (%s)\n" % (
            uri,
            entry['orgName'],
            entry['subRegion'],
        )
    )


def main():
    """Script to get the list of tpo's mirrors from tpo and adapt it to
    be used by GetTor.

    Usage: python2.7 get_mirrors.py [-h] [--proto protocol]

    By default, the protocol is 'https'. Possible values of protcol are:

    http, https, rsync, ftp, onion, http-dist, https-dist, rsync-dist.

    """
    parser = argparse.ArgumentParser(
        description="Utility to download tpo's mirrors and make it usable\
        by GetTor."
    )

    parser.add_argument(
        '-p', '--proto',
        default='https',
        help='Protocol filter. Possible values: http, https, rsync, ftp, onion\
        http-dist, https-dist, rsync-dist. Default to https.')

    args = parser.parse_args()
    p = args.proto

    gettor_path = '/path/to/gettor/'
    csv_path = os.path.join(gettor_path, 'tor-mirrors.csv')
    json_path = os.path.join(gettor_path, 'tor-mirrors')
    mirrors_list = os.path.join(gettor_path, 'mirrors-list.txt')

    # Load tpo certificate and extract common name, we'll later compare this
    # with the certificate sent by tpo to check we're really taltking to it
    try:
        data = open(CERT_TPO).read()
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, data)
        cn_tpo = x509.get_subject().commonName
    except Exception as e:
        logging.error("Error with certificate: %s" % str(e))
        return

    # While we wait the json of mirrors to be implemented in tpo, we need
    # to download the csv file and transform it to json

    # The code below is based in get-tor-exits script from BridgeDB and
    # the tor2web.utils.ssl module from Tor2web
    url = 'https://www.torproject.org/include/tor-mirrors.csv'

    try:
        fh = open(csv_path, 'w')
    except IOError as e:
        logging.error("Could not open %s" % csv_path)
        return

    logging.info("Requesting %s..." % url)

    # If certificate don't match an exception will be raised
    # this is my first experience with twisted, maybe I'll learn to handle
    # this better some time in the future...
    contextFactory = HTTPSVerifyingContextFactory(cn_tpo)
    agent = client.Agent(reactor, contextFactory)
    d = agent.request("GET", url)
    d.addCallback(writeToFile, fh)
    d.addErrback(handle)
    d.addCallbacks(log.msg, log.err)

    if not reactor.running:
        d.addCallback(lambda ignored: reactor.stop())
        reactor.run()

    logging.info("File downloaded!")

    # Now transform it to json -- I couldn't find out how to use a
    # two-character delimiter with the csv package, so I decided to handle
    # the csv data by hand. We are doing this until #16601 gets deployed.
    # https://trac.torproject.org/projects/tor/ticket/16601

    # Code below is based in update-mirrors-json.py script from tpo

    # These are the names of each column e.g. adminContact
    columns = []
    # List of mirrors to be built
    mirrors = []

    logging.info("Transforming csv data into json...")
    logging.info("Getting data from csv")
    try:
        with codecs.open(csv_path, "rb", "utf-8") as csvfile:
            for line in csvfile:
                elements = line.split(", ")
                # first entry have the names of the columns
                if not columns:
                    columns = elements
                else:
                    add_entry(mirrors, columns, elements)
    except IOError as e:
        logging.error("Couldn't read csv file: %s" % str(e))
        return

    logging.info("Creating json")
    if is_json(json.dumps(mirrors)):
        try:
            with codecs.open(json_path, "w", "utf-8") as jsonfile:
                # Make pretty json
                json.dump(
                    mirrors,
                    jsonfile,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                    encoding="utf-8",
                )
        except IOError as e:
            logging.error("Couldn't write json: %s" % str(e))
            return
    else:
        logging.error("Invalid json file")
        return

    # Now make the mirrors list to be used by GetTor
    logging.info("Reading json")
    try:
        mirrors_json = codecs.open(json_path, "rb", "utf-8")
        mirrors = json.load(mirrors_json)
    except IOError as e:
        logging.error("Couldn't open %s" % json_path)
        return

    logging.info("Creating new list with protocol: %s" % p)
    try:
        list = codecs.open(mirrors_list, "w", "utf-8")
        for entry in mirrors:
            if args.proto is not 'all':
                for e in entry:
                    if e == PROTOS[p] and entry[PROTOS[p]]:
                        add_mirror(list, entry, PROTOS[p])
            else:
                for k, v in PROTOS:
                    if entry[v]:
                        add_mirror(list, entry, v)
        logging.info("List created: %s" % mirrors_list)
    except IOError as e:
        logging.error("Couldn't open %s" % mirrors_list)
        return

if __name__ == "__main__":
    logging_format = utils.get_logging_format()
    logging.basicConfig(
        filename='/path/to/gettor/log/get-mirrors.log',
        format=logging_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    logging.info("Started")
    main()
    logging.info("Finished")
