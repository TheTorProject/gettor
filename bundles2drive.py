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
import ConfigParser
import gettor.core

#import google drive libs
import httplib2
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import Credentials


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
        file_body = MediaFileUpload(abs_file, resumable=True)
        body = {
          'title': file
        }
        print "Uploading '%s'..." % file
        try:
            file_data = drive_service.files().insert(body=body, media_body=file_body).execute()
        except:
            raise UploadError

        # upload signature
        asc_body = MediaFileUpload(abs_asc, resumable=True)
        asc_head = {
           'title': "%s.asc" % file
        }
        print "Uploading '%s'..." % asc
        try:
            asc_data = drive_service.files().insert(body=asc_head, media_body=asc_body).execute()
        except:
            raise UploadError

        # add filenames and file id to dict
        files_dict[file] = file_data['id']
        files_dict[asc]  = asc_data['id']

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
               fileId=file_id, body=permission).execute()
    except errors.HttpError, error:
           print('An error occured while sharing: %s' % file_id)

    try:
        file = service.files().get(fileId=file_id).execute()
    except errors.HttpError, error:
           print('Error occured while fetch public link for file: %s' % file_id)

    print("Uploaded to %s" % file['webContentLink'])
    return file['webContentLink']


if __name__ == '__main__':
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

    flow = OAuth2WebServerFlow(client_id, app_secret, OAUTH_SCOPE,
                           redirect_uri=REDIRECT_URI)

    # If no valid token found, need to prompt user.
    # this should only occur once
    if not refresh_token:
       flow.params['access_type'] = 'offline'
       flow.params['approval_prompt'] = 'force'
       authorize_url = flow.step1_get_authorize_url()
       print 'Go to the following link in your browser: ' + authorize_url
       code = raw_input('Enter verification code: ').strip()
       credentials = flow.step2_exchange(code)

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
            link_file = share_file(drive_service,
                                   uploaded_files[file])
            link_asc  = share_file(drive_service,
                                   uploaded_files["%s.asc" % file])

            if p1.match(file):
                osys, arch, lc = get_bundle_info(file, 'linux')
            elif p2.match(file):
                osys, arch, lc = get_bundle_info(file, 'windows')
            elif p3.match(file):
                osys, arch, lc = get_bundle_info(file, 'osx')

            link = "Package (%s-bit): %s\nASC signature (%s-bit): %s\n"\
                   "Package SHA256 checksum (%s-bit): %s\n" %\
                   (arch, link_file, arch, link_asc,
                    arch, sha_file)

            # note that you should only upload bundles for supported locales
            core.add_link('Drive', osys, lc, link)
    except (ValueError, RuntimeError) as e:
        print str(e)
