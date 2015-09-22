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


def get_sha256(string):
    """Get sha256 of a string.

    :param: (string) the string to be hashed.

    :return: (string) the sha256 of string.

    """
    return str(hashlib.sha256(string).hexdigest())
