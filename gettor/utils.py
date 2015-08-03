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


LOGGING_FORMAT = "[%(levelname)s] %(asctime)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d" # %H:%M:%S

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
