#!/usr/bin/env python
import re
import os
import dropbox
import gettor


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
    """
        Get the operating system and locale from a bundle string.

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


def upload_files(basedir, client):
    """
        Upload files from 'basedir' to Dropbox.

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
        if os.path.isfile(path)
        and p.match(path)
        and valid_bundle_format(name):
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

# Test app for now
app_key = ''
app_secret = ''
access_token = ''
# Should we use a dropbox.cfg?
upload_dir = 'upload/'

client = dropbox.client.DropboxClient(access_token)

try:
    uploaded_files = upload_files(upload_dir, client)
    # Fingerprint generation pending...
    fingerprint = '111-222-333-444'
    core = gettor.Core('gettor.cfg')
    # Erase the old links file
    core.create_links_file('Dropbox')

    for file in uploaded_files:
        asc = file + '.asc'
        link_file = client.share(file)
        link_asc = client.share(asc)
        link = link_file[u'url'] + ' ' + link_asc[u'url'] + ' ' + fingerprint
        operating_system, locale = get_bundle_info(file)
        core.add_link('Dropbox', operating_system, locale, link)
except (ValueError, RuntimeError) as e:
    print str(e)
except dropbox.rest.ErrorResponse as e:
    print str(e)
