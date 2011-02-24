# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

import os
import re
import sys
import smtplib
import gettext
import logging

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

import gettor.blacklist
import gettor.i18n as i18n

def getPackageHelpMsg(t):
        return t.gettext(i18n.GETTOR_TEXT[0]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[6]) + "\n\n" \
             + """        tor-browser-bundle
        macosx-i386-bundle
        macosx-ppc-bundle
        linux-browser-bundle-i386
        linux-browser-bundle-x86_64
        source-bundle""" + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[7]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[8]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[9]) + "\n\n" \
             + "        gettor+zh_CN@torproject.org" + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[10]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[11]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[12]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[13]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[14]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[15]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[16]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[17]) + "\n\n" \
             + "        tor-browser-bundle" + "\n" \
             + "        split" + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[18]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[19]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[20]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[21]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[22]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[23]) + "\n\n" \
             + "        http://www.win-rar.com/download.html" + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[23]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[24]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[25]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[26]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[27]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[28]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[33]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[34]) + "\n\n" \
             + "        bridges@torproject.org" + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[34]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[35]) + "\n"
                
def getPackageMsg(t):
        return t.gettext(i18n.GETTOR_TEXT[0]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[29]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[30]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[31]) + "\n\n" \
             + "  gpg: Good signature from 'Roger Dingledine <arma@mit.edu>'" \
             + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[32]) + "\n\n" \
             + "  http://www.gnupg.org/related_software/frontends.html" \
             + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[33]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[34]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[35]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[27]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[28]) + "\n"

def getSplitPackageMsg(t):
        return t.gettext(i18n.GETTOR_TEXT[0]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[36]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[37]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[19]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[20]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[21]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[22]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[23]) + "\n\n" \
             + "        http://www.win-rar.com/download.html" + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[24]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[25]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[26]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[27]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[28]) + "\n"

def getDelayAlertMsg(t):
        return t.gettext(i18n.GETTOR_TEXT[0]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[38]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[39]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[27]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[28]) + "\n"

class Response:
    def __init__(self, config, reqInfo):
        """Intialize the reply class. The most important values are passed in
           via the 'reqInfo' dict. 
        """
        self.config = config
        self.reqInfo = reqInfo

        # Dump info
        logging.info(str(self.reqInfo))

        # Initialize locale subsystem
        self.t = i18n.getLang(self.reqInfo['locale'], config)

        # Init black & whitelists
        wlStateDir = os.path.join(self.config.BASEDIR, "wl")
        blStateDir = os.path.join(self.config.BASEDIR, "bl")
        self.wList = gettor.blacklist.BWList(wlStateDir)
        self.bList = gettor.blacklist.BWList(blStateDir)

    def sendReply(self):
        """All routing decisions take place here. Sending of mails takes place
           here, too.
        """
        if self.isAllowed():
            # Ok, see what we've got here.
            # Should we forward a certain package?
            if self.reqInfo['forward'] is not None:
                return self.forwardPackage()
            # Did the user choose a package?
            if self.reqInfo['package'] is None:
                return self.sendPackageHelp()
            # Be a polite bot and send message that mail is on the way
            if self.config.DELAY_ALERT:
                if not self.sendDelayAlert():
                    logging.error("Failed to sent delay alert.")
            # Did the user request a split or normal package download?
            if self.reqInfo['split']:
                return self.sendSplitPackage()
            else:
                return self.sendPackage()

    def isAllowed(self):
        """Do all checks necessary to decide whether the reply-to user is 
           allowed to get a reply by us.
        """
        return True # *g*

    def isBlacklistedForMessageType(self, fname):
        """This routine takes care that for each function fname, a given user
           can access it only once. The 'fname' parameter carries the message
           type name we're looking for
        """
        # First of all, check if user is whitelisted: Whitelist beats Blacklist
        if self.wList.lookupListEntry(self.reqInfo['user'], "general"):
            logging.info("Whitelisted user " + self.reqInfo['user'])
            return False
        # Now check general and specific blacklists, in that order
        if self.bList.lookupListEntry(self.reqInfo['user'], "general"):
            logging.info("Blacklisted user " + self.reqInfo['user'])
            return True
        # Create a unique dir name for the requested routine
        self.bList.createSublist(fname)
        if self.bList.lookupListEntry(self.reqInfo['user'], fname):
            logging.info("User %s is blacklisted for %s" \
                                   % (self.reqInfo['user'], fname))
            return True
        else:
            self.bList.createListEntry(self.reqInfo['user'], fname)
            return False

    def sendPackage(self):
        """ Send a message with an attachment to the user. The attachment is 
            chosen automatically from the selected self.reqInfo['package']
        """
        pack = self.reqInfo['package']
        to = self.reqInfo['user']
        if self.isBlacklistedForMessageType("sendPackage"):
            # Don't send anything
            return False
        logging.info("Sending out %s to %s." % (pack, to))
        f = os.path.join(self.config.BASEDIR, "packages", pack + ".z")
        txt = getPackageMsg(self.t)
        msg = self.makeMsg(txt, to, fileName=f)
        try:
            status = self.sendEmail(to, msg)
        except:
            logging.error("Could not send package to user")
            status = False

        logging.debug("Send status: %s" % status)
        return status

    def forwardPackage(self):
        """ Forward a certain package to a user. Also send a message to the
            one sending in the forward command.
        """
        pack = self.reqInfo['package']
        fwd = self.reqInfo['forward']
        to = self.reqInfo['user']
        logging.info("Sending out %s to %s."  % (pack, fwd))
        f = os.path.join(self.config.BASEDIR, "packages", pack + ".z")
        text = getPackageMsg(self.t)
        msg = self.makeMsg(text, fwd, fileName=f)
        try:
            status = self.sendEmail(fwd, msg)
        except:
            logging.error("Could not forward package to user")
            status = False

        logging.info("Sending reply to forwarder '%s'" % to)
        text = "Forwarding mail to '%s' status: %s" % (fwd, status)
        msg = self.makeMsg(text, to)
        try:
            status = self.sendEmail(to, msg)
        except:
            logging.error("Could not send information to forward admin")

        return status

    def sendSplitPackage(self):
        """Send a number of messages with attachments to the user. The number
           depends on the number of parts of the package.
        """
        if self.isBlacklistedForMessageType("sendSplitPackage"):
            # Don't send anything
            return False

        # XXX
        # Danger, Will Robinson: We assume that the split package is named
        # `package.split' -- this is stupid because we let the user configure
        # split package names in gettor.conf.
        splitpack = self.reqInfo['package'] + ".split"
        splitDir = os.path.join(self.config.BASEDIR, "packages", splitpack)
        fileList = os.listdir(splitDir)
        # Sort the files, so we can send 01 before 02 and so on..
        fileList.sort()
        nFiles = len(fileList)
        num = 0
        # For each available split file, send a mail
        for filename in fileList:
            path = os.path.join(splitDir, filename)
            num = num + 1
            sub = "[GetTor] Split package [%02d / %02d] " % (num, nFiles) 
            txt = getSplitPackageMsg(self.t)
            msg = self.makeMsg(txt, self.reqInfo['user'], sub, fileName=path)
            try:
                status = self.sendEmail(self.reqInfo['user'], msg)
                logging.info("Package [%02d / %02d] sent. Status: %s" \
                                                    % (num, nFiles, status))
            except:
                logging.error("Could not send package %s to user" % filename)
                # XXX What now? Keep on sending? Bail out? Use might have 
                # already received 10 out of 12 packages..
                status = False

        return status

    def sendDelayAlert(self):
        """Send a polite delay notification
        """
        if self.isBlacklistedForMessageType("sendDelayAlert"):
            # Don't send anything
            return False
        logging.info("Sending delay alert to %s" % self.reqInfo['user'])
        return self.sendTextEmail(getDelayAlertMsg(self.t))
            
    def sendHelp(self):
        """Send a help mail. This happens when a user sent us a request we 
           didn't really understand
        """
        if self.isBlacklistedForMessageType("sendHelp"):
            # Don't send anything
            return False
        logging.info("Sending out help message to %s" % self.reqInfo['user'])
        return self.sendTextEmail(getPackageHelpMsg(self.t))

    def sendPackageHelp(self):
        """Send a helpful message to the user interacting with us about
           how to select a proper package
        """
        if self.isBlacklistedForMessageType("sendPackageHelp"):
            # Don't send anything
            return False
        logging.info("Sending package help to %s" % self.reqInfo['user'])
        return self.sendTextEmail(i18n.MULTILANGHELP)

    def sendTextEmail(self, text):
        """Generic text message sending routine.
        """
        message = self.makeMsg(text, self.reqInfo['user'])
        try:
            status = self.sendEmail(self.reqInfo['user'], message)
        except:
            logging.error("Could not send message to user %s" \
                                                % self.reqInfo['user'])
            status = False

        logging.debug("Send status: %s" % status)
        return status

    def makeMsg(self, txt, to, sub="[GetTor] Your Request", fileName=None):
        """Construct a multi-part mime message, including only the first part
           with plaintext.
        """
        # Build message, add header
        message = MIMEMultipart()
        message['Subject'] = sub
        message['To'] = to
        message['From'] = self.reqInfo['ouraddr']
        
        # Add text part
        mText = MIMEText(txt, _subtype="plain", _charset="utf-8")
        message.attach(mText)

        # Add a file part only if we have one
        if fileName:
            filePart = MIMEBase("application", "zip")
            fp = open(fileName, 'rb')
            filePart.set_payload(fp.read())
            fp.close()
            encoders.encode_base64(filePart)
            # Add file part
            f = os.path.basename(fileName)
            filePart.add_header('Content-Disposition', 'attachment', filename=f)
            message.attach(filePart)

        return message

    def sendEmail(self, sendTo, message, smtpserver="localhost:25"):
        """Send out message via STMP. If an error happens, be verbose about 
           the reason
        """
        try:
            smtp = smtplib.SMTP(smtpserver)
            smtp.sendmail(self.reqInfo['ouraddr'], sendTo, message.as_string())
            smtp.quit()
            status = True
        except smtplib.SMTPAuthenticationError:
            logging.error("SMTP authentication error")
            return False
        except smtplib.SMTPHeloError:
            logging.error("SMTP HELO error")
            return False
        except smtplib.SMTPConnectError:
            logging.error("SMTP connection error")
            return False
        except smtplib.SMTPDataError:
            logging.error("SMTP data error")
            return False
        except smtplib.SMTPRecipientsRefused:
            logging.error("SMTP refused to send to recipients")
            return False
        except smtplib.SMTPSenderRefused:
            logging.error("SMTP sender address refused")
            return False
        except smtplib.SMTPResponseException:
            logging.error("SMTP response exception received")
            return False
        except smtplib.SMTPServerDisconnected:
            logging.error("SMTP server disconnect exception received")
            return False
        except smtplib.SMTPException:
            logging.error("General SMTP error caught")
            return False
        except Exception as e:
            logging.error("Unknown SMTP error while sending via local MTA")
            logging.error("Here is the exception I saw: %s" % sys.exc_info()[0])
            logging.error("Detail: %s" %e)

            return False

        return status
