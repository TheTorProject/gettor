# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

import re
import logging 

def doFilter(reqInfo):
    """DOCDOC
    """
    reqInfo['package'] = doPackageHacks(reqInfo['package'], reqInfo['locale']) 
    reqInfo['valid'] = checkAddressHack(reqInfo['user'])

    return reqInfo

def doPackageHacks(packageName, locale):
    """If someone wants one of the localizable packages, add language 
       suffix. This isn't nice because we're hard-coding package names here
       Attention: This needs to correspond to the  packages in packages.py
    """
    # If someone sent a request for a "tor-browser-bundle" (whatever that is ;)
    # we reply with a "windows" package
    if packageName == "tor-browser-bundle":
       packageName = "windows"
    if packageName == "windows" \
           or packageName == "linux-i386" \
           or packageName == "linux-x86_64" \
           or packageName == "osx-i386":
        # "windows" => "windows_de"
        packageName += "_" + locale

    return packageName

def checkAddressHack(userAddress):
    """This makes it possible to add hardcoded blacklist entries *ugh*
       XXX: This should merge somehow with the GetTor blacklisting
            mechanism at some point
    """
    if re.compile(".*@.*torproject.org.*").match(userAddress):
        return False
        
    # Make sure we drop bounce mails
    if userAddress == "<>":
        logging.debug("We've received a bounce")
        return False

    # User address looks good.
    return True

def doToAddressHack(toAddress):
    """Large HACK alert: If we received an email to the address
       'torfarsi1@torproject.org', we understand it to reply in Farsi to that
       email.
    """
    if re.compile(".*torfarsi.*@torproject.org.*").match(toAddress):
        return "<gettor+fa@torproject.org>"
    else:
        return toAddress

