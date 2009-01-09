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

# Global logger
log = None

# Switch language to 'newlocale'. Return default if language is not supported.
def switchLocale(newlocale, localedir):
    trans = gettext.translation("gettor", 
                                localedir,
                                [newlocale], 
                                fallback=True)
    trans.install()

def runTests():
    # XXX: Implement me
    return True

def installMo(poFile, targetDir):
    global log
    args = os.getcwd() + "/" + poFile + " -o " + targetDir + "/gettor.mo"
    try:
        ret = subprocess.call("msgfmt" + " " + args, shell=True)
        if ret < 0:
            log.error("Error in msgfmt execution: %s" % ret)
            return False
    except OSError, e:
        log.erro("Comilation failed: " % e)
        return False
    return True

def installTrans(config, localeSrcdir):
    global log
    hasDirs = None

    if config is None:
        log.error("Bad arg.")
        return False
    if not os.path.isdir(localeSrcdir):
        log.error("Not a directory: " % localeSrcdir)
        return False
    localeDir = config.getLocaleDir()
    if not os.path.isdir(localeDir):
        log.error("Sorry, %s is not a directory." % distDir)
        return False

    for root, dirs, files in os.walk(localeSrcdir):
        # Python lacks 'depth' featue for os.walk()
        if root != localeSrcdir:
            continue
        for dir in dirs:
            hasDirs = True
            if dir.startswith("."):
                continue
            try:
                poFile = os.path.join(root, dir) + "/gettor_" + dir + ".po"
                # Construct target dir
                targetDir = localeDir + "/" + dir + "/LC_MESSAGES"
                if os.path.isdir(targetDir):
                    if installMo(poFile, targetDir) == False:
                        log.error("Installing .mo files failed.")
                        return False
                else:
                    log.error("Not a directory: " % targetDir)
                    return False
            except Exception, e:
                log.error("Error accessing translation files: " % e)
                return False
    if hasDirs is None:
        log.errpr("Empty locale dir: " % localeSrcdir)
        return False

    return True

def installCron():
    # XXX: Check if cron is installed and understands our syntax?
    currentCronTab = getCurrentCrontab()
    gettorPath = os.getcwd() + "/" + os.path.basename(sys.argv[0])
    gettorArgs = " --clear-blacklist --fetch-packages --prep-packages"
    newCronTab = currentCronTab + '\n' + '3 2 * * * ' + gettorPath + gettorArgs
    echoCmd = ['echo', newCronTab ]
    cronCmd = ['crontab', '-']
    echoProc = subprocess.Popen(echoCmd, stdout=subprocess.PIPE)
    cronProc = subprocess.Popen(cronCmd, stdin=echoProc.stdout)
    cronProc.communicate()[0]
    return cronProc.returncode

def getCurrentCrontab():
    # This returns our current crontab
    savedTab = "# This crontab has been tampered with by gettor.py\n"
    currentTab = os.popen("crontab -l")
    for line in currentTab:
        savedTab += line
    return savedTab

def processMail(conf, logLang, packageList, blackList, whiteList):
    global log

    if packageList is None or len(packageList) < 1:
        log.error(_("Sorry, your package list is unusable."))
        log.error(_("Try running with --fetch-packages --prep-packages."))
        return False

    # Receive mail from stdin
    rmail = gettor_requests.requestMail(packageList)
    rawMessage = rmail.getRawMessage()
    if not rawMessage:
        log.error(_("No raw message. Something went wrong."))
        return False
    parsedMessage = rmail.getParsedMessage()
    if not parsedMessage:
        log.error(_("No parsed message. Dropping message."))
        return False
    replyTo = rmail.getReplyTo()
    if not replyTo:
        log.error(_("No help dispatched. Invalid reply address for user."))
        return False
    replyLang = rmail.getLocale()
    if not replyLang:
        replyLang = logLang

    # Initialize response
    srcEmail = conf.getSrcEmail()
    # Bail out if someone tries to be funny
    if (srcEmail == replyTo):
        log.error(_("Won't send myself emails."))
        return False

    resp = gettor_responses.gettorResponse(conf, replyLang, logLang)
    signature = rmail.hasVerifiedSignature()
    log.info(_("Signature is: %s") % str(signature))
    # Addresses from whitelist can pass without DKIM signature
    if not signature and not whiteList.lookupListEntry(replyTo):
        # Check to see if we've helped them to understand that they need DKIM
        # in the past
        previouslyHelped = blackList.lookupListEntry(replyTo)
        if previouslyHelped:
            log.info(_("Unsigned messaged to gettor by blacklisted user dropped."))
            return False
        else:
            # Reply with some help and bail out
            blackList.createListEntry(replyTo)
            resp.sendHelp(srcEmail, replyTo)
            log.info(_("Unsigned messaged to gettor. We issued some help."))
            return True
    else:
        log.info(_("Good message to gettor."))
        package = rmail.getPackage()
        if package != None:
            log.info(_("Package: %s selected.") % str(package))
            resp.sendPackage(srcEmail, replyTo, packageList[package])  
        else:
            resp.sendPackageHelp(packageList, srcEmail, replyTo)
            log.info(_("We issued some help about proper email formatting."))

    return True

def main():
    global log
    success = None

    # Parse command line, setup config, logging and language
    options, arguments = gettor_opt.parseOpts()
    conf = gettor_config.gettorConf(options.configfile)
    gettor_log.initialize()
    log = gettor_log.getLogger()

    # Setup locale
    logLang = conf.getLocale()
    localeDir = conf.getLocaleDir()
    # We need to do this first
    if options.insttrans:
        if installTrans(conf, options.i18ndir):
            log.info("Installing translation files done.")
            success = True
        else:
            log.error("Installing translation files failed.")
            return False
    # Just check for the english .mo file, because that's the fallback
    englishMoFile = localeDir + "/en/LC_MESSAGES/gettor.mo"
    if not os.path.isfile(englishMoFile):
        log.error("Sorry, %s is not a file we can access." % englishMoFile)
        return False
    switchLocale(logLang, localeDir)

    distDir = conf.getDistDir()
    if not os.path.isdir(distDir):
        log.error(_("Sorry, %s is not a directory.") % distDir)
        return False
    try:
        packs = gettor_packages.gettorPackages(options.mirror, conf)
    except IOError:
        log.error(_("Error initiating package list."))
        return False
    try:
        whiteList = gettor_blacklist.BWList(conf.getWlStateDir())
        blackList = gettor_blacklist.BWList(conf.getBlStateDir())
    except IOError, e:
        log.error(_("White/Black list error: %s") % e)
        return False

    if options.fetchpackages:
        if packs.syncWithMirror() != 0:
            log.error(_("Syncing Tor packages failed."))
            return False
        else:
            log.info(_("Syncing Tor packages done."))
            success = True
    if options.preppackages:
        if not packs.buildPackages():
            log.error(_("Building packages failed."))
            return False
        else:
            log.info(_("Building packages done."))
            success = True
    if options.runtests:
        if not runTests():
            log.error(_("Tests failed."))
            return False
        else:
            log.info(_("Tests passed."))
            success = True
    if options.installcron:
        if installCron() != 0:
            log.error(_("Installing cron failed"))
            return False
        else:
            log.info(_("Installing cron done."))
            success = True
    if options.whitelist:
        if not whiteList.createListEntry(options.whitelist):
            log.error(_("Creating whitelist entry failed."))
            return False
        else:
            log.info(_("Creating whitelist entry ok."))
            success = True
    if options.blacklist:
        if not blackList.createListEntry(options.blacklist):
            log.error(_("Creating blacklist entry failed."))
            return False
        else:
            log.info(_("Creating blacklist entry ok."))
            success = True
    if options.lookup:
        if whiteList.lookupListEntry(options.lookup):
            log.info(_("Present in whitelist."))
            success = True
        if blackList.lookupListEntry(options.lookup):
            log.info(_("Present in blacklist."))
            success = True
        if not success:
            log.info(_("Address neither in blacklist or whitelist."))
            success = True
    if options.clearwl:
        if not whiteList.removeAll():
            log.error(_("Deleting whitelist failed."))
            return False
        else:
            log.info(_("Deleting whitelist done."))
            success = True
    if options.clearbl:
        if not blackList.removeAll():
            log.error(_("Deleting blacklist failed."))
            return False
        else:
            log.info(_("Deleting blacklist done."))
            success = True

    # Break here if preparation work has been done
    if success is not None:
        return success
    
    # Main loop
    if not processMail(conf, logLang, packs.getPackageList(), blackList,
                       whiteList):
        log.error(_("Processing mail failed."))
        return False

    return True

if __name__ == "__main__":
    if not main():
        print >> sys.stderr, "Main loop exited with errors."
        exit(1)
    else:
        exit(0)
