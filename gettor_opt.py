#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 gettor_config.py: Command line parser for gettor

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.


 This is the option parser module for gettor.
'''

import optparse

__all__ = ["parseOpts"]

def parseOpts():
    cmdParser = optparse.OptionParser()
    cmdParser.add_option("-c", "--config", dest="configfile",
                        default="~/.gettorrc",
                        help="set config file to FILE", metavar="FILE")
    cmdParser.add_option("-m", "--use-mirror", dest="mirror",
                        default="rsync.torproject.org",
                        help="set Tor package mirror to MIRROR", metavar="MIRROR")
    cmdParser.add_option("-i", "--install-crontab", dest="installcron",
                        action="store_true", default=False,
                        help="install crontab to refresh packagelist")
    cmdParser.add_option("-f", "--fetch-packages", dest="fetchpackages",
                        action="store_true", default=False,
                        help="fetch Tor packages from mirror")
    cmdParser.add_option("-p", "--prep-packages", dest="preppackages",
                        action="store_true", default=False,
                        help="prepare packages (zip them)")
    cmdParser.add_option("-t", "--run-tests", dest="runtests",
                        action="store_true", default=False,
                        help="run some tests")

    return cmdParser.parse_args()

if __name__ == "__main__":
    print >> sys.stderr "You shouldn't run this directly."
