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
    for k in configPackages.keys():
        packageCounter[k] = 0

    try:
        logFile = open(filename, 'r')
    except:
        print >>sys.stderr, "Couldn't open logfile %s" % filename
        sys.exit(1)

    readData = logFile.read().split('\n')
    for line in readData:
        matchStr = "([0-9]{4}-[0-9]{2}-[0-9]{2}).*({'.*'}).*"
        match = re.match(matchStr, line, re.DOTALL)
        if match:
            dateInfo = match.group(1)
            reqInfo = ast.literal_eval(match.group(2))
            package = reqInfo['package']
            if package is not None:
                packageCounter[package] += 1
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
    logDir = os.path.join(config.BASEDIR, "log")
    logFilePattern = os.path.join(logDir, config.LOGFILE + "*.log")
    fileList = glob.glob(logFilePattern)
    for f in fileList:
        dateInfo, stats = makestats(f, config.PACKAGES)
        printStatsStdout(dateInfo, stats)

if __name__ == "__main__":
    main()
