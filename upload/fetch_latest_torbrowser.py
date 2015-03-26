# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: Israel Leiva <ilv@torproject.org>
#
# :copyright:   (c) 2015, The Tor Project, Inc.
#               (c) 2015, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.
#

import os

import urllib2
import json
import argparse
import ConfigParser
import shutil

# this path should be relative to this script (or absolute)
UPLOAD_SCRIPTS = {
    'dropbox': 'bundles2dropbox.py',
    'drive': 'bundles2drive.py'
}

# "regex" for filtering downloads in wget
OS_RE = {
    'windows': '%s.exe,%s.exe.asc',
    'linux': '%s.tar.xz,%s.tar.xz.asc',
    'osx': '%s.dmg,%s.dmg.asc',
}


def main():
    """Script to fetch the latest Tor Browser.

    Fetch the latest version of Tor Browser and upload it to the supported
    providers (e.g. Dropbox). Ideally, this script should be executed with
    a cron in order to automate the updating of the files served by GetTor
    when a new version of Tor Browser is released.

    Usage: python2.7 fetch.py --os=<OS> --lc=<LC>

    Some fetch examples:

    Fetch Tor Browser for all platforms and languages:
        $ python2.7 fetch.py

    Fetch Tor Browser only for Linux:
        $ python2.7 fetch.py --os=linux

    Fetch Tor Browser only for Windows and in US English:
        $ python2.7 fetch.py --os=windows --lc=en-US

    Fetch Tor Browser for all platforms, but only in Spanish:
        $ python2.7 fetch.py --lc=es-ES

    """
    parser = argparse.ArgumentParser(
        description='Utility to fetch the latest Tor Browser and upload it \
                    to popular cloud services.'
    )

    # if no OS specified, download all
    parser.add_argument('-o', '--os', default=None,
                        help='filter by OS')

    # if no LC specified, download all
    parser.add_argument('-l', '--lc', default='',
                        help='filter by locale')

    args = parser.parse_args()

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
        mirror = '%s%s/' % (dist_tpo, latest_version)

        # what LC should we download?
        lc_re = args.lc

        # what OS should we download?
        if args.os == 'windows':
            os_re = OS_RE['windows'] % (lc_re, lc_re)

        elif args.os == 'osx':
            os_re = OS_RE['osx'] % (lc_re, lc_re)

        elif args.os == 'linux':
            os_re = OS_RE['linux'] % (lc_re, lc_re)

        else:
            os_re = '%s.exe,%s.exe.asc,%s.dmg,%s.dmg.asc,%s.tar.xz,%s.tar'\
                    '.xz.asc' % (lc_re, lc_re, lc_re, lc_re, lc_re, lc_re)

        params = "-nH --cut-dirs=1 -L 1 --accept %s" % os_re

        # in wget we trust
        cmd = 'wget %s --mirror %s' % (params, mirror)

        print "Going to execute %s" % cmd
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
            os.system('python2.7 %s' % UPLOAD_SCRIPTS[provider])

        # if everything is OK, update the current version delivered by GetTor
        config.set('version', 'current', latest_version)
        with open(r'latest_torbrowser.cfg', 'wb') as config_file:
            config.write(config_file)

if __name__ == "__main__":
    main()
