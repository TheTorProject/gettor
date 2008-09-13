#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
gettor may log information, this is how we handle that logging requirement.
A user may log to syslog, a file, stdout or not at all.
The user can choose one of those four options in a configuration file.
'''

import os
import sys
#import threading
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

    # We can't get real shm ipc with python currently :-(
    #sem     = BoundedSemaphore(1)

    def _init_(self):  
        # parse the configuration file so we know how we're running 
        if logger == "file":
            try:
                self.logfd = open(logfile, "w+")
            except:
                self.logfd = None
    
    def log(self, message):
        now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        message = logPrefix + now + " : "+ message
        # Log the message
        if self.logger == "syslog":
            syslog.syslog(message)
        #elif self.logger == "file":
            #sem.aquire()
            #self.logfd.write(message)
            #sem.release()
        elif self.logger == "stdout":
            print message


if __name__ == "__main__" :
    l = gettorLogger()
    l.log("I'm a logger, logging!")
