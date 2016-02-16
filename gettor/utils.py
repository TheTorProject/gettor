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
import re
import hashlib

"""Common utilities for GetTor modules."""


LOGGING_FORMAT = "[%(levelname)s] %(asctime)s; %(message)s"
DATE_FORMAT = "%Y-%m-%d"  # %H:%M:%S

windows_regex = '^torbrowser-install-\d\.\d(\.\d)?_(\w\w)(-\w\w)?\.exe$'
linux_regex = '^tor-browser-linux(\d\d)-\d\.\d(\.\d)?_(\w\w)(-\w\w)?\.tar\.xz$'
osx_regex = '^TorBrowser-\d\.\d(\.\d)?-osx\d\d_(\w\w)(-\w\w)?\.dmg$'


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


def get_bundle_info(filename, osys=None):
    """Get the os, arch and lc from a bundle string.

    :param: file (string) the name of the file.
    :param: osys (string) the OS.

    :raise: ValueError if the bundle doesn't have a valid bundle format.

    :return: (list) the os, arch and lc.

    """
    m_windows = re.search(windows_regex, filename)
    m_linux = re.search(linux_regex, filename)
    m_osx = re.search(osx_regex, filename)

    if m_windows:
        return 'windows', '32/64', m_windows.group(2)
    elif m_linux:
        return 'linux', m_linux.group(1), m_linux.group(3)
    elif m_osx:
        return 'osx', '64', m_osx.group(2)
    else:
        raise ValueError("Invalid bundle format %s" % file)


def valid_format(filename, osys=None):
    """Check for valid bundle format

    Check if the given file has a valid bundle format
    (e.g. tor-browser-linux32-3.6.2_es-ES.tar.xz)

    :param: file (string) the name of the file.

    :return: (boolean) true if the bundle format is valid, false otherwise.

    """
    m_windows = re.search(windows_regex, filename)
    m_linux = re.search(linux_regex, filename)
    m_osx = re.search(osx_regex, filename)
    if any((m_windows, m_linux, m_osx)):
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


def find_files_to_upload(upload_dir):
    """
    Find the files which are named correctly and have a .asc file
    """
    files = []
    for name in os.listdir(upload_dir):
        asc_file = os.path.join(upload_dir, "{}.asc".format(name))
        if valid_format(name) and os.path.isfile(asc_file):
            files.extend([name, "{}.asc".format(name)])

    return files
