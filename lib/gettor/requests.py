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
    # XXX Move this to the config file
    supportedLangs = { "en": "English", 
                       "fa": "Farsi",
                       "de": "Deutsch",
                       "ar": "Arabic",
                       "es": "Spanish",
                       "fr": "French",
                       "it": "Italian",
                       "nl": "Dutch",
                       "pl": "Polish",
                       "ru": "Russian",
                       "zh_CN": "Chinese"  }

    def __init__(self, config):
        """ Read message from stdin, parse all the stuff we want to know
        """
        self.rawMessage = sys.stdin.read()
        self.parsedMessage = email.message_from_string(self.rawMessage)
        self.signature = False
        self.config = config
        self.gotPlusReq = False
        # TODO XXX:
        # This should catch DNS exceptions and fail to verify if we have a 
        # dns timeout
        # We also should catch totally malformed messages here
        try:
            if dkim.verify(self.rawMessage):
                self.signature = True
        except:
            pass

        self.replyLocale = self.defaultLang
        # We want to parse, log and act on the "To" field
        self.toAddress = self.parsedMessage["to"]
        log.info("User made request to %s" % self.toAddress)
        # Check if we got a '+' address
        self.matchPlusAddress()
        # TODO XXX: 
        # Scrub this data
        self.replytoAddress = self.parsedMessage["from"]
        assert self.replytoAddress is not None, "No 'from' field in mail"
        # If no package name could be recognized, use 'None'
        self.returnPackage = None
        self.splitDelivery = False
        self.commandaddress = None
        packager = gettor.packages.Packages(config)
        self.packages = packager.getPackageList()
        assert len(self.packages) > 0, "Empty package list"

    def parseMail(self):
    	# First of all, check what language the user wants
        if not self.gotPlusReq:
	    self.findOutLang()
        self.checkLang()
        # Parse line by line
        for line in email.Iterators.body_line_iterator(self.parsedMessage):
            # Skip quotes
            if line.startswith(">"):
                continue
            # Strip HTML from line
            # XXX: Actually we should rather read the whole body into a string
            #      and strip that. -kaner
            line = self.stripTags(line)
            # Check for package name in line
            self.matchPackage(line)
            # Check for split delivery in line
            self.matchSplit(line)
            # Check if this is a command
            self.matchCommand(line)

	# XXX HACK
	self.torSpecialPackageExpansion()
    
        if self.returnPackage is None:
            log.info("User didn't select any packages")

        return (self.replytoAddress, self.replyLocale, self.returnPackage, \
                self.splitDelivery, self.signature, self.commandaddress)

    def findOutLang(self):
        # Parse line by line
        for line in email.Iterators.body_line_iterator(self.parsedMessage):
            # Skip quotes
            if line.startswith(">"):
                continue
            # Strip HTML from line
            # XXX: Actually we should rather read the whole body into a string
            #      and strip that. -kaner
            line = self.stripTags(line)
	    # Check to see if we got a language request with 'Lang:'
	    self.matchLang(line)
        

    def matchPlusAddress(self):
        match = re.search('(?<=\+)\w+', self.toAddress)
        if match:
            # Cut back and front
            splitFrontPart = self.toAddress.split('@')
            assert len(splitFrontPart) > 0, "Splitting To: address failed"
            splitLang = splitFrontPart[0].rsplit('+')
            assert len(splitLang) > 1, "Splitting for language failed"
            self.replyLocale = splitLang[1]
            # Mark this request so that we might be able to take decisions 
            # later
            self.gotPlusReq = True
            log.info("User requested language %s" % self.replyLocale)
        else:
            log.info("Not a 'plus' address")

    def matchPackage(self, line):
        # XXX This is a bit clumsy, but i cant think of a better way
        # currently. A map also doesnt really help i think. -kaner
        for package in self.packages.keys():
            matchme = ".*" + package + ".*"
            match = re.match(matchme, line)    
            if match: 
                self.returnPackage = package
                log.info("User requested package %s" % self.returnPackage)
                break

    def matchSplit(self, line):
        # If we find 'split' somewhere we assume that the user wants a split 
        # delivery
        match = re.match(".*split.*", line)
        if match:
            self.splitDelivery = True
            log.info("User requested a split delivery")

    def matchLang(self, line):
        match = re.match(".*[Ll]ang:\s+(.*)$", line)
        if match:
            self.replyLocale = match.group(1)
            log.info("User requested locale %s" % self.replyLocale)

    def matchCommand(self, line):
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

    def torSpecialPackageExpansion(self):
        # If someone wants one of the localizable packages, add language 
        # suffix. This isn't nice because we're hard-coding package names here
        # Attention: This needs to correspond to the  packages in packages.py
        if self.returnPackage == "tor-browser-bundle" \
                               or self.returnPackage == "tor-im-browser-bundle":
            # "tor-browser-bundle" => "tor-browser-bundle_de"
	    self.returnPackage = self.returnPackage + "_" + self.replyLocale 

    def checkLang(self):
        # Actually use a map here later XXX
        for (key, lang) in self.supportedLangs.items():
            if self.replyLocale == key:
                log.info("User requested language %s" % self.replyLocale)
                break
        else:
            log.info("Requested language %s not supported. Falling back to %s" \
                        % (self.replyLocale, self.defaultLang))
            self.replyLocale = self.defaultLang

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
