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
import sys
import re
import hashlib

from libsaas.services import github
import gnupg
import gettor.core


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
    elif(osys == 'linux'):
        m = re.search(
            'tor-browser-linux(\d\d)-\d\.\d\.\d_(\w\w)(-\w\w)?\.tar\.xz',
            file)
        if m:
            arch = m.group(1)
            lc = m.group(2)
            return 'linux', arch, lc
    elif(osys == 'osx'):
        m = re.search(
            'TorBrowser-\d\.\d\.\d-osx(\d\d)_(\w\w)(-\w\w)?\.dmg',
            file)
        if m:
            os = 'osx'
            arch = m.group(1)
            lc = m.group(2)
            return 'osx', arch, lc

if __name__ == '__main__':

    # this script should be called after fetching the latest Tor Browser,
    # and specifying the latest version
    version = sys.argv[1]

    # the token allow us to run this script without GitHub user/pass
    gh_token = 'secret-token'

    # path to the fingerprint that signed the packages
    tb_key = 'upload/torbrowser-key.asc'

    # import key fingerprint
    gpg = gnupg.GPG()
    key_data = open(tb_key).read()
    import_result = gpg.import_keys(key_data)
    fp = import_result.results[0]['fingerprint']

    # make groups of four characters to make fingerprint more readable
    # e.g. 123A 456B 789C 012D 345E 678F 901G 234H 567I 890J
    readable_fp = ' '.join(fp[i:i+4] for i in xrange(0, len(fp), 4))

    # we should have previously created a repository on GitHub where we
    # want to push the files using a SSH key (to avoid using user/pass)
    remote = 'origin'
    branch = 'master'
    user = 'ilv'
    repo = 'gettor'
    path = 'upload'
    raw_content = 'https://raw.githubusercontent.com/%s/%s/%s/%s/' %\
                  (user, repo, branch, path)

    # steps: 1) create dir for the new version, copy the latest Tor Browser
    # files there, add the files via git, make a commit for the new version
    # and push the changes (easier with system calls)
    # os.system('mkdir %s' % version)
    # os.system('cp latest/* %s' % version)
    # os.system('git add %s;git commit -m "%s"' % (version, version))
    # os.system('cd %s;git push %s %s' % (version, remote, branch))

    gh = github.GitHub(gh_token, None)
    repocontent = gh.repo(
        user,
        repo
    ).contents().get('%s/%s' % (path, version))

    core = gettor.core.Core(
        '/path/to/gettor/core.cfg'
    )

    # erase old links, if any
    core.create_links_file('GitHub', readable_fp)

    for file in repocontent:
        # e.g. https://raw.githubusercontent.com/ilv/gettor/master/upload/4.0.3/TorBrowser-4.0.3-osx32_en.dmg
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

            sha256 = get_file_sha256('%s/%s/%s' % (path, version, filename))

            # since the url is easy to construct and it doesn't involve any
            # kind of unique hash or identifier, we get the link for the
            # asc signature just by adding '.asc'
            link_asc = file[u'download_url'].replace(filename, filename_asc)

            link = "Package (%s-bit): %s\nASC signature (%s-bit): %s\n"\
                   "Package SHA256 checksum (%s-bit): %s\n" %\
                   (arch, file[u'download_url'], arch, link_asc,
                    arch, sha256)

            print "Adding %s" % file[u'download_url']
            core.add_link('GitHub', osys, lc, link)

    print "Github links updated!"
