#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 gettor_log.py - gettor logging configuration

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

 gettor may log information, this is how we handle that logging requirement.
 A user may log to 'syslog', a 'file', 'stdout' or 'nothing'.
 The user can choose one of those four options in a configuration file.

 Note that this module will silently fall back to 'nothing' if anything is
 minconfigured. Might be harder to debug, but is safer for now.
'''

import os
import sys
from time import gmtime, strftime
import ConfigParser
import syslog
import logging
import gettor.config
from logging import handlers

__all__ = ["initalize", "getLogger", "getLogSubSystem"]

# Leave this to INFO for now
loglevel = logging.INFO
format = '%(asctime)-15s (%(process)d) %(message)s'
logger = None
logSubSystem = None
initialized = False

def initialize():
    global logger
    global logSubSystem
    global initialized
    # Don't add handlers twice
    if initialized == True:
        return
    conf = gettor.config.gettorConf() 
    logger = logging.getLogger('gettor')
    logger.setLevel(loglevel)
    logSubSystem = conf.getLogSubSystem()

    if logSubSystem == "stdout":
        handler = logging.StreamHandler()
    elif logSubSystem == "file":
        # Silently fail if things are misconfigured
        logFile = conf.getLogFile()
        try:
            if os.access(os.path.dirname(logFile), os.W_OK):
                handler = logging.FileHandler(logFile)
            else:
                logSubSystem = "nothing"
        except:
            logSubSystem = "nothing"
    elif logSubSystem == "syslog":
        handler = logging.handlers.SysLogHandler(address="/dev/log")
    else:
        # Failsafe fallback
        logSubSystem = "nothing"

    # If anything went wrong or the user doesn't want to log
    if logSubSystem == "nothing":
        handler = logging.FileHandler(os.devnull)

    formatter = logging.Formatter(fmt=format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    initialized = True

def getLogSubSystem():
    global logSubSystem
    return logSubSystem

def getLogger():
    global logger
    if logger is None:
        initialize()
    return logger

if __name__ == "__main__" :
    initialize()
    print "This is the logging module. You probably do not want to call it by hand."
    print "We'll send a test logging message now with the following subsystem: " + \
    getLogSubSystem()
    log = getLogger()
    log.info("I'm a logger, logging!")
