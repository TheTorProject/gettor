# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser Bundle distribution system.
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
import dropbox
import gettor.core


def valid_bundle_format(file):
    """
        Checks for a valid bundle format
        (e.g. tor-browser-linux32-3.6.2_es-ES.tar.xz

        Returns True or False if it's valid or not.
    """

    m = re.search(
        'tor-browser-(\w+)\d\d-\d\.\d\.\d_(\w\w)-\w+\.tar\.xz',
        file)
    if m:
        return True
    else:
        return False


def get_bundle_info(file):
    """Get the operating system and locale from a bundle string.

    it raises a ValueError if the bundle doesn't have a valid format
    (although you should probably call valid_bundle_format first).
    It returns the pair of strings operating system, locale.

    """
    m = re.search(
        'tor-browser-(\w+)\d\d-\d\.\d\.\d_(\w\w)-\w+\.tar\.xz',
        file)
    if m:
        operating_system = m.group(1)
        locale = m.group(2)
        return operating_system, locale
    else:
        raise ValueError("Bundle invalid format %s" % file)

def get_file_sha256(file):
    """Get the sha256 of a file."""
    
    # as seen on the internet
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(file, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def upload_files(basedir, client):
    """Upload files from 'basedir' to Dropbox.

    It looks for files ending with 'tar.xz' inside 'basedir'. It
    raises ValueError in case the given file doesn't have a .asc file.
    It raises UploadError if something goes wrong while uploading the
    files to Dropbox. All files are uploaded to '/'.

    Returns a list with the names of the uploaded files.

    """
    files = []

    p = re.compile('.*\.tar.xz$')

    for name in os.listdir(basedir):
        path = os.path.abspath(os.path.join(basedir, name))
        if os.path.isfile(path) and p.match(path) and valid_bundle_format(name):
            files.append(name)

    for file in files:
        asc = file + '.asc'
        abs_file = os.path.abspath(os.path.join(basedir, file))
        abs_asc = os.path.abspath(os.path.join(basedir, asc))

        if not os.path.isfile(abs_asc):
            raise ValueError("%s doesn't exist!" % asc)

        # Chunk upload for big files
        to_upload = open(abs_file, 'rb')
        size = os.path.getsize(abs_file)
        uploader = client.get_chunked_uploader(to_upload, size)
        while uploader.offset < size:
            try:
                upload = uploader.upload_chunked()
            except rest.ErrorResponse, e:
                UploadError("An error ocurred while uploading %s" % abs_file)
        uploader.finish(file)

        # This should be small, upload it simple
        to_upload_asc = open(abs_asc, 'rb')
        response = client.put_file(asc, to_upload_asc)

    return files

if __name__ == '__main__':
    # to-do: use config file
    app_key = ''
    app_secret = ''
    access_token = ''
    upload_dir = 'upload/'

    # important: this must be the key that signed the packages
    tbb_key = 'tbb-key.asc'

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
        core = gettor.core.Core()
        
        # erase old links
        core.create_links_file('Dropbox', readable)

        for file in uploaded_files:            
            # build file names
            asc = file + '.asc'
            abs_file = os.path.abspath(os.path.join(upload_dir, file))
            abs_asc = os.path.abspath(os.path.join(upload_dir, asc))
            
            sha_file = get_file_sha256(abs_file)
            
            # build links
            link_file = client.share(file)
            link_asc = client.share(asc)
            link = link_file[u'url'] + ' ' + link_asc[u'url'] + ' ' + sha_file
            
            # add links
            operating_system, locale = get_bundle_info(file)
            core.add_link('Dropbox', operating_system, locale, link)
    except (ValueError, RuntimeError) as e:
        print str(e)
    except dropbox.rest.ErrorResponse as e:
        print str(e)
