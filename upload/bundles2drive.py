# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: poly <poly@darkdepths.net>
#           Israel Leiva <ilv@riseup.net>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2014, The Tor Project, Inc.
#               (c) 2014, Poly
#               (c) 2014, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import re
import os
import gnupg
import hashlib
import logging
import argparse
import ConfigParser
import gettor.core
from gettor.utils import get_bundle_info, get_file_sha256, valid_format

# import google drive libs
import httplib2
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient import errors
from oauth2client.client import FlowExchangeError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import Credentials


def upload_files(client, basedir):
    """Upload files to Google Drive.

    Looks for tor browser files inside basedir.

    :param: basedir (string) path of the folder with the files to be
            uploaded.
    :param: client (object) Google Drive object.

    :raise: UploadError if something goes wrong while uploading the
            files to Google Drive. All files are uploaded to '/'.

    :return: (dict) the names of the uploaded files as the keys,
             and file id as the value

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

    # dictionary to store file names and IDs
    files_dict = dict()

    for file in files:
        asc = "%s.asc" % file
        abs_file = os.path.abspath(os.path.join(basedir, file))
        abs_asc = os.path.abspath(os.path.join(basedir, asc))

        if not os.path.isfile(abs_asc):
            # there are some .mar files that don't have .asc, don't upload it
            continue

        # upload tor browser installer
        file_body = MediaFileUpload(
            abs_file,
            mimetype="application/octet-stream",
            resumable=True
        )
        body = {
            'title': file
        }
        print "Uploading '%s'..." % file
        try:
            file_data = drive_service.files().insert(
                body=body,
                media_body=file_body
                ).execute()
        except errors.HttpError, e:
            print str(e)

        # upload signature
        asc_body = MediaFileUpload(abs_asc, resumable=True)
        asc_head = {
            'title': "%s.asc" % file
        }
        print "Uploading '%s'..." % asc
        try:
            asc_data = drive_service.files().insert(
                body=asc_head,
                media_body=asc_body
                ).execute()
        except errors.HttpError, e:
            print str(e)

        # add filenames and file id to dict
        files_dict[file] = file_data['id']
        files_dict[asc] = asc_data['id']

    return files_dict


def share_file(service, file_id):
    """Make files public

    For a given file-id, sets role 'reader' to 'anyone'. Returns public
    link to file.

    :param: file_id (string)

    :return: (string) url to shared file

    """
    permission = {
        'type': "anyone",
        'role': "reader",
        'withLink': True
    }

    try:
        service.permissions().insert(
            fileId=file_id,
            body=permission
            ).execute()
    except errors.HttpError, error:
        print('An error occured while sharing: %s' % file_id)

    try:
        file = service.files().get(fileId=file_id).execute()
    except errors.HttpError, error:
        print('Error occured while fetch public link for file: %s' % file_id)

    print "Uploaded %s to %s" % (file['title'], file['webContentLink'])
    return file['webContentLink']


def get_files_links(service, v):
    """Print links of uploaded files.

    :param: service (object): Goolge Drive service object.
    :param: v (string): Version of Tor Browser to look for.

    """
    
    windows_re = 'torbrowser-install-%s_\w\w(-\w\w)?\.exe(\.asc)?' % v
    linux_re = 'tor-browser-linux\d\d-%s_(\w\w)(-\w\w)?\.tar\.xz(\.asc)?' % v
    osx_re = 'TorBrowser-%s-osx\d\d_(\w\w)(-\w\w)?\.dmg(\.asc)?' % v

    # dictionary to store file names and IDs
    files_dict = dict()
    
    print "Trying to fetch links of uploaded files..."
    links = service.files().list().execute()
    items = links.get('items', [])

    if not items:
        raise ValueError('No files found.')

    else:
        for item in items:
            if re.search(windows_re, item['title']):
                files_dict[item['title']] = item['id']
            elif re.search(linux_re, item['title']):
                files_dict[item['title']] = item['id']
            elif re.search(osx_re, item['title']):
                files_dict[item['title']] = item['id']
        return files_dict

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Utility to upload Tor Browser to Google Drive.'
    )
    
    # if no LC specified, download all
    parser.add_argument(
        '-l', '--links', default=None,
        help='Create links file with files already uploaded and '\
             'matching the specified version. '
    )

    args = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read('drive.cfg')

    client_id = config.get('app', 'client-id')
    app_secret = config.get('app', 'secret')
    refresh_token = config.get('app', 'refresh_token')
    upload_dir = config.get('general', 'upload_dir')

    # important: this key must be the one that signed the packages
    tbb_key = config.get('general', 'tbb_key')

    # requests full access to drive account
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
    REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

    print "Authenticating..."

    flow = OAuth2WebServerFlow(
        client_id,
        app_secret,
        OAUTH_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    # If no valid token found, need to prompt user.
    # this should only occur once
    if not refresh_token:
        flow.params['access_type'] = 'offline'
        flow.params['approval_prompt'] = 'force'
        authorize_url = flow.step1_get_authorize_url()
        print 'Go to the following link in your browser: ' + authorize_url
        code = raw_input('Enter verification code: ').strip()
        try:
            credentials = flow.step2_exchange(code)
        except FlowExchangeError as e:
            print str(e)

        # oauth2 credentials instance must be stored as json string
        config.set('app', 'refresh_token', credentials.to_json())
        with open('drive.cfg', 'wb') as configfile:
            config.write(configfile)
    else:
        # we already have a valid token
        credentials = Credentials.new_from_json(refresh_token)

    # authenticate with oauth2
    http = httplib2.Http()
    http = credentials.authorize(http)

    # initialize drive instance
    drive_service = build('drive', 'v2', http=http)

    # import key fingerprint
    gpg = gnupg.GPG()
    key_data = open(tbb_key).read()
    import_result = gpg.import_keys(key_data)
    fp = import_result.results[0]['fingerprint']

    # make groups of four characters to make fingerprint more readable
    # e.g. 123A 456B 789C 012D 345E 678F 901G 234H 567I 890J
    readable = ' '.join(fp[i:i+4] for i in xrange(0, len(fp), 4))

    try:
        # helpful when something fails but files are uploaded.
        if args.links:
            uploaded_files = get_files_links(drive_service, args.links)

            if not uploaded_files:
                raise ValueError("There are no files for that version")
        else:
            uploaded_files = upload_files(drive_service, upload_dir)
        # use default config
        core = gettor.core.Core('/home/gettor/core.cfg')

        # erase old links
        core.create_links_file('Drive', readable)

        # recognize file OS by its extension
        p1 = re.compile('.*\.tar.xz$')
        p2 = re.compile('.*\.exe$')
        p3 = re.compile('.*\.dmg$')
        p4 = re.compile('.*\.asc$')

        for file in uploaded_files.keys():
            # only run for tor browser installers
            if p4.match(file):
                continue
            asc = "%s.asc" % file
            abs_file = os.path.abspath(os.path.join(upload_dir, file))
            abs_asc = os.path.abspath(os.path.join(upload_dir, asc))

            sha_file = get_file_sha256(abs_file)

            # build links
            link_file = share_file(
                drive_service,
                uploaded_files[file]
            )

            link_asc = share_file(
                drive_service,
                uploaded_files["%s.asc" % file]
            )

            if p1.match(file):
                osys, arch, lc = get_bundle_info(file, 'linux')
            elif p2.match(file):
                osys, arch, lc = get_bundle_info(file, 'windows')
            elif p3.match(file):
                osys, arch, lc = get_bundle_info(file, 'osx')

            link = "%s$%s$%s$" % (link_file, link_asc, sha_file)

            # note that you should only upload bundles for supported locales
            core.add_link('Drive', osys, lc, link)
    except (ValueError, RuntimeError) as e:
        print str(e)
