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
import gettor_config
from logging import handlers

# Leave this to INFO for now
loglevel = logging.INFO

class gettorLogger:
    '''
    A configurable logging system for gettor.
    '''

    format = '%(asctime)-15s (%(process)d) %(message)s'

    def __init__(self):  
        self.config = gettor_config.gettorConf() 
        self.logger = logging.getLogger('gettor')
        self.logger.setLevel(loglevel)
        self.logSubSystem = self.config.getLogSubSystem()

        if self.logSubSystem == "stdout":
            handler = logging.StreamHandler()
        elif self.logSubSystem == "file":
            # Silently fail if things are misconfigured
            self.logFile = self.config.getLogFile()
            try:
                if os.access(os.path.dirname(self.logFile), os.W_OK):
                    handler = logging.FileHandler(self.logFile)
                else:
                    self.logSubSystem = "nothing"
            except:
                self.logSubSystem = "nothing"
        elif self.logSubSystem == "syslog":
            handler = logging.handlers.SysLogHandler(address="/dev/log")
        else:
            # Failsafe fallback
            self.logSubSystem = "nothing"

        # If anything went wrong or the user doesn't want to log
        if self.logSubSystem == "nothing":
            handler = logging.FileHandler("/dev/null")

        formatter = logging.Formatter(fmt=self.format)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def getLogSubSystem(self):
        return self.logSubSystem

    def getLogger(self):
        return self.logger

if __name__ == "__main__" :
    l = gettorLogger()
    print "This is the logging module. You probably do not want to call it by hand."
    print "We'll send a test logging message now with the following subsystem: " + \
    l.getLogSubSystem()
    log = l.getLogger()
    log.info("I'm a logger, logging!")
