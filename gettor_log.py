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
import ConfigParser
import syslog
from gettor_config import gettorConf

class gettorLogger:
    '''
    A configurable logging system for gettor.
    '''
    config  = gettorConf()
    logger  = config.getLogSubSystem()
    logfile = config.getLogFile()
    logfd   = None
    # We can't get real shm ipc with python currently :-(
    #sem     = BoundedSemaphore(1)

    def _init_(self):  
        print "gettor logger: ", logger
        # parse the configuration file so we know how we're running 
        if logger == "file":
            try:
                self.logfd = open(logfile, "w+")
            except:
                print "Could not open logfile", logfile
                self.logfd = None
            print "Logging to file"
    
    def log(self, message):
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
