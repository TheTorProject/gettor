#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
"""

 gettor.py by Jacob Appelbaum <jacob@appelbaum.net>,
              Christian Fromme <kaner@strace.org>
 This program will hand out Tor via email to supported systems.
 This program is Free Software, see LICENSE for details.

 It is intended to be used in a .forward file as part of a pipe like so:

     cat <<'EOF'> .forward
     |/usr/local/bin/gettor.py
     EOF

 You should have a dist/current/ mirror in a directory that gettor can read.
 Such a mirror can be created like so:

     cd /usr/local/
     rsync -av rsync://rsync.torproject.org/tor/dist/current tor-dist-current/

 You can keep it updated with a cronjob like so:

     MirrorDir=/usr/local/tor-dist-current/
     0 3 * * * rsync -a rsync://rsync.torproject.org/tor/dist/current/ $MirrorDir
 
 You should ensure that for each file and signature pair you wish to 
 distribute, you have created a zip file containing both.

 While this program isn't written in a threaded manner per se, it is designed to function 
 as if it will be called as a pipe many times at once. There is a slight 
 desynchronization with blacklist entry checking and may result in false 
 negatives. This isn't perfect but it is designed to be lightweight. It could 
 be fixed easily with a shared locking system but this isn't implemented yet.

 To clean out the blacklist on a daily basis, install the following cronjob:

     # m h  dom mon dow   command
     1 1 * * * /bin/rm -rf /var/lib/gettor/bl/*

 You'll probably want a directory structure like this owned by uid/gid 'gettor':
    /var/lib/gettor/{bl,pkg}

"""

__program__ = 'gettor.py'
__version__ = '20080914.01'
__url__ = 'https://tor-svn.freehaven.net/svn/tor/trunk/contrib/gettor/'
__author__ = 'Jacob Appelbaum <jacob@appelbaum.net>, Christian Fromme <kaner@strace.org>'
__copyright__ = 'Copyright (c) 2008, Jacob Appelbaum, Christian Fromme'
__license__ = 'See LICENSE for licensing information'

try:
    from future import antigravity
except ImportError:
    antigravity = None

import sys
import os
import subprocess
import gettext
import gettor_blacklist
import gettor_requests
import gettor_responses
import gettor_log
import gettor_config
import gettor_opt
import gettor_packages


# Switch language to 'newlocale'. Return default if language is not supported.
# XXX: There should be a more elegant way to switch languages during runtime.
def switchLocale(newlocale):
    trans = gettext.translation("gettor", "/usr/share/locale", [newlocale], fallback=True)
    trans.install()

def runTests():
    # XXX 
    return True

def installCron(rsync):
    # XXX: Check if cron is installed and understands our syntax?
    echoCmd = ['echo', '3 2 * * * ' + rsync]
    cronCmd = ['crontab', '-']
    echoProc = subprocess.Popen(echoCmd, stdout=subprocess.PIPE)
    cronProc = subprocess.Popen(cronCmd, stdin=echoProc.stdout)
    cronProc.communicate()[0]
    return cronProc.returncode

def processMail(conf, log, logLang, packageList):
    if len(packageList) < 1:
        log.error(_("Sorry, your package list is unusable."))
        return False
    # Receive mail
    rmail = gettor_requests.requestMail(packageList)
    rawMessage = rmail.getRawMessage()
    if not rawMessage:
        log.error(_("No raw message. Something went wrong."))
        return False
    parsedMessage = rmail.getParsedMessage()
    if not parsedMessage:
        log.error(_("No parsed message. Dropping message."))
        return False
    # XXX: We should add a blacklist check here so that for exmaple ReplyTo can't be our own 
    #      address (DoS) (in case we have DKIM) 
    replyTo = rmail.getReplyTo()
    if not replyTo:
        log.error(_("No help dispatched. Invalid reply address for user."))
        return False
    replyLang = rmail.getLocale()
    if not replyLang:
        replyLang = logLang
    # Initialize response
    srcEmail = conf.getSrcEmail()
    resp = gettor_responses.gettorResponse(replyLang, logLang)
    signature = rmail.hasVerifiedSignature()
    log.info(_("Signature is: %s") % str(signature))
    if not signature:
        # Check to see if we've helped them to understand that they need DKIM
        # in the past
        previouslyHelped = gettor_blacklist.blackList(replyTo)
        if previouslyHelped:
            log.info(_("Unsigned messaged to gettor by blacklisted user dropped."))
            return False
        else:
            # Reply with some help and bail out
            gettor_blacklist.blackList(replyTo, True)
            resp.sendHelp(srcEmail, replyTo)
            log.info(_("Unsigned messaged to gettor. We issued some help."))
            return True
    else:
        log.info(_("Signed messaged to gettor."))
        package = rmail.getPackage()
        if package != None:
            log.info(_("Package: %s selected.") % str(package))
            resp.sendPackage(srcEmail, replyTo, packageList[package])  
        else:
            resp.sendPackageHelp(packageList, srcEmail, replyTo)
            log.info(_("We issued some help about proper email formatting."))

    return True

if __name__ == "__main__":
    # Parse command line, setup config, logging and language
    options, arguments = gettor_opt.parseOpts()
    conf = gettor_config.gettorConf(options.configfile)
    logger  = gettor_log.gettorLogger()
    log = logger.getLogger()
    logLang = conf.getLocale()
    switchLocale(logLang)
    distDir = conf.getDistDir()
    if not os.path.isdir(distDir):
        log.info(_("Sorry, %s is not a directory.") % distDir)
        exit(1)

    packs = gettor_packages.gettorPackages(options.mirror, conf)
    # Action
    if options.fetchpackages:
        if packs.syncWithMirror() != 0:
            log.error(_("Syncing Tor packages failed."))
            exit(1)
        else:
            log.info(_("Syncing Tor packages done."))
            exit(0)
    if options.preppackages:
        if not packs.buildPackages():
            log.error(_("Building packages failed."))
            exit(1)
        else:
            log.info(_("Building packages done."))
            exit(0)
    if options.runtests:
        if not runTests():
            log.error(_("Tests failed."))
            exit(1)
        else:
            log.info(_("Tests passed."))
            exit(0)
    if options.installcron:
        if installCron(packs.getCommandToStr()) != 0:
            log.error(_("Installing cron failed"))
            exit(1)
        else:
            log.info(_("Installing cron done."))
            exit(0)
    
    # Main loop
    if not processMail(conf, log, logLang, packs.getPackageList()):
        log.error(_("Processing mail failed."))
        exit(1)

    exit(0)
