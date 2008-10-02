#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
"""
 gettor_config.py - Parse configuration file for gettor

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

 This library implements all of the email replying features needed for gettor. 
"""

import smtplib
import MimeWriter
import StringIO
import base64
import gettext


class gettorResponse():

    def __init__(self, mailLang="en", logLang="en"):
        self.mailLang = mailLang
        self.logLang = logLang

    def setLang(self, language):
        # XXX: Sorta hack, have nothing better on my mind right now
        # On every entry to a translation-needing function, call this with lang=maillang
        # On every exit of a translation-needing function, call this with lang=loglang
        # :-/
        trans = gettext.translation("gettor", "/usr/share/locale", [language])
        trans.install()

    def sendHelp(self, source, destination):
        """ Send a helpful message to the user interacting with us """
        self.setLang(self.mailLang)
        message = _("""
    Hello! This is the "get tor" robot.

    Unfortunately, we won't answer you at this address. We only process
    requests from email services that support "DKIM", which is an email
    feature that lets us verify that the address in the "From" line is
    actually the one who sent the mail.

    Gmail and Yahoo Mail both use DKIM. You will have better luck sending
    us mail from one of those.

    (We apologize if you didn't ask for this mail. Since your email is from
    a service that doesn't use DKIM, we're sending a short explanation,
    and then we'll ignore this email address for the next day or so.
        """)
        help = self.constructMessage(message, source, destination)
        try:
            status = self.sendMessage(help, source, destination)
        except:
            status = False
        self.setLang(self.logLang)

        return status

    def sendPackageHelp(self, packageList, source, destination):
        """ Send a helpful message to the user interacting with us """
        self.setLang(self.mailLang)
        message = [_("Hello, I'm a robot. ")]
        message.append(_("Your request was not understood. Please select one of the following package names:\n"))

        for key in packageList.keys():
            message.append(key + "\n")
        message.append(_("Please send me another email. It only needs a single package name anywhere in the body of your email.\n"))
        help = self.constructMessage(''.join(message), source, destination)
        try:
            status = self.sendMessage(help, source, destination)
        except:
            status = False
        self.setLang(self.logLang)

        return status

    def sendPackage(self, source, destination, filelist):
        """ Send a message with an attachment to the user interacting with us """
        self.setLang(self.mailLang)
        message = _("""
    Here's your requested software as a zip file. Please unzip the 
    package and verify the signature.
        """)
        package = self.constructMessage(source, destination, filelist)
        try:
            status = self.sendMessage(package, source, destination)
        except:
            status = False
        self.setLang(self.mailLang)

        return status

    def constructMessage(self, messageText, ourAddress, recipient, fileList=None, 
                         fileName="requested-files.z"):
        """ Construct a multi-part mime message, including only the first part
        with plaintext."""

        message = StringIO.StringIO()
        mime = MimeWriter.MimeWriter(message)
        mime.addheader('MIME-Version', '1.0')
        mime.addheader('Subject', _('Re: Your "get tor" request'))
        mime.addheader('To', recipient)
        mime.addheader('From', ourAddress)
        mime.startmultipartbody('mixed')

        firstPart = mime.nextpart()
        emailBody = firstPart.startbody('text/plain')
        emailBody.write(messageText)

        # Add a file if we have one
        if fileList:
            # XXX TODO: Iterate over each file eventually
            filePart = mime.nextpart()
            filePart.addheader('Content-Transfer-Encoding', 'base64')
            emailBody = filePart.startbody('application/zip; name=%s' % fileName)
            base64.encode(open(fileList, 'rb'), emailBody)

        # Now end the mime messsage
        mime.lastpart()
        return message

    def sendMessage(self, message, src, dst, smtpserver="localhost:25"):
        try:
            smtp = smtplib.SMTP(smtpserver)
            smtp.sendmail(src, dst, message.getvalue())
            smtp.quit()
            status = True
        except:
            return False

        return status

if __name__ == "__main__" :
    print "This is the response handling code. You probably do not want to call it by hand."

