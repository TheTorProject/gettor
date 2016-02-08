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

import os
import hashlib

"""Common utilities for GetTor modules."""


LOGGING_FORMAT = "[%(levelname)s] %(asctime)s; %(message)s"
DATE_FORMAT = "%Y-%m-%d"  # %H:%M:%S


def get_logging_format():
    """Get the logging format.

    :return: (string) the logging format.

    """
    return LOGGING_FORMAT


def get_date_format():
    """Get the date format for logging.

    :return: (string) the date format for logging.

    """
    return DATE_FORMAT


def get_sha256(string):
    """Get sha256 of a string.

    :param: (string) the string to be hashed.

    :return: (string) the sha256 of string.

    """
    return str(hashlib.sha256(string).hexdigest())


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
