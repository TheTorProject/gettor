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

import gettor.gtlog
import gettor.packages

__all__ = ["requestMail"]

log = gettor.gtlog.getLogger()

class requestMail:

    defaultLang = "en"
    # XXX
    supportedLangs = { "en": "English", 
                       "de": "Deutsch" }

    def __init__(self, config):
        """ Read message from stdin, parse all the stuff we want to know
        """
        self.rawMessage = sys.stdin.read()
        self.parsedMessage = email.message_from_string(self.rawMessage)
        self.signature = False
        self.config = config
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
        self.replytoAddress = self.parsedMessage["from"]
        assert self.replytoAddress is not None, "Replyto address is None"
        # If no package name could be recognized, use 'None'
        self.returnPackage = None
        self.splitDelivery = False
        self.commandaddress = None
        self.replyLocale = "en-US"
        packager = gettor.packages.Packages(config)
        self.packages = packager.getPackageList()
        assert len(self.packages) > 0, "Empty package list"

    def parseMail(self):
        # Parse line by line
        for line in email.Iterators.body_line_iterator(self.parsedMessage):
            # Remove quotes
            if line.startswith(">"):
                continue
            # Strip HTML from line
            # XXX: Actually we should rather read the whole body into a string
            #      and strip that. -kaner
            line = self.stripTags(line)
            # XXX This is a bit clumsy, but i cant think of a better way
            # currently. A map also doesnt really help i think. -kaner
            for package in self.packages.keys():
                matchme = ".*" + package + ".*"
                match = re.match(matchme, line)    
                if match: 
                    self.returnPackage = package
                    log.info("User requested package %s" % self.returnPackage)
                    break
            # If we find 'split' somewhere in the mail, we assume that the user 
            # wants a split delivery
            match = re.match(".*split.*", line)
            if match:
                self.splitDelivery = True
                log.info("User requested a split delivery")
            # Default locale is english
            match = re.match(".*[Ll]ang:\s+(.*)$", line)
            if match:
                self.replyLocale = match.group(1)
                log.info("User requested locale %s" % self.replyLocale)
            # Check if this is a command
            match = re.match(".*[Cc]ommand:\s+(.*)$", line)
            if match:
                log.info("Command received from %s" % self.replytoAddress) 
                cmd = match.group(1).split()
                length = len(cmd)
                assert length == 3, "Wrong command syntax"
                auth = cmd[0]
                # Package is parsed by the usual package parsing mechanism
                package = cmd[1]
                address = cmd[2]
                verified = gettor.utils.verifyPassword(self.config, auth)
                assert verified == True, \
                        "Unauthorized attempt to command from: %s" \
                        % self.replytoAddress
                self.commandaddress = address

        if self.returnPackage is None:
            log.info("User didn't select any packages")
        # Actually use a map here later XXX
        for (key, lang) in self.supportedLangs.items():
            if self.replyLocale == key:
                break
        else:
            log.info("Requested language %s not supported. Falling back to %s" \
                        % (self.replyLocale, self.defaultLang))
            self.replyLocale = self.defaultLang

        return (self.replytoAddress, self.replyLocale, self.returnPackage, \
                self.splitDelivery, self.signature, self.commandaddress)

    def stripTags(self, string):
        """Simple HTML stripper"""
        return re.sub(r'<[^>]*?>', '', string)

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

    def getSplitDelivery(self):
        return self.splitDelivery

    def getAll(self):
        return (self.replytoAddress, self.replyLocale, \
                self.returnPackage, self.splitDelivery, self.signature)
