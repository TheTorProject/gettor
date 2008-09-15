#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
This grabs configurable values from the users' gettor config file
if that file is not present, it will supply reasonable defaults.
'''

import os
import sys
import ConfigParser

class gettorConf:
    '''
    Initialize gettor with default values if one or more
    values are missing from the config file.
    This will return entirely default values if the configuration file is
    missing. Our default file location is ~/.gettorrc for the current user.
    '''

    stateDir = "/var/lib/gettor/"
    blStateDir = stateDir + "bl/"
    srcEmail = "gettor@torproject.org"
    distDir = "/var/lib/gettor/pkg/"
    locale = "en"
    logSubSystem = "nothing"
    logFile = "/dev/null"
    configFile = "~/.gettorrc"
    config = ConfigParser.ConfigParser()

    def __init__(self, path = os.path.expanduser(configFile)):

        self.configFile = os.path.expanduser(path)

        try:
            if os.access(self.configFile, os.R_OK):
                readableConfigFile = True
            else:
                readableConfigFile = False

        except OSError:
            readableConfigFile = False

        if readableConfigFile: 
            try:
                # It's likely that a user will make a mistake in their config
                # If they make a mistake for now we'll ignore *everything* :-)
                self.config.read(self.configFile)
            except:
                self.config.add_section("global")
        else:
            self.config.add_section("global")

        if self.config.has_option("global", "stateDir"):
            self.stateDir = self.config.get("global", "stateDir")
        else:
            self.config.set("global", "stateDir", self.stateDir)

        if self.config.has_option("global", "blStateDir"):
            self.blStateDir = self.config.get("global", "blStateDir")
        else:
            self.config.set("global", "blStateDir", self.blStateDir)

        if self.config.has_option("global", "srcEmail"):
            self.srcEmail = self.config.get("global", "srcEmail")
        else:
            self.config.set("global", "srcEmail", self.srcEmail)

        if self.config.has_option("global", "distDir"):
            self.distDir = self.config.get("global", "distDir")
        else:
            self.config.set("global", "distDir", self.distDir)

        if self.config.has_option("global", "locale"):
            self.locale = self.config.get("global", "locale")
        else:
            self.config.set("global", "locale", self.locale)

        if self.config.has_option("global", "logSubSystem"):
            self.logSubSystem = self.config.get("global", "logSubSystem")
        else:
            self.config.set("global", "logSubSystem", self.logSubSystem)

        if self.config.has_option("global", "logFile"):
            self.logFile = self.config.get("global", "logFile")
        else:
            self.config.set("global", "logFile", self.logFile)

    def printConfiguration(self):
        return self.config.write(sys.stdout)

    # All getter routines live below
    def getStateDir(self):
        return self.stateDir

    def getBlStateDir(self):
        return self.blStateDir

    def getSrcEmail(self):
        return self.srcEmail

    def getDistDir(self):
        return self.distDir

    def getLocale(self):
        return self.locale

    def getLogSubSystem(self):
        return self.logSubSystem

    def getLogFile(self):
        return self.logFile

if __name__ == "__main__" :
    c = gettorConf()
    print "# This is a suitable default configuration. Tune to fit your needs."
    c.printConfiguration()
