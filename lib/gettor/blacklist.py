#!/usr/bin/python2.5
"""This library implements all of the black listing features needed for gettor.
Basically, it offers creation, removal and lookup of email addresses stored as
SHA1 hashes in a dedicated directory on the filesystem.
"""

import hashlib
import os
import re
import gettor.config
import gettor.gtlog

log = gettor.gtlog.getLogger()

conf = gettor.config.Config()
stateDir = conf.getStateDir()
blStateDir = conf.getBlStateDir()

# XXX
def createDir(path):
    try:
        log.info("Creating directory %s.." % path)
        os.makedirs(path)
    except OSError, e:
        log.error("Failed to create directory %s: %s" % (path, e))
        return False
    return True

class BWList:
    def __init__(self, listdir):
        self.listDir = listdir
        if not os.path.isdir(self.listDir):
            if not createDir(self.listDir):
                # XXX Change this to something more appropriate
                raise IOError("Bad dir: %s" % self.listDir)

    def lookupListEntry(self, address):
        """Check to see if we have a list entry for the given address."""
        if address is None:
           log.error("Argument 'address' is None")
           return False
        emailonly = self.stripEmail(address)
        entry = self.listDir + "/" + str(hashlib.sha1(emailonly).hexdigest())
        try:
            entry = os.stat(entry)
        except OSError:
            return False
        return True

    def createListEntry(self, address):
        """ Create a black- or whitelist entry """
        if address is None:
           log.error("Argument 'address' is None")
           return False
        emailonly = self.stripEmail(address)
        entry = self.listDir + "/" + str(hashlib.sha1(emailonly).hexdigest())
        if self.lookupListEntry(address) == False:
            try:
                fd = open(entry, 'w')
                fd.close
                return True
            except:
                log.error("Creating list entry %s failed." % entry)
                return False
        else:
            # List entry already exists
            return False

    def removeListEntry(self, address):
        """ Remove an entry from the black- or whitelist """
        if address is None:
           log.error("Argument 'address' is None")
           return False
        emailonly = self.stripEmail(address)
        entry = self.listDir + "/" + str(hashlib.sha1(emailonly).hexdigest())
        if (self.lookupListEntry(address) == True):
            try:
                os.unlink(entry)
            except OSError:
                log.error("Could not unlink entry %s" % entry)
                return False
        else:
            log.info("Requested removal of non-existing entry %s. Abord." 
                    % entry)
            return False

    def removeAll(self):
        print "Removing all entries from list!"
        for root, dirs, files in os.walk(self.listDir):
            for file in files:
                try:
                    rmfile = os.path.join(root, file)
                    os.remove(rmfile)
                except:
                    log.error("Could not remove %s." % rmfile)
                    return False
        return True

    def stripEmail(self, address):
        '''Strip "Bart Foobar <bart@foobar.net>" to "<bart@foobar.net">'''
        match = re.search('<.*?>', address)
        if match is not None:
            return match.group()
        return address
