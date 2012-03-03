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
    except Exception as e:
        logging.error("Creating dump entry failed: %s" % e)
        return False

def fetchPackages(conf):
    """Fetch Tor packages from a mirror
    """
    logging.debug("Fetching package files..")
    try:
        packs = gettor.packages.Packages(conf, False)
    except IOError:
        logging.error("Error initiating package list.")
        return False
    if packs.syncWithMirror() != 0:
        logging.error("Syncing Tor packages failed.")
        return False
    else:
        logging.debug("Syncing Tor packages done.")
        return True

def prepPackages(conf):
    """Prepare the downloaded packages in a way so GetTor can work with them
    """
    logging.debug("Preparing package files..")
    packs = gettor.packages.Packages(conf)

    if not packs.preparePackages():
        return False
    if not packs.buildPackages():
       return False

    # Copy the short user manual
    packs.copyManuals()

    logging.debug("Building packages done.")
    return True

def installCron():
    """Install all needed cronjobs for GetTor
    """
    logging.debug("Installing cronjob..")
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
    wlStateDir = os.path.join(conf.BASEDIR, 'var', 'cache', 'gettor', 'wl')
    logging.debug("Adding address to whitelist: %s" % address)
    try:
        whiteList = gettor.blacklist.BWList(wlStateDir, conf.BLACKLIST_THRES)
    except IOError, e:
        logging.error("Whitelist error: %s" % e)
        return False
    if not whiteList.createListEntry(normalizeAddress(address), "general"):
        logging.error("Creating whitelist entry failed.")
        return False
    else:
        logging.debug("Creating whitelist entry ok.")
        return True

def addBlacklistEntry(conf, address):
    """Add an entry to the global blacklist
    """
    logging.debug("Adding address to blacklist: %s" % address)
    blStateDir = os.path.join(conf.BASEDIR, 'var', 'cache', 'gettor', 'bl')
    try:
        blackList = gettor.blacklist.BWList(blStateDir, conf.BLACKLIST_THRES)
    except IOError, e:
        logging.error("Blacklist error: %s" % e)
        return False
    if not blackList.createListEntry(normalizeAddress(address), "general"):
        logging.error("Creating blacklist entry failed.")
        return False
    else:
        logging.debug("Creating whitelist entry ok.")
        return True

def lookupAddress(conf, address):
    """Lookup if a given address is in the blacklist- or whitelist pool
    """
    logging.debug("Lookup address: %s" % address)
    found = False
    wlStateDir = os.path.join(conf.BASEDIR, 'var', 'cache', 'gettor', 'wl')
    blStateDir = os.path.join(conf.BASEDIR, 'var', 'cache', 'gettor', 'bl')
    try:
        whiteList = gettor.blacklist.BWList(wlStateDir, conf.BLACKLIST_THRES)
        blackList = gettor.blacklist.BWList(blStateDir, conf.BLACKLIST_THRES)
    except IOError, e:
        logging.error("White/Blacklist error: %s" % e)
        return False
    if whiteList.checkAndUpdate(address, "general"):
        logging.info("Address '%s' is present in the whitelist." % address)
        found = True
    if blackList.checkAndUpdate(address, "general"):
        logging.info("Address '%s' is present in the blacklist." % address)
        found = True
    if not found:
        logging.info("Address '%s' neither in black or whitelist." % address)
        found = True

    # Always True
    return found

def clearWhitelist(conf):
    """Delete all entries in the global whitelist
    """
    wlStateDir = os.path.join(conf.BASEDIR, 'var', 'cache', 'gettor', 'wl')
    try:
        whiteList = gettor.blacklist.BWList(wlStateDir, conf.BLACKLIST_THRES)
    except IOError, e:
        logging.error("Whitelist error: %s" % e)
        return False
    logging.debug("Clearing whitelist..")
    if not whiteList.removeAll():
        logging.error("Deleting whitelist failed.")
        return False
    else:
        logging.debug("Deleting whitelist done.")
        return True

def clearBlacklist(conf, olderThanDays):
    """Delete all entries in the global blacklist that are older than
       'olderThanDays' days
    """
    logging.debug("Clearing blacklist..")
    blStateDir = os.path.join(conf.BASEDIR, 'var', 'cache', 'gettor', 'bl')
    try:
        blackList = gettor.blacklist.BWList(blStateDir, conf.BLACKLIST_THRES)
    except IOError, e:
        logging.error("Blacklist error: %s" % e)
        return False
    if not blackList.removeAll(olderThanDays):
        logging.error("Deleting blacklist failed.")
        return False
    else:
        logging.debug("Deleting blacklist done.")
        return True

def setCmdPassword(conf, password):
    """Write the password for the admin commands in the configured file
       Hash routine used: SHA1
    """
    logging.debug("Setting command password")
    passwordHash = str(hashlib.sha1(password).hexdigest())
    # Be nice: Create dir if it's not there
    passwordDir = os.path.join(conf.BASEDIR, 'etc', 'gettor')
    if not createDir(passwordDir):
        logging.error("Couldn't create password dir %s" % passwordDir)
        return False
    passFile = os.path.join(passwordDir, conf.PASSFILE)
    try:
        fd = open(passFile, 'w')
        fd.write(passwordHash)
        fd.close
        # Sekrit
        os.chmod(passFile, 0400)
        return True
    except Exception as e:
        logging.error("Creating pass file failed: %s" % e)
        return False

def verifyPassword(conf, password):
    """Verify that a given password matches the one provided in the
       password file
    """
    candidateHash = str(hashlib.sha1(password).hexdigest())
    try:
        passFile = os.path.join(conf.BASEDIR, 'etc', 'gettor', conf.PASSFILE)
        fd = open(passFile, 'r')
        passwordHash = fd.read()
        fd.close
        if candidateHash == passwordHash:
            logging.debug("Verification succeeded")
            return True
        else:
            logging.error("Verification failed")
            return False
    except Exception as e:
        logging.error("Verifying password failed: %s" % e)
        return False

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

def getCurrentCrontab():
    """This returns our current crontab
    """
    savedTab = "# This crontab has been tampered with by gettor.py\n"
    currentTab = os.popen("crontab -l")
    for line in currentTab:
        savedTab += line
    return savedTab

def normalizeAddress(address):
    """This does everything from checking if the address is ok to stripping
       dots and "+" addresses so absuing GetTor gets harder.
    """
    address = normalizeEmail(address)
    return "<" + address + ">"


def stripEmail(address):
    """Strip "Bart Foobar <bart@foobar.net>" to "<bart@foobar.net">
    """
    match = re.search('<.*?>', address)
    if match is not None:
        return match.group()
    # Make sure to return the address in the form of '<bla@foo.de>'
    return normalizeAddress(address)

def stripHTMLTags(string):
    """Simple HTML stripper
    """
    return re.sub(r'<[^>]*?>', '', string)

def getHash(string):
    """Return hash of given string
    """
    return str(hashlib.sha1(string).hexdigest())

def removeFromListByRegex(l, string):
    """Remove entries from a list that match a certain regular expression
    """
    for f in l:
        m = re.search(string, f)
        if m:
            l.remove(f)

    return l

def getBase64Size(unencoded_size):
    """Return the number of bytes a given byte sequence will expand to if it
       is base64 (MIME) encoded.

       Source for the formula: Wikipedia
    """
    return (unencoded_size + 814) * 1.37

def getMaxAttSize(addr, config):
    """Return the maximum attachment size allowed for a certain email 
       provider. If the provider isn't known by us, return 0, indicating
       an unlimited attachment size.
    """
    (_, domain) = emailGetLocalAndDomainPart(addr)
    if domain in config.PROVIDER_ATTACHMENT_SIZES:
       return config.PROVIDER_ATTACHMENT_SIZES[domain] * 1024 * 1024
    else:
       return 0

# The following code is more or less taken from BridgeDB

class BadEmail(Exception):
    """Exception raised when we get a bad email address."""
    def __init__(self, msg, email):
        Exception.__init__(self, msg)
        self.email = email

ASPECIAL = '-_+/=_~'

ACHAR = r'[\w%s]' % "".join("\\%s"%c for c in ASPECIAL)
DOTATOM = r'%s+(?:\.%s+)*'%(ACHAR,ACHAR)
DOMAIN = r'\w+(?:\.\w+)*'
ADDRSPEC = r'(%s)\@(%s)'%(DOTATOM, DOMAIN)

SPACE_PAT = re.compile(r'\s+')
ADDRSPEC_PAT = re.compile(ADDRSPEC)

def extractAddrSpec(addr):
    """Given an email From line, try to extract and parse the addrspec
       portion.  Returns localpart,domain on success; raises BadEmail
       on failure.
    """
    orig_addr = addr
    addr = SPACE_PAT.sub(' ', addr)
    addr = addr.strip()
    # Only works on usual-form addresses; raises BadEmail on weird
    # address form.  That's okay, since we'll only get those when
    # people are trying to fool us.
    if '<' in addr:
        # Take the _last_ index of <, so that we don't need to bother
        # with quoting tricks.
        idx = addr.rindex('<')
        addr = addr[idx:]
        m = re.search(r'<([^>]*)>', addr)
        if m is None:
            raise BadEmail("Couldn't extract address spec", orig_addr)
        addr = m.group(1)

    # At this point, addr holds a putative addr-spec.  We only allow the
    # following form:
    #   addr-spec = local-part "@" domain
    #   local-part = dot-atom
    #   domain = dot-atom
    #
    # In particular, we are disallowing: obs-local-part, obs-domain,
    # comment, obs-FWS,
    #
    # Other forms exist, but none of the incoming services we recognize
    # support them.
    addr = addr.replace(" ", "")
    m = ADDRSPEC_PAT.match(addr)
    if not m:
        raise BadEmail("Bad address spec format", orig_addr)
    localpart, domain = m.groups()
    return localpart, domain

def emailGetLocalAndDomainPart(addr):
    """For a given email address, return a touple of localpart, domainpart.
       Example:
       bla@foo.org -> bla, foo.org
    """
    addr = addr.lower()
    localpart, domain = extractAddrSpec(addr)

    # addr+foo@ is an alias for addr@
    idx = localpart.find('+')
    if idx >= 0:
        localpart = localpart[:idx]
    localpart = localpart.replace(".", "")

    return localpart, domain

def normalizeEmail(addr):
    """Return normalized email address.
    """
    return "%s@%s" % emailGetLocalAndDomainPart(addr)

