#!/usr/bin/python2.5
"""This library implements all of the black listing features needed for gettor.
Basically, it offers creation, removal and lookup of email addresses stored as
SHA1 hashes in a dedicated directory on the filesystem.
"""

import hashlib
import os
import gettor_config
import gettor_log

log = gettor_log.getLogger()

conf = gettor_config.gettorConf()
stateDir = conf.getStateDir()
blStateDir = conf.getBlStateDir()

class BWList:
    def __init__(self, listdir):
        self.listDir = listdir
        if not os.path.isdir(self.listDir):
            # XXX Change this to something more appropriate
            raise IOError("Bad dir: %s" % self.listDir)

    def lookupListEntry(self, address):
        """Check to see if we have a list entry for the given address."""
        entry = self.listDir + "/" + str(hashlib.sha1(address).hexdigest())
        try:
            entry = os.stat(entry)
        except OSError:
            return False
        return True

    def createListEntry(self, address):
        entry = self.listDir + "/" + str(hashlib.sha1(address).hexdigest())
        if self.lookupListEntry(address) == False:
            try:
                fd = open(entry, 'w')
                fd.close
                return True
            except:
                log.error(_("Creating list entry %s failed.") % entry)
                return False
        else:
            # List entry already exists
            return False

    def removeListEntry(self, address):
        entry = self.listDir + "/" + str(hashlib.sha1(address).hexdigest())
        if (self.lookupListEntry(address) == True):
            try:
                os.unlink(entry)
            except OSError:
                log.error(_("Could not unlink entry %s") % entry)
                return False
        else:
            log.info(_("Requested removal of non-existing entry %s. Abord.") 
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
                    log.error(_("Could not remove %s." % rmfile))
                    return False
        return True

def blackListtests(address):
    """ This is a basic evaluation of our blacklist functionality """
    bwlist = BWList("/tmp/") 
    print bwlist.createListEntry(address)
    print bwlist.lookupListEntry(address)
    #prepBLStateDir()
    #privateAddress = makeAddressPrivate(address)
    #print "We have a private address of: "  + privateAddress
    #print "Testing creation of blacklist entry: "
    #blackListEntry = createBlackListEntry(privateAddress)
    #print blackListEntry
    #print "We're testing a lookup of a known positive blacklist entry: "
    #blackListEntry = lookupBlackListEntry(privateAddress)
    #print blackListEntry
    #print "We're testing removal of a known blacklist entry: "
    #blackListEntry = removeBlackListEntry(privateAddress)
    #print blackListEntry
    #print "We're testing a lookup of a known false blacklist entry: "
    #blackListEntry = lookupBlackListEntry(privateAddress)
    #print blackListEntry
    #print "Now we'll test the higher level blacklist functionality..."
    #print "This should not find an entry in the blacklist: "
    #print blackList(address)
    #print "This should add an entry to the blacklist: "
    #print blackList(address, True)
    #print "This should find the previous addition to the blacklist: "
    #print blackList(address)
    #print "Please ensure the tests match what you would expect for your environment."

if __name__ == "__main__" :
    print "Running some tests.."
    blackListtests("requestingUser@example.com")
