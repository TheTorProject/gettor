# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

import os
import re
import sys
import copy
import smtplib
import gettext
import logging

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

import gettor.blacklist
import gettor.utils
import gettor.i18n as i18n

def getGreetingText(t):
    return t.gettext(i18n.GETTOR_TEXT[0]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[1]) + "\n\n"

def getPackageHelpText(t):
    return t.gettext(i18n.GETTOR_TEXT[6]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[46]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[47]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[48]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[51]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[49]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[50]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[51]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[52]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[51]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[53]) + "\n\n"

def getLocalizedVersionHelpText(t):
    return t.gettext(i18n.GETTOR_TEXT[8]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[9]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[10]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[12]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[13]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[14]) + "\n\n"

def getBridgesHelpText(t):
    return t.gettext(i18n.GETTOR_TEXT[32]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[33]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[34]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[35]) + "\n\n"

def getGeneralHelpText(t):
    return getGreetingText(t) \
         + getPackageHelpText(t) \
         + getLocalizedVersionHelpText(t) \
         + getBridgesHelpText(t) \
         + getSupportText(t)

def getFAQText(t):
    return t.gettext(i18n.GETTOR_TEXT[54]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[63]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[55]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[64]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[56]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[57]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[63]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[58]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[64]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[59]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[63]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[60]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[64]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[61]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[47]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[48]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[49]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[50]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[51]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[52]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[53]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[63]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[62]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[64]) + "\n" \
             + t.gettext(i18n.GETTOR_TEXT[43]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[44]) + "\n\n" \
             + t.gettext(i18n.GETTOR_TEXT[45]) + "\n\n"

def getSupportText(t):
    return t.gettext(i18n.GETTOR_TEXT[26]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[27]) + "\n\n" 

def getSplitPackageText(t):
    return t.gettext(i18n.GETTOR_TEXT[36]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[37]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[19]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[20]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[21]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[22]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[23]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[24]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[25]) + "\n\n" 

def getUnpackingText(t):
    return t.gettext(i18n.GETTOR_TEXT[42]) + "\n" \
         + t.gettext(i18n.GETTOR_TEXT[43]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[44]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[45]) + "\n\n" \

def getVerifySignatureText(t):
    return t.gettext(i18n.GETTOR_TEXT[29]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[30]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[31]) + "\n\n"

def getInitialHelpMsg(t, config):
    """Build a help string containing all languages we know.
    """
    help_text = ""
    # Hello, dirty hack! Add "en", "fa", "zh_CN" hard-coded in the front
    # as long as Python won't let us order out dict
    t = i18n.getLang("en", config)
    help_text += getGeneralHelpText(t)
    help_text += "-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --\n\n"
    t = i18n.getLang("fa", config)
    help_text += getGeneralHelpText(t)
    help_text += "-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --\n\n"
    t = i18n.getLang("zh_CN", config)
    help_text += getGeneralHelpText(t)
    help_text += "-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --\n\n"
    for lang in config.SUPP_LANGS.keys():
        # Hack continued: Skip "en", "fa", "zh_CN" -- because we have those
        # already in
        if lang == "en" or lang == "fa" or lang == "zh_CN":
            continue       
        t = i18n.getLang(lang, config)
        help_text += getGeneralHelpText(t)
        help_text += "-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --\n\n"
    return help_text

def getPackageMsg(t):
    return getGreetingText(t) \
         + t.gettext(i18n.GETTOR_TEXT[28]) + "\n\n" \
         + getUnpackingText(t) \
         + getBridgesHelpText(t) \
         + getVerifySignatureText(t) \
         + getFAQText(t) \
         + getSupportText(t)

def getSplitPackageMsg(t):
    return getGreetingText(t) \
         + t.gettext(i18n.GETTOR_TEXT[28]) + "\n\n" \
         + getSplitPackageText(t) \
         + getUnpackingText(t) \
         + getBridgesHelpText(t) \
         + getFAQText(t) \
         + getSupportText(t)

def getDelayAlertMsg(t, packageInfo):
    return getGreetingText(t) \
         + t.gettext(i18n.GETTOR_TEXT[38] % packageInfo) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[39]) + "\n\n" \
         + getSupportText(t)

def getSorrySizeMsg(t, packageInfo):
    return getGreetingText(t) \
           + t.gettext(i18n.GETTOR_TEXT[65] % packageInfo) + "\n\n" \
           + getSupportText(t)

def getNoSplitAvailable(t):
    return getGreetingText(t) \
         + t.gettext(i18n.GETTOR_TEXT[1]) + "\n\n" \
         + t.gettext(i18n.GETTOR_TEXT[41]) + "\n\n" \
         + getSupportText(t)


class Response:
    def __init__(self, config, reqInfo):
        """Intialize the reply class. The most important values are passed in
           via the 'reqInfo' dict. 
        """
        self.config = config
        self.reqInfo = reqInfo

        # Delete sensitive data before dumping info
        reqInfoClean = copy.deepcopy(self.reqInfo)
        del reqInfoClean['user']
        logging.info(str(reqInfoClean))

        # Initialize locale subsystem
        self.t = i18n.getLang(self.reqInfo['locale'], config)

        # Init black & whitelists
        wlStateDir = os.path.join(self.config.BASEDIR, "wl")
        blStateDir = os.path.join(self.config.BASEDIR, "bl")
        self.wList = gettor.blacklist.BWList(wlStateDir, config.BLACKLIST_THRES)
        self.bList = gettor.blacklist.BWList(blStateDir, config.BLACKLIST_THRES)

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
            # Did the user request a split or normal package download?
            if self.reqInfo['split']:
                return self.sendSplitPackage()
            else:
                # Check if the user's allowed attachment size is okay.
                if self.attachmentSizeOk(self.reqInfo['package'], self.reqInfo['max_attach']):
                    return self.sendPackage()
                else:
                    return self.sendSorrySize()

    def attachmentSizeOk(self, package, max_attach):
        """Check if the user is allowed to receive a certain attachment size-wise.
        """
        if max_attach == 0:
           return True

        try:
            package_path = os.path.join(self.config.BASEDIR, "packages", package + ".z")
            package_size = os.path.getsize(package_path)
            if package_size <= max_attach:
                return True
        except OSError:
            log.error("Ugh, this is bad. package %s isnt available!" % package_path)

        return False

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
        normalized_addr = gettor.utils.normalizeAddress(self.reqInfo['user'])
        if self.wList.entryExists(normalized_addr, "general"):
            logging.info("Whitelisted user " + self.reqInfo['hashed_user'])
            return False
        # Now check general and specific blacklists, in that order
        if self.bList.entryExists(normalized_addr, "general"):
            logging.info("Blacklisted user " + self.reqInfo['hashed_user'])
            return True
        # Create a unique dir name for the requested routine
        self.bList.createSublist(fname)
        if self.bList.checkAndUpdate(normalized_addr, fname, True):
            logging.info("User %s is blacklisted for %s" \
                                   % (self.reqInfo['hashed_user'], fname))
            return True
        else:
            self.bList.createListEntry(normalized_addr, fname)
            return False

    def sendPackage(self):
        """ Send a message with an attachment to the user. The attachment is 
            chosen automatically from the selected self.reqInfo['package']
        """
        # Be a polite bot and send message that mail is on the way
        if self.config.DELAY_ALERT:
	    if not self.sendDelayAlert():
	        logging.error("Failed to sent delay alert.")

        pack = self.reqInfo['package']
        to = self.reqInfo['user']
        if self.isBlacklistedForMessageType("sendPackage"):
            # Don't send anything
            return False
        logging.info("Sending out %s." % (pack))
        f = os.path.join(self.config.BASEDIR, "packages", pack + ".z")
        txt = getPackageMsg(self.t)
        msg = self.makeMsg(txt, to, fileName=f)
        msg = self.addUserManual(msg, self.reqInfo['locale'])
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
        logging.info("Sending out %s."  % (pack))
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
        # Check if there's a split package for this available
        pack =  self.reqInfo['package']
        split = self.config.PACKAGES[pack][1]
        if split is not None and split == "unavailable":
            logging.error("User requested split package that isn't available")
            # Inform the user
            return self.sendTextEmail(getNoSplitAvailable(self.t))

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

        # Be a polite bot and send message that mail is on the way
        if self.config.DELAY_ALERT:
            if not self.sendDelayAlert(nFiles):
                logging.error("Failed to sent delay alert.")

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

    def sendDelayAlert(self, packageCount=1):
        """Send a polite delay notification. Add the number of packages that
           the user can expect to arrive.
        """
        if self.isBlacklistedForMessageType("sendDelayAlert"):
            # Don't send anything
            return False

        if packageCount > 1:
            packageInfo = "Package: %s [%d parts]" \
                           % (self.reqInfo['package'], packageCount)
        else:
            packageInfo = "Package: %s" % self.reqInfo['package']

        logging.info("Sending delay alert to %s" % self.reqInfo['hashed_user'])
        return self.sendTextEmail(getDelayAlertMsg(self.t, packageInfo))


    def sendSorrySize(self):
        """Send a polite note that the user's provider doesn't support the
           attachment size necessary for a given package.
        """
        if self.isBlacklistedForMessageType("sendSorrySize"):
            # Don't send anything
            return False

        logging.info("Sending sorry size email to %s" % self.reqInfo['hashed_user']) 
        return self.sendTextEmail(getSorrySizeMsg(self.t, self.reqInfo['package']))

    def sendHelp(self):
        """Send a help mail. This happens when a user sent us a request we 
           didn't really understand

           XXX: This routine is currently not used, since we send out the 
                longer MULTILANGHELP message instead.
        """
        if self.isBlacklistedForMessageType("sendHelp"):
            # Don't send anything
            return False
        logging.info("Sending out help message to %s" % self.reqInfo['hashed_user'])
        return self.sendTextEmail(getPackageHelpMsg(self.t))

    def sendPackageHelp(self):
        """Send a helpful message to the user interacting with us about
           how to select a proper package
        """
        if self.isBlacklistedForMessageType("sendPackageHelp"):
            # Don't send anything
            return False
        logging.info("Sending package help to %s" % self.reqInfo['hashed_user'])
        return self.sendTextEmail(getInitialHelpMsg(self.t, self.config))

    def sendTextEmail(self, text):
        """Generic text message sending routine.
        """
        message = self.makeMsg(text, self.reqInfo['user'])
        try:
            status = self.sendEmail(self.reqInfo['user'], message)
        except:
            logging.error("Could not send message to user %s" \
                                                % self.reqInfo['hashed_user'])
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

    def addUserManual(self, message, lang="en"):
        """Add the short user manual to an existing message.
        """
        docDir = os.path.join(self.config.BASEDIR, "doc")
        mName = "short-user-manual_" + lang + ".xhtml"
        docName = os.path.join(docDir, mName)
        if not os.access(docName, os.R_OK):
            # Fall back to english if a certain locale isn't 
            # available
            mName = "short-user-manual_en.xhtml"
            docName = os.path.join(docDir, mName)
        if os.access(docName, os.R_OK):
            filePart = MIMEBase("application", "xhtml")
            fp = open(docName, 'rb')
            filePart.set_payload(fp.read())
            fp.close()
            encoders.encode_base64(filePart)
            # Add file part
            filePart.add_header('Content-Disposition', 'attachment', filename=mName)
            message.attach(filePart)
        else:
            logging.error("Could not open manual file %d" % docName)

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
