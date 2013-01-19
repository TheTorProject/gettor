# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.
# -*- coding: utf-8 -*-

import os
import gettext

def getLang(lang, config):
    """Return the Translation instance for a given language. If no Translation
       instance is found, return the one for 'en'
    """
    localeDir = os.path.join(config.BASEDIR, 'share', 'i18n')
    fallback = config.DEFAULT_LOCALE
    return gettext.translation("gettor", localedir=localeDir,
                               languages=[lang], fallback=fallback)

def _(text):
    """This is necessary because strings are translated when they're imported.
       Otherwise this would make it impossible to switch languages more than 
       once
    """
    return text

GETTOR_TEXT = [
 # GETTOR_TEXT[0]
_("""Hello, This is the "GetTor" robot."""),
 # GETTOR_TEXT[1]
_("""Thank you for your request."""),
 # GETTOR_TEXT[2]
_("""Unfortunately, we won't answer you at this address. You should make
an account with GMAIL.COM, YAHOO.COM or YAHOO.CN and send the mail from
one of those."""),
 # GETTOR_TEXT[3]
_("""We only process requests from email services that support "DKIM",
which is an email feature that lets us verify that the address in the
"From" line is actually the one who sent the mail."""),
 # GETTOR_TEXT[4]
_("""(We apologize if you didn't ask for this mail. Since your email is from
a service that doesn't use DKIM, we're sending a short explanation,
and then we'll ignore this email address for the next day or so.)"""),
 # GETTOR_TEXT[5]
_("""If you have any questions or it doesn't work, you can contact a
human at this support email address: help@rt.torproject.org"""),
 # GETTOR_TEXT[6]
_("""I will mail you a Tor package, if you tell me which one you want.
Please select one of the following package names:

    windows
    macos-i386
    macos-ppc
    linux-i386
    linux-x86_64
    obfs-windows
    obfs-macos-i386
    obfs-macos-x86_64
    obfs-linux-i386
    obfs-linux-x86_64
    source"""),
 # GETTOR_TEXT[7]
_("""Please reply to this mail, and tell me a single package name anywhere 
in the body of your email."""),
 # GETTOR_TEXT[8]
_("""OBTAINING LOCALIZED VERSIONS OF TOR
==================================="""),
 # GETTOR_TEXT[9]
_("""To get a version of Tor translated into your language, specify the
language you want in the address you send the mail to:

    gettor+fa@torproject.org"""),
 # GETTOR_TEXT[10]
_("""This example will give you the requested package in a localized
version for Farsi (Persian). Check below for a list of supported language
codes. """),
 # GETTOR_TEXT[11]
_(""" List of supported locales:"""),
 # GETTOR_TEXT[12]
_("""Here is a list of all available languages:"""),
 # GETTOR_TEXT[13]
_("""    gettor+ar@torproject.org:     Arabic
    gettor+de@torproject.org:     German
    gettor+en@torproject.org:     English
    gettor+es@torproject.org:     Spanish
    gettor+fa@torproject.org:     Farsi (Iran)
    gettor+fr@torproject.org:     French
    gettor+it@torproject.org:     Italian
    gettor+nl@torproject.org:     Dutch
    gettor+pl@torproject.org:     Polish
    gettor+ru@torproject.org:     Russian
    gettor+zh@torproject.org:     Chinese"""),
 # GETTOR_TEXT[14]
_("""If you select no language, you will receive the English version."""),
 # GETTOR_TEXT[15]
_("""SMALLER SIZED PACKAGES
======================"""),
 # GETTOR_TEXT[16]
_("""If your bandwith is low or your provider doesn't allow you to
receive large attachments in your email, GetTor can send you several
small packages instead of one big one."""),
 # GETTOR_TEXT[17]
_("""Simply include the keyword 'split' in a new line on its own (this part
is important!) like so: 
        
    windows
    split"""),
 # GETTOR_TEXT[18]
_("""Sending this text in an email to GetTor will cause it to send you 
the Tor Browser Bundle in a number of 1,4MB attachments."""),
 # GETTOR_TEXT[19]
_("""After having received all parts, you need to re-assemble them to 
one package again. This is done as follows:"""),
 # GETTOR_TEXT[20]
_("""1.) Save all received attachments into one folder on your disk."""),
 # GETTOR_TEXT[21]
_("""2.) Unzip all files ending in ".z". If you saved all attachments to
a fresh folder before, simply unzip all files in that folder. If you don't
know how to unzip the .z files, please see the UNPACKING THE FILES section."""),
 # GETTOR_TEXT[22]
_("""3.) Verify all files as described in the mail you received with 
each package. (gpg --verify)"""),
 # GETTOR_TEXT[23]
_("""4.) Now unpack the multi-volume archive into one file by double-
clicking the file ending in "..split.part01.exe". This should start the 
process automatically."""),
 # GETTOR_TEXT[24]
_("""5.) After unpacking is finished, you should find a newly created 
".exe" file in your destination folder. Simply doubleclick
that and Tor Browser Bundle should start within a few seconds."""),
 # GETTOR_TEXT[25]
_("""6.) That's it. You're done. Thanks for using Tor and have fun!"""),
 # GETTOR_TEXT[26]
_("""SUPPORT
======="""),
 # GETTOR_TEXT[27]
_("""If you have any questions or it doesn't work, you can contact a
human at this support email address: help@rt.torproject.org"""),
 # GETTOR_TEXT[28]
_("""Here's your requested software as a zip file. Please unzip the
package and verify the signature."""),
 # GETTOR_TEXT[29]
_("""VERIFY SIGNATURE
================
If your computer has GnuPG installed, use the gpg commandline 
tool as follows after unpacking the zip file:

    gpg --verify tor-browser-1.3.24_en-US.exe.asc tor-browser-1.3.24_en-US.exe"""),
 # GETTOR_TEXT[30]
_("""The output should look somewhat like this:

    gpg: Good signature from 'Erinn Clark <...>'"""),
 # GETTOR_TEXT[31]
_("""If you're not familiar with commandline tools, try looking for
a graphical user interface for GnuPG on this website:

    http://www.gnupg.org/related_software/frontends.html"""),
 # GETTOR_TEXT[32]
_("""BLOCKED ACCESS / CENSORSHIP
==========================="""),
 # GETTOR_TEXT[33]
_("""If your Internet connection blocks access to the Tor network, you
may need a bridge relay. Bridge relays (or "bridges" for short)
are Tor relays that aren't listed in the main directory. Since there
is no complete public list of them, even if your ISP is filtering
connections to all the known Tor relays, they probably won't be able
to block all the bridges."""),
 # GETTOR_TEXT[34]
_("""You can acquire a bridge by sending an email that contains "get bridges"
in the body of the email to the following email address:

    bridges@torproject.org"""),
 # GETTOR_TEXT[35]
_("""It is also possible to fetch bridges with a web browser at the following
url: https://bridges.torproject.org/"""),
 # GETTOR_TEXT[36]
_("""Another censorship circumvention tool you can request from GetTor is
the Tor Obfsproxy Browser Bundle. Please read the package descriptions for
which package you should request to receive this."""),
 # GETTOR_TEXT[37]
_("""IMPORTANT NOTE:
Since this is part of a split-file request, you need to wait for
all split files to be received by you before you can save them all
into the same directory and unpack them by double-clicking the
first file."""),
 # GETTOR_TEXT[38]
_("""Packages might arrive out of order! Please make sure you received
all packages before you attempt to unpack them!"""),
 # GETTOR_TEXT[39]
_("""It was successfully understood. Your request is currently being processed.
Your package (%s) should arrive within the next ten minutes."""),
 # GETTOR_TEXT[40]
_("""If it doesn't arrive, the package might be too big for your mail provider.
Try resending the mail from a GMAIL.COM, YAHOO.CN or YAHOO.COM account."""),
 # GETTOR_TEXT[41]
_("""Unfortunately we are currently experiencing problems and we can't fulfill
your request right now. Please be patient as we try to resolve this issue."""),
 # GETTOR_TEXT[42]
_("""Unfortunately there is no split package available for the package you
requested. Please send us another package name or request the same package 
again, but remove the 'split' keyword. In that case we'll send you the whole 
package. Make sure this is what you want."""),
 # GETTOR_TEXT[43]
_("""UNPACKING THE FILES
==================="""),
 # GETTOR_TEXT[44]
_("""The easiest way to unpack the files you received is to install 7-Zip,
a free file compression/uncompression tool. If it isn't installed on
your computer yet, you can download it here:

    http://www.7-zip.org/"""),
 # GETTOR_TEXT[45]
_("""When 7-Zip is installed, you can open the .z archive you received from
us by double-clicking on it."""),
 # GETTOR_TEXT[46]
_("""An alternative way to get the .z files extraced is to rename them to
.zip. For example, if you recevied a file called "windows.z", rename it to 
"windows.zip". You should then be able to extract the archive with common 
file archiver programs that probably are already installed on your computer."""),
 # GETTOR_TEXT[47]
_("""Please reply to this mail, and tell me a single package name anywhere
in your reply. Here's a short explanation of what these packages are:"""),
 # GETTOR_TEXT[48]
_("""windows:
The Tor Browser Bundle package for Windows operating systems. If you're 
running some version of Windows, like Windows XP, Windows Vista or 
Windows 7, this is the package you should get."""),
 # GETTOR_TEXT[49]
_("""macos-i386:
The Tor Browser Bundle package for OS X, Intel CPU architecture. In 
general, newer Mac hardware will require you to use this package."""),
 # GETTOR_TEXT[50]
_("""macos-ppc:
This is an older installer (the "Vidalia bundle") for older Macs running
OS X on PowerPC CPUs. Note that this package will be deprecated soon."""),
 # GETTOR_TEXT[51]
_("""linux-i386:
The Tor Browser Bundle package for Linux, 32bit versions."""),
 # GETTOR_TEXT[52]
_("""Note that this package is rather large and needs your email provider to 
allow for attachments of about 30MB in size."""),
 # GETTOR_TEXT[53]
_("""linux-x86_64:
The Tor Browser Bundle package for Linux, 64bit versions."""),
 # GETTOR_TEXT[54]
_("""obfs-windows:
The Tor Obfsproxy Browser Bundle for Windows operating systems. If you need
strong censorship circumvention and you are running some version of the 
Windows, like Windows XP, Windows Vista or Windows 7, this is the package
you should get."""),
 # GETTOR_TEXT[55]
_("""obfs-macos-i386:
The Tor Obfsproxy Browser Bundle package for OS X, 32bit Intel CPU 
architecture."""),
 # GETTOR_TEXT[56]
_("""obfs-macos-x86_64:
The Tor Obfsproxy Browser Bundle package for OS X, 64bit Intel CPU 
architecture."""),
 # GETTOR_TEXT[57]
_("""obfs-linux-i386:
The Tor Obfsproxy Browser Bundle package for Linux, 32bit Intel CPU 
architecture."""),
 # GETTOR_TEXT[58]
_("""obfs-linux-x86_64:
The Tor Obfsproxy Browser Bundle package for Linux, 64bit Intel CPU 
architecture."""),
 # GETTOR_TEXT[59]
_("""source:
The Tor source code, for experts. Most users do not want this package."""),
 # GETTOR_TEXT[60]
_("""FREQUENTLY ASKED QUESTIONS
=========================="""),
 # GETTOR_TEXT[61]
_("""What is Tor?"""),
 # GETTOR_TEXT[62]
_("""The name "Tor" can refer to several different components."""),
 # GETTOR_TEXT[63]
_("""The Tor software is a program you can run on your computer that helps 
keep you safe on the Internet. Tor protects you by bouncing your 
communications around a distributed network of relays run by volunteers 
all around the world: it prevents somebody watching your Internet connection 
from learning what sites you visit, and it prevents the sites you visit from 
learning your physical location. This set of volunteer relays is called the 
Tor network. You can read more about how Tor works here:

    https://www.torproject.org/about/overview.html.en"""),
 # GETTOR_TEXT[64]
_("""What is the Tor Browser Bundle?"""),
 # GETTOR_TEXT[65]
_("""The Browser Bundle (TBB) is the package we recommend to most users. 
The bundle comes with everything you need to safely browse the Internet.
Just extract it and run."""),
 # GETTOR_TEXT[66]
_("""What package should I request?"""),
 # GETTOR_TEXT[67]
_("""This depends on the operating system you use. For instance, if your
operating system is Microsoft Windows, you should request "windows". Here
is a short explanation of all packages to request and what operating 
systems there are suitable for:"""),
 # GETTOR_TEXT[68]
_("""How do I extract the file(s) you sent me?"""),
 # GETTOR_TEXT[69]
_("""QUESTION:"""),
 # GETTOR_TEXT[70]
_("""ANSWER:"""),
 # GETTOR_TEXT[71]
_("""Sorry, but the package you requested (%s) is too large for your 
provider to accept as an attachment. Try using another provider that allows 
for larger email attachments. Or try one of the following mirrors:

  https://www.oignon.net/dist/torbrowser/
  https://tor.beme-it.de/dist/torbrowser/
  https://www.torservers.net/mirrors/torproject.org/dist/torbrowser/""")
]
