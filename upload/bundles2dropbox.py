# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: Israel Leiva <ilv@riseup.net>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2014, The Tor Project, Inc.
#               (c) 2014, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import re
import os
import gnupg
import hashlib
import ConfigParser

import dropbox
import gettor.core
from gettor.utils import get_bundle_info, get_file_sha256, valid_format


def upload_files(basedir, client):
    """Upload files to Dropbox.

    Looks for files ending with 'tar.xz' inside basedir.

    :param: basedir (string) path of the folder with the files to be
            uploaded.
    :param: client (object) DropboxClient object.

    :raise: ValueError if the .xz file doesn't have an .asc file.
    :raise: UploadError if something goes wrong while uploading the
            files to Dropbox. All files are uploaded to '/'.

    :return: (list) the names of the uploaded files.

    """
    files = []

    for name in os.listdir(basedir):
        path = os.path.abspath(os.path.join(basedir, name))
        if os.path.isfile(path) and valid_format(name, 'linux'):
            files.append(name)

    for name in os.listdir(basedir):
        path = os.path.abspath(os.path.join(basedir, name))
        if os.path.isfile(path) and valid_format(name, 'windows'):
            files.append(name)

    for name in os.listdir(basedir):
        path = os.path.abspath(os.path.join(basedir, name))
        if os.path.isfile(path) and valid_format(name, 'osx'):
            files.append(name)

    for file in files:
        asc = "%s.asc" % file
        abs_file = os.path.abspath(os.path.join(basedir, file))
        abs_asc = os.path.abspath(os.path.join(basedir, asc))

        if not os.path.isfile(abs_asc):
            # there are some .mar files that don't have .asc, don't upload it
            continue

        # chunk upload for big files
        to_upload = open(abs_file, 'rb')
        size = os.path.getsize(abs_file)
        uploader = client.get_chunked_uploader(to_upload, size)
        while uploader.offset < size:
            try:
                upload = uploader.upload_chunked()
            except dropbox.rest.ErrorResponse, e:
                print("An error ocurred while uploading %s: %s" % abs_file, e)
        uploader.finish(file)
        print "Uploading %s" % file

        # this should be small, upload it simple
        to_upload_asc = open(abs_asc, 'rb')
        response = client.put_file(asc, to_upload_asc)
        print "Uploading %s" % asc

    return files

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('dropbox.cfg')

    app_key = config.get('app', 'key')
    app_secret = config.get('app', 'secret')
    access_token = config.get('app', 'access_token')
    upload_dir = config.get('general', 'upload_dir')

    # important: this key must be the one that signed the packages
    tbb_key = config.get('general', 'tbb_key')

    client = dropbox.client.DropboxClient(access_token)

    # import key fingerprint
    gpg = gnupg.GPG()
    key_data = open(tbb_key).read()
    import_result = gpg.import_keys(key_data)
    fp = import_result.results[0]['fingerprint']

    # make groups of four characters to make fingerprint more readable
    # e.g. 123A 456B 789C 012D 345E 678F 901G 234H 567I 890J
    readable = ' '.join(fp[i:i+4] for i in xrange(0, len(fp), 4))

    try:
        uploaded_files = upload_files(upload_dir, client)
        # use default config
        core = gettor.core.Core('/home/gettor/core.cfg')

        # erase old links
        core.create_links_file('Dropbox', readable)

        # recognize file OS by its extension
        p1 = re.compile('.*\.tar.xz$')
        p2 = re.compile('.*\.exe$')
        p3 = re.compile('.*\.dmg$')

        for file in uploaded_files:
            # build file names
            asc = "%s.asc" % file
            abs_file = os.path.abspath(os.path.join(upload_dir, file))
            abs_asc = os.path.abspath(os.path.join(upload_dir, asc))

            sha_file = get_file_sha256(abs_file)

            # build links
            link_file = client.share(file, short_url=False)
            # if someone finds how to do this with the API, please tell me!
            link_file[u'url'] = link_file[u'url'].replace('?dl=0', '?dl=1')
            link_asc = client.share(asc, short_url=False)
            link_asc[u'url'] = link_asc[u'url'].replace('?dl=0', '?dl=1')
            if p1.match(file):
                osys, arch, lc = get_bundle_info(file, 'linux')
            elif p2.match(file):
                osys, arch, lc = get_bundle_info(file, 'windows')
            elif p3.match(file):
                osys, arch, lc = get_bundle_info(file, 'osx')

            link = "%s$%s$%s$" % (link_file[u'url'], link_asc[u'url'], sha_file)

            # note that you should only upload bundles for supported locales
            core.add_link('Dropbox', osys, lc, link)
    except (ValueError, RuntimeError) as e:
        print str(e)
    except dropbox.rest.ErrorResponse as e:
        print str(e)
