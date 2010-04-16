#!/usr/bin/python

import sys
import os
import re
import string

def emptyPacks(packs):
    for k, v in packs.iteritems():
        packs[k] = 0
    return packs

def makestats(filename, days):
    day = None
    pack = None
    lang = None
    packages = {"None": 0,
                "tor-browser-bundle": 0,
                "tor-im-browser-bundle": 0,
                "tor-browser-bundle_en": 0,
                "tor-im-browser-bundle_en": 0,
                "tor-browser-bundle_de": 0,
                "tor-im-browser-bundle_de": 0,
                "tor-browser-bundle_ar": 0,
                "tor-im-browser-bundle_ar": 0,
                "tor-browser-bundle_es": 0,
                "tor-im-browser-bundle_es": 0,
                "tor-browser-bundle_fa": 0,
                "tor-im-browser-bundle_fa": 0,
                "tor-browser-bundle_fr": 0,
                "tor-im-browser-bundle_fr": 0,
                "tor-browser-bundle_it": 0,
                "tor-im-browser-bundle_it": 0,
                "tor-browser-bundle_nl": 0,
                "tor-im-browser-bundle_nl": 0,
                "tor-browser-bundle_pl": 0,
                "tor-im-browser-bundle_pl": 0,
                "tor-browser-bundle_pt": 0,
                "tor-im-browser-bundle_pt": 0,
                "tor-browser-bundle_ru": 0,
                "tor-im-browser-bundle_ru": 0,
                "tor-browser-bundle_zh_CN": 0,
                "tor-im-browser-bundle_zh_CN": 0,
                "source-bundle": 0,
                "macosx-ppc-bundle": 0,
                "macosx-i386-bundle": 0}

    try:
        logFile = open(filename, 'r')
    except:
        print "Couldn't open logfile %s" % filename
        sys.exit(1)
    readData = logFile.read().split('\n')
    for line in readData:
        match = re.match(".*Request from.*cmdaddr None.*", line, re.DOTALL)
        if match:
            splitline = string.split(line)
            if len(splitline) > 12:
                day = splitline[0]
                pack = splitline[7]
                lang = splitline[9]
                if not re.match("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]", day):
                    continue
                pack = pack.strip(',')
                lang = lang.strip(',')
                if day in days:
                    packs = days[day]
                else:
                    packs = emptyPacks(packages).copy()
                if pack is not None:
                    if pack in packs:
                        packs[pack] += 1
                days[day] = packs
        else:
            match = re.match(".*Request From.*Cmdaddr: None.*", line, re.DOTALL)
            if match:
                splitline = string.split(line)
                if len(splitline) > 12:
                    day = splitline[0]
                    pack = splitline[9]
                    lang = splitline[11]
                    if not re.match("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]", day):
                        continue
                    pack = pack.strip(',')
                    lang = lang.strip(',')
                    if day in days:
                        packs = days[day]
                    else:
                        packs = emptyPacks(packages).copy()
                    if pack is not None:
                        if pack in packs:
                            packs[pack] += 1
                    days[day] = packs

def printStatsStdout(days):
    for day in sorted(days.iterkeys()):
        packs = days[day]
        daystr = "%s -" % day
        print daystr, 
        for pack in sorted(packs.iterkeys()):
            packstr = "%s:%s" % (pack, packs[pack])
            print packstr,
        print ""

def printStatsGNUPlot(days):
    for day in sorted(days.iterkeys()):
        packs = days[day]
        print day,
        for pack in sorted(packs.iterkeys()):
            print packs[pack],
        print ""

def main():
    days = {}
    
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage: %s LOGDIR" % sys.argv[0]
        sys.exit(1)
    for arg in sys.argv:
        if not os.path.isfile(arg):
            print >> sys.stderr, "Not a file: %s" % arg
            sys.exit(1)
        makestats(arg, days)

    printStatsStdout(days)
    #printStatsGNUPlot(days)

if __name__ == "__main__":
    main()
