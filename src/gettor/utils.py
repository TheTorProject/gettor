# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser Bundle distribution system.
#

import os
import logging

"""Common utilities for GetTor modules."""

class SingleLevelFilter(logging.Filter):
    """Filter logging levels to create separated logs.

    Public methods: 

        filter(): fitler logging levels.

    """

    def __init__(self, passlevel, reject):
        """Create a new object with level to be filtered.

        If reject value is false, all but the passlevel will be filtered. 
        Useful for logging in separated files.
        
        Params: passlevel - name of a logging level.

        """

        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        """Do the actual filtering."""
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)
            
def filter_logging(logger, dir, level):
    """Create separated files for each level of logging.
    
    Params: logger - a logging object.
            dir - directory to put the log files.
            level - the level of logging for the all.log file.
            
    Returns: logger object.

    """
    # Keep a good format
    string_format = '[%(levelname)7s] %(asctime)s - %(message)s'
    formatter = logging.Formatter(string_format, '%Y-%m-%d %H:%M:%S')

    # Keep logs separated (and filtered)
    # all.log depends on level specified as param
    all_log = logging.FileHandler(os.path.join(dir, 'all.log'), mode='a+')
    all_log.setLevel(logging.getLevelName(level))
    all_log.setFormatter(formatter)

    debug_log = logging.FileHandler(os.path.join(dir, 'debug.log'), mode='a+')
    debug_log.setLevel('DEBUG')
    debug_log.addFilter(SingleLevelFilter(logging.DEBUG, False))
    debug_log.setFormatter(formatter)

    info_log = logging.FileHandler(os.path.join(dir, 'info.log'), mode='a+')
    info_log.setLevel('INFO')
    info_log.addFilter(SingleLevelFilter(logging.INFO, False))
    info_log.setFormatter(formatter)

    warn_log = logging.FileHandler(os.path.join(dir, 'warn.log'), mode='a+')
    warn_log.setLevel('WARNING')
    warn_log.addFilter(SingleLevelFilter(logging.WARNING, False))
    warn_log.setFormatter(formatter)

    error_log = logging.FileHandler(os.path.join(dir, 'error.log'), mode='a+')
    error_log.setLevel('ERROR')
    error_log.addFilter(SingleLevelFilter(logging.ERROR, False))
    error_log.setFormatter(formatter)

    logger.addHandler(all_log)
    logger.addHandler(info_log)
    logger.addHandler(debug_log)
    logger.addHandler(warn_log)
    logger.addHandler(error_log)
    
    return logger

