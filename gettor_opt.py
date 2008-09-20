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

def parseOpts():
    cmdParser = optparse.OptionParser()
    cmdParser.add_option("-c", "--config", dest="configfile",
                        default="~/.gettorrc",
                        help="set config file to FILE", metavar="FILE")

    return cmdParser.parse_args()
