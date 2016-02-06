# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: Israel Leiva <ilv@torproject.org>
#           see also AUTHORS file
#
# :copyright:   (c) 2015, The Tor Project, Inc.
#               (c) 2015, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.
#

import os
import re
import sys
import argparse
import ConfigParser

import github3
import gnupg
import gettor.core
from gettor.utils import (get_bundle_info, get_file_sha256,
                          find_files_to_upload)

import urllib3

# Actually verify Github's cert!
urllib3.disable_warnings()


def upload_new_release(github_repo, version, upload_dir):
    """
    Returns a Release object
    """

    # Create a new release of this TBB
    release = target_repo.create_release(
        'v{}'.format(version),
        target_commitish="master",
        name='Tor Browser Bundle {}'.format(version),
        body='',
        draft=True,
    )

    for filename in find_files_to_upload(upload_dir):
        # Upload each file for this release
        file_path = os.path.join(upload_dir, filename)
        print("Uploading file {}".format(filename))
        release.upload_asset('application/zip',
                             filename, open(file_path, 'rb'))

    return release


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Utility to upload Tor Browser to Github.'
    )

    # with this we only get the links of files already uploaded
    # useful when somethings fail after uploading
    parser.add_argument(
        '-l', '--links', default=None,
        help='Create links file with files already uploaded.'
    )

    parser.add_argument(
        '-v', '--version', default=None,
        help='Version of Tor Browser.'
    )

    args = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read('github-local.cfg')

    # this script should be called after fetching the latest Tor Browser,
    # and specifying the latest version
    if args.version:
        version = args.version
    else:
        tbb_version_config = ConfigParser.ConfigParser()
        tbb_version_config.read('latest_torbrowser.cfg')
        version = tbb_version_config.get('version', 'current')

    # the token allow us to run this script without GitHub user/pass
    github_access_token = config.get('app', 'access_token')

    # path to the fingerprint that signed the packages
    tb_key = os.path.abspath('tbb-key-torbrowserteam.asc')

    # path to the latest version of Tor Browser
    tb_path = os.path.abspath('latest')

    # user and repository where we upload Tor Browser
    github_user = config.get('app', 'user')
    github_repo = config.get('app', 'repo')

    gh = github3.login(token=github_access_token)
    target_repo = gh.repository(github_user, github_repo)

    # import key fingerprint
    gpg = gnupg.GPG()
    key_data = open(tb_key).read()
    import_result = gpg.import_keys(key_data)
    fp = import_result.results[0]['fingerprint']

    # make groups of four characters to make fingerprint more readable
    # e.g. 123A 456B 789C 012D 345E 678F 901G 234H 567I 890J
    readable_fp = ' '.join(fp[i:i+4] for i in xrange(0, len(fp), 4))

    # Find any published releases with this version number
    for release in target_repo.iter_releases():
        if release.tag_name == 'v{}'.format(version) and not release.draft:
            print("Found an existing published release with this version. "
                  "Not uploading again unless you delete the published "
                  "release '{}'.".format(release.tag_name))
            break
    else:
        release = None

    if args.links or release:
        # Only generating link file, should use previously published release
        if not release:
            print("Error occured! Could not find a published release for "
                  "version {}".format(version))
            sys.exit(1)

    else:
        # Remove any drafts to clean broken uploads
        print('Uploading release, please wait, this might take a while!')
        # Upload the latest browser bundles to a new release
        release = upload_new_release(target_repo, version, tb_path)

        # Upload success, publish the release
        release.edit(draft=False)

    # Create the links file for this release
    core = gettor.core.Core(os.path.abspath('../core.cfg'))

    # Erase old links if any and create a new empty one
    core.create_links_file('GitHub', readable_fp)

    print("Creating links file")
    for asset in release.assets:
        url = ("https://github.com/{user}/{repo}/releases/download/"
               "v{tag}/{file}".format(
                user=github_user,
                repo=github_repo,
                tag=version,
                file=asset.name,
                ))
        osys, arch, lc = get_bundle_info(asset.name)
        sha256 = get_file_sha256(
            os.path.abspath(os.path.join(tb_path, asset.name))
        )

        link = "{}${}${}$".format(url, url + ".asc", sha256)

        print("Adding {}".format(url))
        core.add_link('GitHub', osys, lc, link)

    print "Github links updated!"
