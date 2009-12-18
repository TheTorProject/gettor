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
    #                  LANG: ALIASE
    supportedLangs = { "en": ("english", ),
                       "fa": ("farsi", ),
                       "de": ("deutsch", ),
                       "ar": ("arabic", ),
                       "es": ("spanish", ),
                       "fr": ("french", ),
                       "it": ("italian", ),
                       "nl": ("dutch", ),
                       "pl": ("polish", ),
                       "ru": ("russian", ),
                       "zh_CN": ("chinese", "zh",) }

    def __init__(self, config):
        """ Read message from stdin, parse all the stuff we want to know
        """
        # Read email from stdin
        self.rawMessage = sys.stdin.read()
        self.parsedMessage = email.message_from_string(self.rawMessage)

        # WARNING WARNING *** This next line whitelists all ***
        self.signature = True
        self.config = config
        self.gotPlusReq = False
        self.returnPackage = None
        self.splitDelivery = False
        self.commandAddress = None
        self.replyLocale = self.defaultLang
        self.replytoAddress = self.parsedMessage["Return-Path"]
        self.bounce = False
        
        # Filter rough edges
        self.doEarlyFilter()

        # We want to parse, log and act on the "To" field
        self.toAddress = self.parsedMessage["to"]
        log.info("User %s made request to %s" % \
                (self.replytoAddress, self.toAddress))
        self.gotPlusReq = self.matchPlusAddress()

        packager = gettor.packages.Packages(config)
        self.packages = packager.getPackageList()
        assert len(self.packages) > 0, "Empty package list"

        # TODO XXX:
        # This should catch DNS exceptions and fail to verify if we have a 
        # dns timeout
        # We also should catch totally malformed messages here
        #try:
        #           if dkim.verify(self.rawMessage):
        #               self.signature = True
        #       except:
        #           pass

    def parseMail(self):
        if self.parsedMessage.is_multipart():
            for part in self.parsedMessage.walk():
                if part.get_content_maintype() == "text":
                    # We found a text part, parse it
                    self.parseTextPart(part.get_payload(decode=1))
        else:
            self.parseTextPart(part.get_payload(decode=1))

        if self.returnPackage is None:
            log.info("User didn't select any packages")

        return (self.toAddress, self.replytoAddress, self.replyLocale, \
                self.returnPackage, \
                self.splitDelivery, self.signature, self.commandAddress)

    def parseTextPart(self, text):
        text = self.stripTags(text)
        if not self.gotPlusReq:
            self.matchLang(text)
        self.checkLang()
        self.torSpecialPackageExpansion()
    
        self.matchPackage(text)
        self.matchSplit(text)
        self.matchCommand(text)

    def matchPlusAddress(self):
        regexPlus = '.*(<)?(\w+\+(\w+)@\w+(?:\.\w+)+)(?(1)>)'
        match = re.match(regexPlus, self.toAddress)
        if match:
            self.replyLocale = match.group(3)
            log.info("User requested language %s" % self.replyLocale)
            return True
        else:
            log.info("Not a 'plus' address")
            return False

    def matchPackage(self, line):
        for package in self.packages.keys():
            matchme = ".*" + package + ".*"
            match = re.match(matchme, line, re.DOTALL)    
            if match: 
                self.returnPackage = package
                log.info("User requested package %s" % self.returnPackage)
                break

    def matchSplit(self, line):
        # If we find 'split' somewhere we assume that the user wants a split 
        # delivery
        match = re.match(".*split.*", line, re.DOTALL)
        if match:
            self.splitDelivery = True
            log.info("User requested a split delivery")

    def matchLang(self, line):
        match = re.match(".*[Ll]ang:\s+(.*)$", line, re.DOTALL)
        if match:
            self.replyLocale = match.group(1)
            log.info("User requested locale %s" % self.replyLocale)

    def matchCommand(self, line):
        match = re.match(".*[Cc]ommand:\s+(.*)$", line, re.DOTALL)
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
            self.commandAddress = address

    def torSpecialPackageExpansion(self):
        # If someone wants one of the localizable packages, add language 
        # suffix. This isn't nice because we're hard-coding package names here
        # Attention: This needs to correspond to the  packages in packages.py
        if self.returnPackage == "tor-browser-bundle" \
                               or self.returnPackage == "tor-im-browser-bundle":
            # "tor-browser-bundle" => "tor-browser-bundle_de"
	    self.returnPackage = self.returnPackage + "_" + self.replyLocale 

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

    def checkLang(self):
        # Look through our aliases list for languages and check if the user
        # requested an alias rather than an 'official' language name. If he 
        # does, map back to that official name. Also, if the user didn't 
        # request a language we support, fall back to default
        for (lang, aliases) in self.supportedLangs.items():
            if lang == self.replyLocale:
                log.info("User requested lang %s" % lang)
                return
            if aliases is not None:
                for alias in aliases:
                    if alias == self.replyLocale:
                        log.info("Request for %s via alias %s" % (lang, alias))
                        # Set it back to the 'official' name
                        self.replyLocale = lang
                        return
        else:
            log.info("Requested language %s not supported. Falling back to %s" \
                        % (self.replyLocale, self.defaultLang))
            self.replyLocale = self.defaultLang
            return

    def checkInternalEarlyBlacklist(self):
        if re.compile(".*@.*torproject.org.*").match(self.replytoAddress):
            return True
        else:
            return False
            
    def doEarlyFilter(self):
        # Make sure we drop bounce mails
        if self.replytoAddress == "<>":
                log.info("We've received a bounce")
                self.bounce = True
        assert self.bounce is not True, "We've got a bounce. Bye."

        # Make sure we drop stupid from addresses
        badMail = "Mail from address: %s" % self.replytoAddress
        assert self.checkInternalEarlyBlacklist() is False, badMail
