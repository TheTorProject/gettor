#!/usr/bin/python2.5
"""
This library implements all of the black listing features needed for gettor.
"""

import hashlib
import os
from gettor_config import gettorConf

conf = gettorConf()
stateDir = conf.getStateDir()
blStateDir = conf.getBlStateDir()

def blackList(address, createEntry=False):
    """ 
    Check to see if an address is on our blacklist. If it is - we'll return true.
    If requested, we'll attempt to create a blacklist entry and return true if 
    everything works out.
    """
    # XXX TODO: Eventually we may want to sort entries with netcom
    # style /tmp/gettor/2-digits-of-hash/2-more-digits/rest-of-hash files

    prepBLStateDir()

    privateAddress = makeAddressPrivate(address)
    blackListed = lookupBlackListEntry(privateAddress)
    
    if blackListed:
        return True
    elif createEntry:
        return createBlackListEntry(privateAddress)

    return False

def lookupBlackListEntry(privateAddress):
    """ Check to see if we have a blacklist entry for the given address. """
    entry = stateDir + str(privateAddress)
    try:
        entry = os.stat(entry)
    except OSError:
        return False
    return True

def createBlackListEntry(privateAddress):
    """ Create a zero byte file that represents the address in our blacklist. """
    entry = blStateDir + str(privateAddress)
    stat = None
    try:
        stat = os.stat(entry)
    except OSError:
        try:
            fd = open(entry, 'w')
            fd.close()
            return True
        except:
            return False
    return False

def removeBlackListEntry(privateAddress):
    """ Remove the zero byte file that represents an entry in our blacklist."""
    entry = blStateDir + str(privateAddress)
    stat = None
    try:
        entry = os.unlink(entry)
    except OSError:
        return False
    return True

def makeAddressPrivate(address):
    """ Creates a unique identifier for the user. """
    hash = hashlib.sha1(address)
    privateAddress = hash.hexdigest()
    return privateAddress

def prepBLStateDir():
    stat = None
    try:
        stat = os.stat(stateDir)
        return True
    except OSError:
        try:
            os.makedirs(stateDir)
            return True
        except:
            return False

def blackListtests(address):
    """ This is a basic evaluation of our blacklist functionality """
    prepBLStateDir()
    privateAddress = makeAddressPrivate(address)
    print "We have a private address of: "  + privateAddress
    print "Testing creation of blacklist entry: "
    blackListEntry = createBlackListEntry(privateAddress)
    print blackListEntry
    print "We're testing a lookup of a known positive blacklist entry: "
    blackListEntry = lookupBlackListEntry(privateAddress)
    print blackListEntry
    print "We're testing removal of a known blacklist entry: "
    blackListEntry = removeBlackListEntry(privateAddress)
    print blackListEntry
    print "We're testing a lookup of a known false blacklist entry: "
    blackListEntry = lookupBlackListEntry(privateAddress)
    print blackListEntry
    print "Now we'll test the higher level blacklist functionality..."
    print "This should not find an entry in the blacklist: "
    print blackList(address)
    print "This should add an entry to the blacklist: "
    print blackList(address, True)
    print "This should find the previous addition to the blacklist: "
    print blackList(address)
    print "Please ensure the tests match what you would expect for your environment."

if __name__ == "__main__" :
    print "It appears that you're manually calling the blacklisting code. We'll run some tests..."
    blackListtests("requestingUser@example.com")
