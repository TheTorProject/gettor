#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
gettor may log information, this is how we handle that logging requirement.
A user may log to syslog, a file, stdout or not at all.
The user can choose one of those four options in a configuration file.
'''

import os
import sys
from time import gmtime, strftime
import ConfigParser
import syslog
from gettor_config import gettorConf

class gettorLogger:
    '''
    A configurable logging system for gettor.
    '''
    config    = gettorConf()
    logger    = config.getLogSubSystem()
    logfile   = config.getLogFile()
    logfd     = None
    pid       = str(os.getpid())
    logPrefix = "gettor (pid " + pid + ") "

    def _init_(self):  
        # parse the configuration file so we know how we're running 
        if logger == "file":
            try:
                self.logfd = open(logfile, "a+")
            except:
                self.logfd = None

    def _del_(self):
        if logger == "file" and self.logfd == None:
            self.logfd.close()
    
    def log(self, message):
        # Syslog does not need a timestamp
        if self.logger == "syslog":
            now = ""
        else:
            now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

        message = self.logPrefix + now + " : "+ message

        # By default, we'll just drop the message
        if self.logger == "nothing":
            return True

        # Other options for logging the message follow
        elif self.logger == "syslog":
            syslog.syslog(message)
            
        elif self.logger == "file":
            self.logfd.write(message)

        elif self.logger == "stdout":
            print message

if __name__ == "__main__" :
    l = gettorLogger()
    print "This is the logging module. You probably do not want to call it by hand."
    print "We'll send a test logging message now with the following subsystem: " + \
    str(l.logger)
    l.log("I'm a logger, logging!")
