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
import sys
import re
import subprocess
import hashlib
from datetime import date, timedelta, datetime
from time import localtime

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

def dumpMessage(conf, message):
    """Dump a message to our dumpfile"""
    dumpFile = conf.getDumpFile()
    # Be nice: Create dir if it's not there
    dumpDir = os.path.dirname(dumpFile)
    if not os.access(dumpDir, os.W_OK):
        if not createDir(dumpDir):
            log.error("Could not create dump dir")
            return False
    try:
        fd = open(dumpFile, 'a')
        now = datetime.now()
        prefix = "Failed mail at %s:\n" % now.strftime("%Y-%m-%d %H:%M:%S")
        fd.write(prefix)
        fd.write(message)
        fd.close
        return True
    except Exception, e:
        log.error("Creating dump entry failed: %s" % e)
        return False

def installTranslations(conf, localeSrcdir):
    """Install all translation files to 'dir'"""
    log.info("Installing translation files..")
    hasDirs = None

    if conf is None:
        log.error("Bad arg.")
        return False
    if not os.path.isdir(localeSrcdir):
        log.info("Not a directory: %s" % localeSrcdir)
        if not createDir(localeSrcdir):
            log.error("Giving up on %s" % localeSrcdir)
            return False
    localeDir = conf.getLocaleDir()
    if not os.path.isdir(localeDir):
        log.info("Not a directory: %s" % localeDir)
        if not createDir(localeDir):
            log.error("Giving up on %s" % localeDir)
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
                        log.error("Giving up on %s" % targetDir)
                        return False
                if installMo(poFile, targetDir) == False:
                    log.error("Installing .mo files failed.")
                    return False
            except Exception:
                log.error("Error accessing translation files.")
                return False
    if hasDirs is None:
        log.error("Empty locale dir: " % localeSrcdir)
        return False

    log.info("Installing translation files done.")

    return True

def fetchPackages(conf, mirror):
    """Fetch Tor packages from a mirror"""
    log.info("Fetching package files..")
    try:
        packs = gettor.packages.Packages(conf, mirror, False)
    except IOError:
        log.error("Error initiating package list.")
        return False
    if packs.syncWithMirror() != 0:
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
    #packs.preparePackages()
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
    args = " --clear-blacklist=7 --fetch-packages --prep-packages"
    newCronTab = currentCronTab + '\n' + '3 2 * * * ' + path + args
    echoCmd = ['echo', newCronTab ]
    cronCmd = ['crontab', '-']
    echoProc = subprocess.Popen(echoCmd, stdout=subprocess.PIPE)
    cronProc = subprocess.Popen(cronCmd, stdin=echoProc.stdout)
    cronProc.communicate()[0]
    return cronProc.returncode

def addWhitelistEntry(conf, address):
    log.info("Adding address to whitelist: %s" % address)
    try:
        whiteList = gettor.blacklist.BWList(conf.getWlStateDir())
    except IOError, e:
        log.error("Whitelist error: %s" % e)
        return False
    if not whiteList.createListEntry(prepareAddress(address), "general"):
        log.error("Creating whitelist entry failed.")
        return False
    else:
        log.info("Creating whitelist entry ok.")
        return True

def addBlacklistEntry(conf, address):
    log.info("Adding address to blacklist: %s" % address)
    try:
        blackList = gettor.blacklist.BWList(conf.getBlStateDir())
    except IOError, e:
        log.error("Blacklist error: %s" % e)
        return False
    if not blackList.createListEntry(prepareAddress(address), "general"):
        log.error("Creating blacklist entry failed.")
        return False
    else:
        log.info("Creating whitelist entry ok.")
        return True

def lookupAddress(conf, address):
    log.info("Lookup address: %s" % address)
    found = False
    try:
        whiteList = gettor.blacklist.BWList(conf.getWlStateDir())
        blackList = gettor.blacklist.BWList(conf.getBlStateDir())
    except IOError, e:
        log.error("White/Blacklist error: %s" % e)
        return False
    if whiteList.lookupListEntry(address, "general"):
        log.info("Address '%s' is present in the whitelist." % address)
        found = True
    if blackList.lookupListEntry(address, "general"):
        log.info("Address '%s' is present in the blacklist." % address)
        found = True
    if not found:
        log.info("Address '%s' neither in blacklist or whitelist." % address)
        found = True

    # Always True
    return found

def clearWhitelist(conf):
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

def clearBlacklist(conf, olderThanDays):
    log.info("Clearing blacklist..")
    try:
        blackList = gettor.blacklist.BWList(conf.getBlStateDir())
    except IOError, e:
        log.error("Blacklist error: %s" % e)
        return False
    if not blackList.removeAll(olderThanDays):
        log.error("Deleting blacklist failed.")
        return False
    else:
        log.info("Deleting blacklist done.")
        return True

def setCmdPassword(conf, password):
    log.info("Setting command password")
    passwordHash = str(hashlib.sha1(password).hexdigest())
    cmdPassFile = conf.getCmdPassFile()
    # Be nice: Create dir if it's not there
    passDir = os.path.dirname(cmdPassFile)
    if not os.access(passDir, os.W_OK):
        if not createDir(passDir):
            log.error("Could not create pass dir")
            return False
    try:
        fd = open(cmdPassFile, 'w')
        fd.write(passwordHash)
        fd.close
        # Be secretive
        os.chmod(cmdPassFile, 0400)
        return True
    except Exception, e:
        log.error("Creating list entry %s failed: %s" % (entry, e))
        return False

def verifyPassword(conf, password):
    candidateHash = str(hashlib.sha1(password).hexdigest())
    cmdPassFile = conf.getCmdPassFile()
    try:
        fd = open(cmdPassFile, 'r')
        passwordHash = fd.read()
        fd.close
        if candidateHash == passwordHash:
            log.info("Verification succeeded")
            return True
        else:
            log.info("Verification failed")
            return False
    except Exception, e:
        log.error("Verifying password failed: %s" % e)
        return False

def hasExe(filename):
    if re.compile(".*.exe.*").match(filename):
        return True
    else:
        return False

def renameExe(filename, renameFile=True):
    log.info("Renaming exe..")
    if renameFile and not os.access(filename, os.R_OK):
        log.error("Could not access file %s" % filename)
        raise OSError

    newfilename = filename.replace(".exe", ".ex_RENAME", 1)
    if renameFile:
        os.rename(filename, newfilename)

    return newfilename

def fileIsOlderThan(filename, olderThanDays):
    olderThanDays = int(olderThanDays)
    if olderThanDays is not 0:
        daysold = datetime.now() - timedelta(days=olderThanDays)
        daysold = daysold.timetuple()
        filetimeUnix = os.path.getmtime(filename)
        filetime = localtime(filetimeUnix)
        if daysold < filetime:
            return False
        
    return True

def getVersionStringFromFile(filename):
    regex = "[a-z-]*-([0-9]*\.[0-9]*\.[0-9]*)"
    match = re.match(regex, filename)
    if match:
        return match.group(1)
    else:
        return None

def isNewTorVersion(old, new):
    oldsplit = old.split(".")
    newsplit = new.split(".")
    if len(oldsplit) != 3 or len(newsplit) != 3:
        log.error("Tor version length fail")
        return False
    if oldsplit[0] > newsplit[0]:
        return False
    if oldsplit[0] < newsplit[0]:
        return True
    if oldsplit[0] == newsplit[0]:
        if oldsplit[1] > newsplit[1]:
            return False
        if oldsplit[1] < newsplit[1]:
            return True
        if oldsplit[1] == newsplit[1]:
            if oldsplit[2] > newsplit[2]:
                return False
            if oldsplit[2] < newsplit[2]:
                return True
            if oldsplit[2] == newsplit[2]:
                # Same version
                return False

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
            log.error("Giving up on %s" % localeSrcdir)
            return False
    localeDir = config.getLocaleDir()
    if not os.path.isdir(localeDir):
        log.info("Not a directory: %s" % localeDir)
        if not createDir(localeDir):
            log.error("Giving up on %s" % localeDir)
            return False

def getCurrentCrontab():
    # This returns our current crontab
    savedTab = "# This crontab has been tampered with by gettor.py\n"
    currentTab = os.popen("crontab -l")
    for line in currentTab:
        savedTab += line
    return savedTab

def prepareAddress(address):
    """We need this because we internally store email addresses in this format
       in the black- and whitelists"""
    if address.startswith("<"):
        return address
    else:
        return "<" + address + ">"
