# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

import sys
import email
import re
import logging

import gettor.utils
import gettor.packages
import gettor.filters

class requestMail:
    def __init__(self, config):
        """ Read message from stdin, try to assign some values already.
        """
        # Read email from stdin
        self.rawMessage = sys.stdin.read()
        self.parsedMessage = email.message_from_string(self.rawMessage)

        self.config = config
        self.request = {}
        self.request['user'] = self.parsedMessage["Return-Path"]
        # Normalize address before hashing
        normalized_addr = gettor.utils.normalizeAddress(self.request['user'])
        self.request['hashed_user'] = gettor.utils.getHash(normalized_addr)
        self.request['ouraddr'] = self.getRealTo(self.parsedMessage["to"])
        self.request['locale'] = self.getLocaleInTo(self.request['ouraddr'])
        self.request['package'] = None
        self.request['split'] = False
        self.request['forward'] = None
        self.request['valid'] = False # This will get set by gettor.filters

    def getRealTo(self, toField):
        """If someone wrote to `gettor+zh_CN@torproject.org', the `From:' field
           in our reply should reflect that. So, use the `To:' field from the
           incoming mail, but filter out everything except the gettor@ address.
        """
        regexGettor = '.*(<)?(gettor.*@.*torproject.org)+(?(1)>).*'
        toField = gettor.filters.doToAddressHack(toField)
        logging.debug("toField: %s" % toField)
        match = re.match(regexGettor, toField)
        if match:
            return match.group(2)
        else:
            # Fall back to default From: address
            return self.config.MAIL_FROM

    def getLocaleInTo(self, address):
        """See whether the user sent his email to a 'plus' address, for 
           instance to gettor+fa@tpo. Plus addresses are the current 
           mechanism to set the reply language
        """
        regexPlus = '.*(<)?(\w+\+(\w+)@\w+(?:\.\w+)+)(?(1)>)'
        match = re.match(regexPlus, address)
        if match:
            locale = match.group(3)
            logging.debug("User requested language %s" % locale)
            return self.checkAndGetLocale(locale)
        else:
            logging.debug("Not a 'plus' address")
            return self.config.DEFAULT_LOCALE

    def parseMail(self):
        """Main mail parsing routine. Returns a RequestVal value class
        """
        if self.parsedMessage.is_multipart():
            for part in self.parsedMessage.walk():
                if part.get_content_maintype() == "text":
                    # We found a text part, parse it
                    self.parseTextPart(part.get_payload(decode=1))
        else:
            # Not a multipart message, just parse along what we've got
            self.parseTextPart(self.parsedMessage.get_payload(decode=1))

        if self.request['package'] is None:
            logging.debug("User didn't select any packages")

        return self.request

    def parseTextPart(self, text):
        """If we've found a text part in a multipart email or if we just want
           to parse a non-multipart message, this is the routine to call with
           the text body as its argument
        """
        lines = gettor.utils.stripHTMLTags(text).split('\n')
        for line in lines:
            if self.request['package'] is None:
                self.request['package'] = self.matchPackage(line)
            if self.request['split'] is False:
                self.request['split'] = self.matchSplit(line)
            if self.request['forward'] is None:
                self.request['forward'] = self.matchForwardCommand(line)

    def matchPackage(self, line):
        """Look up which package the user is requesting.
        """
        # XXX HACK ALERT: This makes it possible for users to still request
        #                 the windows bundle by its old name
        packages_hacked = self.config.PACKAGES
        packages_hacked['tor-browser-bundle'] = ()
        for p in self.config.PACKAGES.keys():
            matchme = ".*" + p + ".*"
            match = re.match(matchme, line, re.DOTALL)    
            if match: 
                logging.debug("User requested package %s" % p)
                return p

        return None

    def matchSplit(self, line):
        """If we find 'split' somewhere we assume that the user wants a split 
           delivery
        """
        match = re.match("\s*split.*", line, re.DOTALL)
        if match:
            logging.debug("User requested a split delivery")
            return True
        else:
            return False

    def matchForwardCommand(self, line):
        """Check if we have a command from the GetTor admin in this email.
           Command lines always consists of the following syntax:
           'Command: <password> <command part 1> <command part 2>'
           For the forwarding command, part 1 is the email address of the
           recipient, part 2 is the package name of the package that needs
           to be forwarded.
           The password is checked against the password found in the file
           configured as cmdPassFile in the GetTor configuration.
        """
        match = re.match(".*[Cc]ommand:\s+(.*)$", line, re.DOTALL)
        if match:
            logging.debug("Command received from %s" % self.request['user']) 
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
                    % self.request['user']
            return address
        else:
            return None

    def checkAndGetLocale(self, locale):
        """Look through our aliases list for languages and check if the user
           requested an alias rather than an 'official' language name. If he 
           does, map back to that official name. Also, if the user didn't 
           request a language we support, fall back to default.
        """
        for (lang, aliases) in self.config.SUPP_LANGS.items():
            if lang == locale:
                return locale
            if aliases is not None:
                if locale in aliases:
                    logging.debug("Request for %s via alias %s" % (lang, locale))
                    # Return the 'official' name
                    return lang
        else:
            logging.debug("Requested language %s not supported. Fallback: %s" \
                              % (self.replyLocale, self.config.DEFAULT_LOCALE))
            self.replyLocale = self.config.DEFAULT_LOCALE
            return self.config.DEFAULT_LOCALE

    def getRawMessage(self):
        return self.rawMessage
