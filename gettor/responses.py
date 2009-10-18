#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
"""
 gettor_config.py - Parse configuration file for gettor

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

 This library implements all of the email replying features needed for gettor. 
"""

import os
import smtplib
import MimeWriter
import StringIO
import base64
import gettext
import re

import gettor.gtlog
import gettor.blacklist
import gettor.constants

__all__ = ["Response"]

log = gettor.gtlog.getLogger()

class Response:

    def __init__(self, config, replyto, lang, package, split, signature, caddr):
        self.config = config
        self.srcEmail = "GetTor <gettor@torproject.org>"
        self.replyTo = replyto
        assert self.replyTo is not None, "Empty replyto address."
        self.mailLang = lang
        self.package = package
        self.splitsend = split
        self.signature = signature
        self.cmdAddr = caddr
        # If cmdAddr is set, we are forwarding mail rather than sending a 
        # reply to someone
        if self.cmdAddr is not None:
            self.sendTo = self.cmdAddr
        else:
            self.sendTo = self.replyTo
        self.whiteList = gettor.blacklist.BWList(config.getWlStateDir())
        self.blackList = gettor.blacklist.BWList(config.getBlStateDir())
        try:
            trans = gettext.translation("gettor", config.getLocaleDir(), [lang])
            trans.install()
        except IOError:
            log.error("Translation fail. Trying running with -r.")
            raise

    def sendReply(self):
        """All routing decisions take place here."""
        # Check we're happy with sending this user a package
        if not self.signature and not self.cmdAddr \
           and not self.whiteList.lookupListEntry(self.replyTo) \
           and not re.compile(".*@yahoo.com.cn").match(self.replyTo) \
           and not re.compile(".*@yahoo.cn").match(self.replyTo) \
           and not re.compile(".*@gmail.com").match(self.replyTo):
            blackListed = self.blackList.lookupListEntry(self.replyTo)
            if blackListed:
                log.info("Unsigned messaged to gettor by blacklisted user dropped.")
                return False
            else:
                # Reply with some help and bail out
                self.blackList.createListEntry(self.replyTo)
                log.info("Unsigned messaged to gettor. We will issue help.")
                return self.sendHelp()
        else:
            if self.cmdAddr is not None:
                success = self.sendPackage()
                if not success:
                    log.error("Failed to forward mail to '%s'" % self.cmdAddr)
                return self.sendForwardReply(success)
                
            if self.package is None:
                return self.sendPackageHelp()
            delayAlert = self.config.getDelayAlert()
            if delayAlert:
                ret = self.sendDelayAlert()
                if ret != True:
                    log.error("Failed to sent delay alert.")
            if self.splitsend:
                return self.sendSplitPackage()
            else:
                return self.sendPackage()

    def sendPackage(self):
        """ Send a message with an attachment to the user"""
        log.info("Sending out %s to %s." % (self.package, self.sendTo))
        packages = gettor.packages.Packages(self.config)
        packageList = packages.getPackageList()
        filename = packageList[self.package]
        message = gettor.constants.packagemsg
        package = self.constructMessage(message, "", filename)
        try:
            status = self.sendMessage(package)
        except:
            log.error("Could not send package to user")
            status = False

        log.info("Send status: %s" % status)
        return status

    def sendSplitPackage(self):
        """XXX XXX XXX alpha state XXX XXX XXX"""
        splitdir = self.config.getPackDir() + "/" + self.package + ".split"
        try:
            entry = os.stat(splitdir)
        except OSError, e:
            log.error("Not a valid directory: %s" % splitdir)
            return False
        files = os.listdir(splitdir)
        # Sort the files, so we can send 01 before 02 and so on..
        files.sort()
        nFiles = len(files)
        num = 0
        for filename in files:
            fullPath = splitdir + "/" + filename
            num = num + 1
            subj = "[GetTor] Split package [%02d / %02d] " % (num, nFiles) 
            message = gettor.constants.splitpackagemsg
            package = self.constructMessage(message, subj, fullPath)
            try:
                status = self.sendMessage(package)
            except:
                log.error("Could not send package %s to user" % filename)
                # XXX What now? Keep on sending? Bail out? Use might have 
                # already received 10 out of 12 packages..
                status = False

        return status

    def sendDelayAlert(self):
        """ Send a delay notification """
        log.info("Sending delay alert to %s" % self.sendTo)
        return self.sendGenericMessage(gettor.constants.delayalertmsg)
            
    def sendHelp(self):
        """ Send a helpful message to the user interacting with us """
        log.info("Sending out help message to %s" % self.sendTo)
        return self.sendGenericMessage(gettor.constants.helpmsg)

## XXX the following line was used below to automatically list the names
## of available packages. But they were being named in an arbitrary
## order, which caused people to always pick the first one. I listed
## tor-browser-bundle first since that's the one they should want.
## Somebody should figure out how to automate yet sort. -RD
##    """ + "".join([ "\t%s\n" % key for key in packageList.keys()]) + """

    def sendPackageHelp(self):
        """ Send a helpful message to the user interacting with us """
        log.info("Sending package help to %s" % self.sendTo)
        return self.sendGenericMessage(gettor.constants.packagehelpmsg)

    def sendForwardReply(self, status):
        " Send a message to the user that issued the forward command """
        log.info("Sending reply to forwarder '%s'" % self.replyTo)
        message = "Forwarding mail to '%s' status: %s" % (self.sendTo, status)
        # Magic: We're now returning to the original issuer
        self.sendTo = self.replyTo
        return self.sendGenericMessage(message)

    def sendGenericMessage(self, text):
        """ Send a message of some sort """
        message = self.constructMessage(text, "")
        try:
            status = self.sendMessage(message)
        except:
            log.error("Could not send message to user %s" % self.sendTo)
            status = False

        log.info("Send status: %s" % status)
        return status

    def constructMessage(self, messageText, subj, fileName=None):
        """ Construct a multi-part mime message, including only the first part
        with plaintext."""

        if subj == "":
            subj =_('[GetTor] Your request')
        message = StringIO.StringIO()
        mime = MimeWriter.MimeWriter(message)
        mime.addheader('MIME-Version', '1.0')
        mime.addheader('Subject', subj)
        mime.addheader('To', self.sendTo)
        mime.addheader('From', self.srcEmail)
        mime.startmultipartbody('mixed')

        firstPart = mime.nextpart()
        emailBody = firstPart.startbody('text/plain')
        emailBody.write(messageText)

        # Add a file if we have one
        if fileName:
            filePart = mime.nextpart()
            filePart.addheader('Content-Transfer-Encoding', 'base64')
            emailBody = filePart.startbody('application/zip; name=%s' % os.path.basename(fileName))
            base64.encode(open(fileName, 'rb'), emailBody)

        # Now end the mime messsage
        mime.lastpart()
        return message

    def sendMessage(self, message, smtpserver="localhost:25"):
        try:
            smtp = smtplib.SMTP(smtpserver)
            smtp.sendmail(self.srcEmail, self.sendTo, message.getvalue())
            smtp.quit()
            status = True
        except smtplib.SMTPAuthenticationError:
            log.error("SMTP authentication error")
            return False
        except smtplib.SMTPHeloError:
            log.error("SMTP HELO error")
            return False
        except smtplib.SMTPConnectError:
            log.error("SMTP connection error")
            return False
        except smtplib.SMTPDataError:
            log.error("SMTP data error")
            return False
        except smtplib.SMTPRecipientsRefused:
            log.error("SMTP refused to send to recipients")
            return False
        except smtplib.SMTPSenderRefused:
            log.error("SMTP sender address refused")
            return False
        except smtplib.SMTPResponseException:
            log.error("SMTP response exception received")
            return False
        except smtplib.SMTPServerDisconnected:
            log.error("SMTP server disconnect exception received")
            return False
        except smtplib.SMTPException:
            log.error("General SMTP error caught")
            return False
        except:
            log.error("Unknown SMTP error while trying to send via local MTA")
            return False

        return status
