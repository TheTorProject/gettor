#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
gettor may log information, this is how we handle that logging requirement.
A user may log to syslog, a file, stdout or not at all.
The user can choose one of those four options in a configuration file.
'''

import gettor_config

class gettorLogger:
    '''
    A configurable logging system for gettor.
    '''

    def _init_(self):  
        # parse the configuration file so we know how we're running 
        config = gettorConf()
    
    def log(self, message):
        # Log the message

