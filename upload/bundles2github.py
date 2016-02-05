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
import sh
import sys
import time
import shutil
import hashlib
import argparse

from libsaas.services import github
import gnupg
import gettor.core
from gettor.utils import get_bundle_info, get_file_sha256


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

    # this script should be called after fetching the latest Tor Browser,
    # and specifying the latest version
    version = args.version

    # the token allow us to run this script without GitHub user/pass
    gh_token = ''

    # path to the fingerprint that signed the packages
    tb_key = os.path.abspath('tbb-key-torbrowserteam.asc')

    # path to the latest version of Tor Browser
    tb_path = os.path.abspath('upload/latest')

    # path to the repository where we upload Tor Browser
    repo_path = os.path.abspath('gettorbrowser')

    # wait time between pushing the files to GH and asking for its links
    wait_time = 10

    # import key fingerprint
    gpg = gnupg.GPG()
    key_data = open(tb_key).read()
    import_result = gpg.import_keys(key_data)
    fp = import_result.results[0]['fingerprint']

    # make groups of four characters to make fingerprint more readable
    # e.g. 123A 456B 789C 012D 345E 678F 901G 234H 567I 890J
    readable_fp = ' '.join(fp[i:i+4] for i in xrange(0, len(fp), 4))

    # we should have previously created a repository on GitHub where we
    # want to push the files using an SSH key (to avoid using user/pass)
    remote = 'origin'
    branch = 'master'
    user = 'TheTorProject'
    repo = 'gettorbrowser'
    raw_content = 'https://raw.githubusercontent.com/%s/%s/%s/' %\
                  (user, repo, branch)

    # steps:
    # 1) copy folder with latest version of Tor Browser
    # 2) add files via sh.git
    # 3) make a commit for the new version
    # 4) push the changes

    if not args.links:
        shutil.copytree(
            tb_path,
            os.path.abspath('%s/%s' % (repo_path, version))
        )

        git = sh.git.bake(_cwd=repo_path)
        git.add('%s' % version)
        git.commit(m=version)
        git.push()

        # it takes a while to process the recently pushed files
        print "Wait a few seconds before asking for the links to Github..."
        time.sleep(wait_time)

    print "Trying to get the links"
    gh = github.GitHub(gh_token, None)
    repocontent = gh.repo(
        user,
        repo
    ).contents().get('%s' % version)

    core = gettor.core.Core(
        os.path.abspath('core.cfg')
    )

    # erase old links, if any
    core.create_links_file('GitHub', readable_fp)

    for file in repocontent:
        # e.g. https://raw.githubusercontent.com/gettorbrowser/dl/master/4.0.7/TorBrowser-4.0.4-osx32_en-US.dmg
        m = re.search('%s.*\/(.*)' % raw_content, file[u'download_url'])
        if m:
            filename = m.group(1)
            # get bundle info according to its OS
            if re.match('.*\.exe$', filename):
                osys, arch, lc = get_bundle_info(filename, 'windows')
                filename_asc = filename.replace('exe', 'exe.asc')

            elif re.match('.*\.dmg$', filename):
                osys, arch, lc = get_bundle_info(filename, 'osx')
                filename_asc = filename.replace('dmg', 'dmg.asc')

            elif re.match('.*\.tar.xz$', filename):
                osys, arch, lc = get_bundle_info(filename, 'linux')
                filename_asc = filename.replace('tar.xz', 'tar.xz.asc')

            else:
                # don't care about other files (asc or txt)
                continue

            sha256 = get_file_sha256(
                os.path.abspath(
                    '%s/%s/%s' % (repo, version, filename)
                )
            )

            # since the url is easy to construct and it doesn't involve any
            # kind of unique hash or identifier, we get the link for the
            # asc signature just by adding '.asc'
            link_asc = file[u'download_url'].replace(filename, filename_asc)

            link = "%s$%s$%s$" % (file[u'download_url'], link_asc, sha256)

            print "Adding %s" % file[u'download_url']
            core.add_link('GitHub', osys, lc, link)

    print "Github links updated!"
