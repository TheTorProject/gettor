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

import gettor.gtlog

__all__ = ["gettorResponse"]

log = gettor.gtlog.getLogger()

class gettorResponse:

    def __init__(self, config, mailLang="en", logLang="en"):
        self.mailLang = mailLang
        self.logLang = logLang
        self.config = config

    def setLang(self, language):
        # XXX: Sorta hack, have nothing better on my mind right now
        # On every entry to a translation-needing function, call this with 
        # lang=maillang
        # On every exit of a translation-needing function, call this with 
        # lang=loglang
        # :-/
        if self.config:
            trans = gettext.translation("gettor", self.config.getLocaleDir(), [language])
            trans.install()

    def sendHelp(self, source, destination):
        """ Send a helpful message to the user interacting with us """
        self.setLang(self.mailLang)
        message = _("""
    Hello! This is the "gettor" robot.

    Unfortunately, we won't answer you at this address. We only process
    requests from email services that support "DKIM", which is an email
    feature that lets us verify that the address in the "From" line is
    actually the one who sent the mail.

    Gmail.com uses DKIM: you will have better luck sending us mail from
    your gmail account.

    (We apologize if you didn't ask for this mail. Since your email is from
    a service that doesn't use DKIM, we're sending a short explanation,
    and then we'll ignore this email address for the next day or so.)

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

    Please note that currently, we can't process HTML emails. You will need
    to send plain text.
        """)
        help = self.constructMessage(message, source, destination)
        try:
            status = self.sendMessage(help, source, destination)
        except:
            log.error(_("Could not send help message to user"))
            status = False
        self.setLang(self.logLang)

        return status

    def sendPackageHelp(self, packageList, source, destination):
        """ Send a helpful message to the user interacting with us """
        self.setLang(self.mailLang)
        message = _("""
    Hello, This is the "gettor" robot.

    I am sorry, but your request was not understood. Please select one of the 
    following package names:

    """ + "".join([ "\t%s\n" % key for key in packageList.keys()]) + """
    Please send another mail to gettor@torproject.org. It only needs a
    single package name anywhere in the body of your email.

    Please note that currently, we can't process HTML emails. You will need to
    send plain text.

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

        """)
        help = self.constructMessage(message, source, destination)
        try:
            status = self.sendMessage(help, source, destination)
        except:
            status = False
            log.error(_("Could not send package help message to user"))
        self.setLang(self.logLang)

        return status

    def sendGenericMessage(self, source, destination, message):
        """ Send a helpful message of some sort """
        self.setLang(self.mailLang)
        help = self.constructMessage(message, source, destination)
        try:
            status = self.sendMessage(help, source, destination)
        except:
            log.error(_("Could not send generic help message to user"))
            status = False
        self.setLang(self.logLang)
        return status

    def sendPackage(self, source, destination, filename):
        """ Send a message with an attachment to the user interacting with us """
        self.setLang(self.mailLang)
        message = _("""
    Hello! This is the "gettor" robot.

    Here's your requested software as a zip file. Please unzip the 
    package and verify the signature.

    Hint: If your computer has GnuPG installed, use the gpg
    commandline tool as follows after unpacking the zip file:

       gpg --verify <packagename>.asc <packagename>

    The output should look somewhat like this:

       gpg: Good signature from "Roger Dingledine <arma@mit.edu>"

    If you're not familiar with commandline tools, try looking for
    a graphical user interface for GnuPG on this website:

       http://www.gnupg.org/related_software/frontends.html

    If your Internet connection blocks access to the Tor network, please
    consider using a bridge relay. Bridge relays (or "bridges" for short)
    are Tor relays that aren't listed in the main directory. Since there
    is no complete public list of them, even if your ISP is filtering
    connections to all the known Tor relays, they probably won't be able
    to block all the bridges.

    You can acquire a bridge by sending an email that contains "get bridges"
    in the body of the email to the following email address:
    bridges@torproject.org

    It is also possible to fetch bridges with a web browser at the following
    url: https://bridges.torproject.org/

    If you have any questions or it doesn't work, you can contact a
    human at this support email address: tor-assistants@torproject.org

        """)
        package = self.constructMessage(message, source, destination, filename)
        try:
            status = self.sendMessage(package, source, destination)
        except:
            log.error(_("Could not send package to user"))
            status = False
        self.setLang(self.mailLang)

        return status

    def constructMessage(self, messageText, ourAddress, recipient, fileName=None):
        """ Construct a multi-part mime message, including only the first part
        with plaintext."""

        message = StringIO.StringIO()
        mime = MimeWriter.MimeWriter(message)
        mime.addheader('MIME-Version', '1.0')
        mime.addheader('Subject', _('Re: Your "gettor" request'))
        mime.addheader('To', recipient)
        mime.addheader('From', ourAddress)
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

    def sendMessage(self, message, src, dst, smtpserver="localhost:25"):
        try:
            smtp = smtplib.SMTP(smtpserver)
            smtp.sendmail(src, dst, message.getvalue())
            smtp.quit()
            status = True
        except smtplib.SMTPAuthenticationError:
            log.error(_("SMTP authentication error"))
            return False
        except smtplib.SMTPHeloError:
            log.error(_("SMTP HELO error"))
            return False
        except smtplib.SMTPConnectError:
            log.error(_("SMTP connection error"))
            return False
        except smtplib.SMTPDataError:
            log.error(_("SMTP data error"))
            return False
        except smtplib.SMTPRecipientsRefused:
            log.error(_("SMTP refused to send to recipients"))
            return False
        except smtplib.SMTPSenderRefused:
            log.error(_("SMTP sender address refused"))
            return False
        except smtplib.SMTPResponseException:
            log.error(_("SMTP response exception received"))
            return False
        except smtplib.SMTPServerDisconnected:
            log.error(_("SMTP server disconnect exception received"))
            return False
        except smtplib.SMTPException:
            log.error(_("General SMTP error caught"))
            return False
        except:
            log.error(_("Unknown SMTP error while trying to send via local MTA"))
            return False

        return status

if __name__ == "__main__" :
    print "This is the response handling code. You probably do not want to call it by hand."

