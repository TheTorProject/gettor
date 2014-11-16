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

def valid_format(file, osys):
    """Check for valid bundle format

    Check if the given file has a valid bundle format
    (e.g. tor-browser-linux32-3.6.2_es-ES.tar.xz)

    :param: file (string) the name of the file.
    :param: osys (string) the OS.

    :return: (boolean) true if the bundle format is valid, false otherwise.

    """
    if(osys == 'windows'):
        m = re.search(
            'torbrowser-install-\d\.\d\.\d_\w\w(-\w\w)?\.exe',
            file)
    elif(osys == 'linux'):
        m = re.search(
            'tor-browser-linux\d\d-\d\.\d\.\d_(\w\w)(-\w\w)?\.tar\.xz',
            file)
    elif(osys == 'osx'):
        m = re.search(
            'TorBrowser-\d\.\d\.\d-osx\d\d_(\w\w)(-\w\w)?\.dmg',     
            file)
    if m:
        return True
    else:
        return False


def get_bundle_info(file, osys):
    """Get the os, arch and lc from a bundle string.

    :param: file (string) the name of the file.
    :param: osys (string) the OS.

    :raise: ValueError if the bundle doesn't have a valid bundle format.

    :return: (list) the os, arch and lc.

    """
    if(osys == 'windows'):
        m = re.search(
            'torbrowser-install-\d\.\d\.\d_(\w\w)(-\w\w)?\.exe',
            file)
        if m:
            lc = m.group(1)
            return 'windows', '32/64', lc
        else:
            raise ValueError("Invalid bundle format %s" % file)
    elif(osys == 'linux'):
        m = re.search(
            'tor-browser-linux(\d\d)-\d\.\d\.\d_(\w\w)(-\w\w)?\.tar\.xz',
            file)
        if m:
            arch = m.group(1)
            lc = m.group(2)
            return 'linux', arch, lc
        else:
            raise ValueError("Invalid bundle format %s" % file)
    elif(osys == 'osx'):
        m = re.search(
            'TorBrowser-\d\.\d\.\d-osx(\d\d)_(\w\w)(-\w\w)?\.dmg',
            file)
        if m:
            os = 'osx'
            arch = m.group(1)
            lc = m.group(2)
            return 'osx', arch, lc
        else:
            raise ValueError("Invalid bundle format %s" % file)


def get_file_sha256(file):
    """Get the sha256 of a file.

    :param: file (string) the path of the file.

    :return: (string) the sha256 hash.

    """
    # as seen on the internetz
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(file, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()


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

    p = re.compile('.*\.tar.xz$')
    for name in os.listdir(basedir):
        path = os.path.abspath(os.path.join(basedir, name))
        if os.path.isfile(path) and p.match(path)\
        and valid_format(name, 'linux'):
            files.append(name)

    p = re.compile('.*\.exe$')
    for name in os.listdir(basedir):
        path = os.path.abspath(os.path.join(basedir, name))
        if os.path.isfile(path) and p.match(path)\
        and valid_format(name, 'windows'):
            files.append(name)

    p = re.compile('.*\.dmg$')
    for name in os.listdir(basedir):
        path = os.path.abspath(os.path.join(basedir, name))
        if os.path.isfile(path) and p.match(path)\
        and valid_format(name, 'osx'):
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

            link = "Package (%s-bit): %s\nASC signature (%s-bit): %s\n"\
                   "Package SHA256 checksum (%s-bit): %s\n" %\
                   (arch, link_file[u'url'], arch, link_asc[u'url'],
                    arch, sha_file)

            # note that you should only upload bundles for supported locales
            core.add_link('Dropbox', osys, lc, link)
    except (ValueError, RuntimeError) as e:
        print str(e)
    except dropbox.rest.ErrorResponse as e:
        print str(e)
