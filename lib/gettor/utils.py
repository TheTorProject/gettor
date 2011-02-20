# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

import os
import sys
import re
import subprocess
import hashlib
import logging
import errno
import zipfile

from datetime import date, timedelta, datetime
from time import localtime

import gettor.blacklist
import gettor.packages

def createDir(path):
    """Helper routine that creates a given directory. Doesn't fail if directory
       already exists.
    """
    try:
        logging.debug("Creating directory %s if it doesn't exist.." % path)
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logging.error("Failed to create directory %s: %s" % (path, e))
            return False
    return True

def makeZip(zipPath, fileList):
    """Create a zip file zipFile from the files listed in fileList.
    """
    zipper = zipfile.ZipFile(zipPath, "w")
    for item in fileList:
        zipper.write(item, os.path.basename(item))
    zipper.close()

def dumpMessage(dumpFile, message):
    """Dump a (mail) message to our dumpfile
    """
    # Be nice: Create dir if it's not there
    dumpDir = os.path.dirname(dumpFile)
    if not os.access(dumpDir, os.W_OK):
        if not createDir(dumpDir):
            logging.error("Could not create dump dir")
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
        logging.error("Creating dump entry failed: %s" % e)
        return False

def fetchPackages(conf):
    """Fetch Tor packages from a mirror
    """
    logging.info("Fetching package files..")
    try:
        packs = gettor.packages.Packages(conf, False)
    except IOError:
        logging.error("Error initiating package list.")
        return False
    if packs.syncWithMirror() != 0:
        logging.error("Syncing Tor packages failed.")
        return False
    else:
        logging.info("Syncing Tor packages done.")
        return True

def prepPackages(conf):
    """Prepare the downloaded packages in a way so GetTor can work with them
    """
    logging.info("Preparing package files..")
    packs = gettor.packages.Packages(conf)

    if not packs.preparePackages():
        return False
    if not packs.buildPackages():
       return False

    logging.info("Building packages done.")
    return True

def installCron():
    """Install all needed cronjobs for GetTor
    """
    logging.info("Installing cronjob..")
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
    """Add an entry to the global whitelist
    """
    wlStateDir = conf.BASEDIR + "/wl"
    logging.info("Adding address to whitelist: %s" % address)
    try:
        whiteList = gettor.blacklist.BWList(conf.wlStateDir)
    except IOError, e:
        logging.error("Whitelist error: %s" % e)
        return False
    if not whiteList.createListEntry(normalizeAddress(address), "general"):
        logging.error("Creating whitelist entry failed.")
        return False
    else:
        logging.info("Creating whitelist entry ok.")
        return True

def addBlacklistEntry(conf, address):
    """Add an entry to the global blacklist
    """
    logging.info("Adding address to blacklist: %s" % address)
    blStateDir = conf.BASEDIR + "/bl"
    try:
        blackList = gettor.blacklist.BWList(blStateDir)
    except IOError, e:
        logging.error("Blacklist error: %s" % e)
        return False
    if not blackList.createListEntry(normalizeAddress(address), "general"):
        logging.error("Creating blacklist entry failed.")
        return False
    else:
        logging.info("Creating whitelist entry ok.")
        return True

def lookupAddress(conf, address):
    """Lookup if a given address is in the blacklist- or whitelist pool
    """
    logging.info("Lookup address: %s" % address)
    found = False
    wlStateDir = conf.BASEDIR + "/wl"
    blStateDir = conf.BASEDIR + "/bl"
    try:
        whiteList = gettor.blacklist.BWList(wlStateDir)
        blackList = gettor.blacklist.BWList(blStateDir)
    except IOError, e:
        logging.error("White/Blacklist error: %s" % e)
        return False
    if whiteList.lookupListEntry(address, "general"):
        logging.info("Address '%s' is present in the whitelist." % address)
        found = True
    if blackList.lookupListEntry(address, "general"):
        logging.info("Address '%s' is present in the blacklist." % address)
        found = True
    if not found:
        logging.info("Address '%s' neither in blacklist or whitelist." % address)
        found = True

    # Always True
    return found

def clearWhitelist(conf):
    """Delete all entries in the global whitelist
    """
    wlStateDir = conf.BASEDIR + "/wl"
    try:
        whiteList = gettor.blacklist.BWList(wlStateDir)
    except IOError, e:
        logging.error("Whitelist error: %s" % e)
        return False
    logging.info("Clearing whitelist..")
    if not whiteList.removeAll():
        logging.error("Deleting whitelist failed.")
        return False
    else:
        logging.info("Deleting whitelist done.")
        return True

def clearBlacklist(conf, olderThanDays):
    """Delete all entries in the global blacklist that are older than
       'olderThanDays' days
    """
    logging.info("Clearing blacklist..")
    blStateDir = conf.BASEDIR + "/bl"
    try:
        blackList = gettor.blacklist.BWList(blStateDir)
    except IOError, e:
        logging.error("Blacklist error: %s" % e)
        return False
    if not blackList.removeAll(olderThanDays):
        logging.error("Deleting blacklist failed.")
        return False
    else:
        logging.info("Deleting blacklist done.")
        return True

def setCmdPassword(cmdPassFile, password):
    """Write the password for the admin commands in the configured file
       Hash routine used: SHA1
    """
    logging.info("Setting command password")
    passwordHash = str(hashlib.sha1(password).hexdigest())
    # Be nice: Create dir if it's not there
    passDir = os.path.dirname(cmdPassFile)
    if not os.access(passDir, os.W_OK):
        if not createDir(passDir):
            logging.error("Could not create pass dir")
            return False
    try:
        fd = open(cmdPassFile, 'w')
        fd.write(passwordHash)
        fd.close
        # Be secretive
        os.chmod(cmdPassFile, 0400)
        return True
    except Exception, e:
        logging.error("Creating pass file failed: %s" % e)
        return False

def verifyPassword(conf, password):
    """Verify that a given password matches the one provided in the
       password file
    """
    candidateHash = str(hashlib.sha1(password).hexdigest())
    try:
        fd = open(conf.PASSFILE, 'r')
        passwordHash = fd.read()
        fd.close
        if candidateHash == passwordHash:
            logging.info("Verification succeeded")
            return True
        else:
            logging.info("Verification failed")
            return False
    except Exception, e:
        logging.error("Verifying password failed: %s" % e)
        return False

def hasExe(filename):
    """Helper routine for building the packages for GetTor:
       Check if a file ends in .exe
    """
    if re.compile(".*.exe.*").match(filename):
        return True
    else:
        return False

def renameExe(filename, renameFile=True):
    """Helper routine for building the packages for GetTor:
       If we find a file ending in .exe, we rename it to .ex_RENAME
       to get past Google's spam filters
    """
    if renameFile and not os.access(filename, os.R_OK):
        logging.error("Could not access file %s" % filename)
        raise OSError

    newfilename = filename.replace(".exe", ".ex_RENAME", 1)
    if renameFile:
        os.rename(filename, newfilename)

    return newfilename

def fileIsOlderThan(filename, olderThanDays):
    """Return True if file 'filename' is older than 'olderThandays'
    """
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
    """Return what version string is encoded in Tor package filename
    """
    regex = "[a-z-]*-([0-9]*\.[0-9]*\.[0-9]*)"
    match = re.match(regex, filename)
    if match:
        return match.group(1)
    else:
        return None

def isNewTorVersion(old, new):
    """Return True if Tor version string 'new' is newer than 'old'
    """
    oldsplit = old.split(".")
    newsplit = new.split(".")
    if len(oldsplit) != 3 or len(newsplit) != 3:
        logging.error("Tor version length fail")
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

def installMo(poFile, targetDir):
    """Install a certain gettext .mo file
    """
    global log
    args = os.getcwd() + "/" + poFile + " -o " + targetDir + "/gettor.mo"
    try:
        ret = subprocess.call("msgfmt" + " " + args, shell=True)
        if ret < 0:
            logging.error("Error in msgfmt execution: %s" % ret)
            return False
    except OSError, e:
        logging.error("Comilation failed: " % e)
        return False
    return True

def getCurrentCrontab():
    """This returns our current crontab
    """
    savedTab = "# This crontab has been tampered with by gettor.py\n"
    currentTab = os.popen("crontab -l")
    for line in currentTab:
        savedTab += line
    return savedTab

def normalizeAddress(address):
    """We need this because we internally store email addresses in this format
       in the black- and whitelists
    """
    if address.startswith("<"):
        return address
    else:
        return "<" + address + ">"


def stripEmail(address):
    """Strip "Bart Foobar <bart@foobar.net>" to "<bart@foobar.net">
    """
    match = re.search('<.*?>', address)
    if match is not None:
        return match.group()
    # Make sure to return the address in the form of '<bla@foo.de>'
    return normalizeAddress(address)

