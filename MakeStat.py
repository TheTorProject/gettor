#!/usr/bin/python

import ast
import sys
import os
import re
import glob
import string
import gettor.config

def makestats(filename, configPackages):

    # Initialize package counter
    packageCounter = { 'None': 0}
    dateInfo = ""
    for k in configPackages.keys():
        packageCounter[k] = 0

    try:
        logFile = open(filename, 'r')
    except:
        print >>sys.stderr, "Couldn't open logfile %s" % filename
        sys.exit(1)

    readData = logFile.read().split('\n')
    for line in readData:
        # This is how we recognize a relevant line: Starts with a date like
        # 2011-10-04 and has a "{" with matching "}" somewhere.
        matchStr = "^([0-9]{4}-[0-9]{2}-[0-9]{2}).*({'.*}).*"
        match = re.match(matchStr, line, re.DOTALL)
        if match:
            dateInfo = match.group(1)
            reqInfo = ast.literal_eval(match.group(2))
            package = reqInfo['package']
            if package is not None:
                match = re.match("tor-browser-bundle(_.*)", package)
                if match:
                    package = "windows" + match.group(1)
                match = re.match("linux-browser-bundle(-.*)", package)
                if match:
                    package = "linux" + match.group(1)
                match = re.match("(macosx-i386)(.*)", package)
                if match:
                    package = "macos-i386"
                match = re.match("(macosx-ppc)(.*)", package)
                if match:
                    package = "macos-ppc"
                match = re.match("windows-bundle", package)
                if match:
                    continue
                if package in packageCounter.keys():
                    packageCounter[package] += 1
                else:
                    packageCounter['None'] += 1
            else:
                packageCounter['None'] += 1

    logFile.close()

    return dateInfo, packageCounter            

def printStatsStdout(daystr, stats):
    print daystr + " -", 
    for pack in sorted(stats.iterkeys()):
        packstr = "%s:%s" % (pack, stats[pack])
        print packstr,
    print ""

def main():
    stats = {}
    
    config = gettor.config.Config()
    logDir = os.path.join(config.BASEDIR, "var", "log")
    logFilePattern = os.path.join(logDir, config.LOGFILE + "*.log")
    fileList = glob.glob(logFilePattern)
    fileList = sorted(fileList)
    for f in fileList:
        dateInfo, stats = makestats(f, config.PACKAGES)
        printStatsStdout(dateInfo, stats)

if __name__ == "__main__":
    main()
