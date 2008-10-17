#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
"""
 gettor_config.py - Parse configuration file for gettor

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

 This library implements all of the email parsing features needed for gettor.
"""

import sys
import email
import dkim
import re

__all__ = ["requestMail"]

class requestMail:

    defaultLang = "en"
    supportedLangs = { "en": "English", 
                       "de": "Deutsch" }

    def __init__(self, packages):
        """
        Read message from stdin, parse all the stuff we want to know
        """
        self.rawMessage = sys.stdin.read()
        self.parsedMessage = email.message_from_string(self.rawMessage)
        self.signature = False
        # TODO XXX:
        # This should catch DNS exceptions and fail to verify if we have a 
        # dns timeout
        # We also should catch totally malformed messages here
        try:
            if dkim.verify(self.rawMessage):
                self.signature = True
        except:
            pass

        # TODO XXX: 
        # Scrub this data
        self.replyToAddress = None
        self.replytoAddress = self.parsedMessage["from"]
        # If no package name could be recognized, use 'None'
        self.returnPackage = None
        # XXX TODO:
        # Should we pick only the first line of the email body. Drop the rest?
        # It may be too unfriendly to our users
        for line in email.Iterators.body_line_iterator(self.parsedMessage):
            for package in packages.keys():
                match = re.match(package, line)    
                if match: 
                    self.returnPackage = package

        self.replyLocale = None
        pattern = re.compile("^Lang:\s+(.*)$")
        for line in email.Iterators.body_line_iterator(self.parsedMessage):
            match = pattern.match(line)
            if match:
                self.replyLocale = match.group(1)

        for (key, lang) in self.supportedLangs.items():
            if self.replyLocale == key:
                break
        else:
            self.replyLocale = self.defaultLang

    def getRawMessage(self):
        return self.rawMessage

    def hasVerifiedSignature(self):
        return self.signature

    def getParsedMessage(self):
        return self.parsedMessage

    def getReplyTo(self):
        return self.replytoAddress

    def getPackage(self):
        return self.returnPackage

    def getLocale(self):
        return self.replyLocale

if __name__ == "__main__" :
    """ Give us an email to understand what we think of it. """
    packageList = { 
        "windows-bundle": "/var/lib/gettor/pkg/windows-bundle.z",
        "macosx-bundle": "/var/lib/gettor/pkg/macosx-bundle.z",
        "linux-bundle": "/var/lib/gettor/pkg/linux-bundle.z",
        "source-bundle": "/var/lib/gettor/pkg/source-bundle.z"
        }

    rmail = requestMail(packageList)
    print "Fetching raw message."
    rawMessage = rmail.getRawMessage()
    # This doesn't work without DNS ( no wifi on board current airplane )
    print "Verifying signature of message."
    signature = rmail.hasVerifiedSignature()
    print "Parsing Message."
    parsedMessage = rmail.getParsedMessage()
    print "Parsing reply."
    parsedReply = rmail.getReplyTo()
    print "Parsing package request."
    package = rmail.getRequestPackage()
    if package == None:
        packageFile = "help"        
    else:
        packageFile = packageList[package]

    print "The signature status of the email is: %s" % str(signature)
    print "The email requested the following reply address: %s" % parsedReply
    print "It looks like the email requested the following package: %s" % package
    print "We would select the following package file: %s" % packageFile
