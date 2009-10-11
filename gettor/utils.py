#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 utils.py: Useful helper routines

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

 This module handles all package related functionality
'''

import os

import gettor.gtlog
import gettor.blacklist
import gettor.packages

log = gettor.gtlog.getLogger()

def createDir(path):
    """Helper routine that creates a given directory"""
    try:
        log.info("Creating directory %s.." % path)
        os.makedirs(path)
    except OSError, e:
        log.error("Failed to create directory %s: %s" % (path, e))
        return False
    return True

def installTrans(conf, dir):
    """Install all translation files to 'dir'"""
    log.info("Installing translation files..")
    hasDirs = None

    if conf is None:
        log.error("Bad arg.")
        return False
    if not os.path.isdir(localeSrcdir):
        log.info("Not a directory: %s" % localeSrcdir)
        if not createDir(localeSrcdir):
            log.error(_("Giving up on %s" % localeSrcdir))
            return False
    localeDir = conf.getLocaleDir()
    if not os.path.isdir(localeDir):
        log.info("Not a directory: %s" % localeDir)
        if not createDir(localeDir):
            log.error(_("Giving up on %s" % localeDir))
            return False

    # XXX: Warn if there is no translation files anywhere..
    for root, dirs, files in os.walk(localeSrcdir):
        # Python lacks 'depth' feature for os.walk()
        if root != localeSrcdir:
            continue
        for dir in dirs:
            hasDirs = True
            if dir.startswith("."):
                continue
            # We ignore the templates dir for now
            if dir.startswith("templates"):
                continue
            try:
                poFile = os.path.join(root, dir) + "/gettor.po"
                # Construct target dir
                targetDir = localeDir + "/" + dir + "/LC_MESSAGES"
                if not os.path.isdir(targetDir):
                    log.info("Not a directory: %s" % targetDir)
                    if not createDir(targetDir):
                        log.error(_("Giving up on %s" % targetDir))
                        return False
                if installMo(poFile, targetDir) == False:
                    log.error("Installing .mo files failed.")
                    return False
            except Exception:
                log.error("Error accessing translation files.")
                return False
    if hasDirs is None:
        log.errpr("Empty locale dir: " % localeSrcdir)
        return False

    return True

def fetchPackages(conf, mirror):
    """Fetch Tor packages from a mirror"""
    log.info("Fetching package files..")
    try:
        packs = gettor.packages.Packages(conf)
    except IOError:
        log.error("Error initiating package list.")
        return False
    if packs.syncWithMirror(mirror, False) != 0:
        log.error("Syncing Tor packages failed.")
        return False
    else:
        log.info("Syncing Tor packages done.")
        return True

def prepPackages(conf):
    """Prepare the downloaded packages in a way so GetTor can work with them"""
    log.info("Preparing package files..")
    try:
        packs = gettor.packages.Packages(conf)
    except IOError:
        log.error("Error initiating package list.")
        return False
    if not packs.buildPackages():
        log.error("Building packages failed.")
        return False
    else:
        log.info("Building packages done.")
        return True

def installCron():
    log.info("Installing cronjob..")
    # XXX: Check if cron is installed and understands our syntax?
    currentCronTab = getCurrentCrontab()
    path = os.getcwd() + "/" + os.path.basename(sys.argv[0])
    args = " --clear-blacklist --fetch-packages --prep-packages"
    newCronTab = currentCronTab + '\n' + '3 2 * * * ' + path + args
    echoCmd = ['echo', newCronTab ]
    cronCmd = ['crontab', '-']
    echoProc = subprocess.Popen(echoCmd, stdout=subprocess.PIPE)
    cronProc = subprocess.Popen(cronCmd, stdin=echoProc.stdout)
    cronProc.communicate()[0]
    return cronProc.returncode

def addWhitelistEntry(address):
    log.info("Adding address to whitelist: %s" % address)
    try:
        whiteList = gettor.blacklist.BWList(conf.getWlStateDir())
    except IOError, e:
        log.error("Whitelist error: %s" % e)
        return False
    if not whiteList.createListEntry(options.whitelist):
        log.error("Creating whitelist entry failed.")
        return False
    else:
        log.info("Creating whitelist entry ok.")
        return True

def addBlacklistEntry(address):
    log.info("Adding address to blacklist: %s" % address)
    try:
        blackList = gettor.blacklist.BWList(conf.getBlStateDir())
    except IOError, e:
        log.error("Blacklist error: %s" % e)
        return False
    if not blackList.createListEntry(options.whitelist):
        log.error("Creating blacklist entry failed.")
        return False
    else:
        log.info("Creating whitelist entry ok.")
        return True

def lookupAddress(address):
    log.info("Lookup address: %s" % address)
    found = False
    try:
        whiteList = gettor.blacklist.BWList(conf.getWlStateDir())
        blackList = gettor.blacklist.BWList(conf.getBlStateDir())
    except IOError, e:
        log.error("White/Blacklist error: %s" % e)
        return False
    if whiteList.lookupListEntry(address):
        log.info("Address '%s' is present in the whitelist." % address)
        found = True
    if blackList.lookupListEntry(address):
        log.info("Address '%s' is present in the blacklist." % address)
        found = True
    if not success:
        log.info("Address '%s' neither in blacklist or whitelist." % address)
        found = True

    return found

def clearWhitelist():
    try:
        whiteList = gettor.blacklist.BWList(conf.getWlStateDir())
    except IOError, e:
        log.error("Whitelist error: %s" % e)
        return False
    log.info("Clearing whitelist..")
    if not whiteList.removeAll():
        log.error("Deleting whitelist failed.")
        return False
    else:
        log.info("Deleting whitelist done.")
        return True

def clearBlacklist():
    log.info("Clearing blacklist..")
    try:
        blackList = gettor.blacklist.BWList(conf.getBlStateDir())
    except IOError, e:
        log.error("Blacklist error: %s" % e)
        return False
    if not blackList.removeAll():
        log.error("Deleting blacklist failed.")
        return False
    else:
        log.info("Deleting blacklist done.")
        return True

# Helper routines go here ####################################################

def installMo(poFile, targetDir):
    global log
    args = os.getcwd() + "/" + poFile + " -o " + targetDir + "/gettor.mo"
    try:
        ret = subprocess.call("msgfmt" + " " + args, shell=True)
        if ret < 0:
            log.error("Error in msgfmt execution: %s" % ret)
            return False
    except OSError, e:
        log.error("Comilation failed: " % e)
        return False
    return True

def installTrans(config, localeSrcdir):
    global log
    hasDirs = None

    if config is None:
        log.error("Bad arg.")
        return False
    if not os.path.isdir(localeSrcdir):
        log.info("Not a directory: %s" % localeSrcdir)
        if not createDir(localeSrcdir):
            log.error(_("Giving up on %s" % localeSrcdir))
            return False
    localeDir = config.getLocaleDir()
    if not os.path.isdir(localeDir):
        log.info("Not a directory: %s" % localeDir)
        if not createDir(localeDir):
            log.error(_("Giving up on %s" % localeDir))
            return False

def getCurrentCrontab():
    # This returns our current crontab
    savedTab = "# This crontab has been tampered with by gettor.py\n"
    currentTab = os.popen("crontab -l")
    for line in currentTab:
        savedTab += line
    return savedTab

