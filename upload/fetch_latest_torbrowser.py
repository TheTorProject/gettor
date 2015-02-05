# -*- coding: utf-8 -*-
#
# Fetch the latest version of Tor Browser and upload it to the supported
# providers (e.g. Dropbox). Ideally, this script should be executed with
# a cron in order to automate of updating the files served by GetTor when
# a new version of Tor Browser is released.
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: Israel Leiva <ilv@torproject.org>
#
# :copyright:   (c) 2015, The Tor Project, Inc.
#               (c) 2015, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import os

import urllib2
import json
import ConfigParser
import shutil

# this path should be relative to this script (or absolute)
UPLOAD_SCRIPTS = {
    'dropbox': 'bundles2dropbox.py',
    'drive': 'bundles2drive.py'
}

# server from which to download Tor Browser
dist_tpo = 'https://dist.torproject.org/torbrowser/'

# find out the latest version
url = 'https://www.torproject.org/projects/torbrowser/RecommendedTBBVersions'
response = urllib2.urlopen(url)
json_response = json.load(response)
latest_version = json_response[0]

# find out the current version delivered by GetTor
config = ConfigParser.RawConfigParser()
config.read('latest_torbrowser.cfg')
current_version = config.get('version', 'current')

if current_version != latest_version:

    # in wget we trust
    mirror = '%s%s' % (dist_tpo, latest_version)
    # download files for windows, osx, linux, signatures and checksums
    params = '-nH --cut-dirs=1 -L 1 --accept exe,dmg,tar.xz,asc,txt'
    cmd = 'wget %s --mirror %s' % (params, mirror)
    # make the mirror
    # a folder with the value of 'latest_version' will be created
    os.system(cmd)
    # everything inside upload will be uploaded by the provivers' scripts
    shutil.move('latest', 'latest_backup')
    shutil.move(latest_version, 'latest')
    shutil.rmtree('latest_backup')

    # latest version of Tor Browser has been syncronized
    # let's upload it
    for provider in UPLOAD_SCRIPTS:
        os.sytem('python2.7 %s' % UPLOAD_SCRIPTS[provider])

    # if everything is OK, update the current version delivered by GetTor
    config.set('version', 'current', latest_version)
    with open(r'latest_torbrowser.cfg', 'wb') as config_file:
        config.write(config_file)
