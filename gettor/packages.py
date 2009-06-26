#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 gettor_packages.py: Package related stuff

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.

 This module handles all package related functionality
'''

import os
import zipfile
import subprocess
import gettor.gtlog
import gettor.config
import re

__all__ = ["gettorPackages"]

log = gettor.gtlog.getLogger()

class gettorPackages:

    packageRegex = { "windows-bundle": "vidalia-bundle-.*.exe$",
                     "panther-bundle": "vidalia-bundle-.*-ppc.dmg$",
                     "macosx-universal-bundle": "vidalia-bundle-.*-universal.dmg$",
                     "source-bundle": "tor-.*.tar.gz",
                     "tor-browser-bundle": "tor-browser-.*_en-US.exe",
                     "tor-im-browser-bundle": "tor-im-browser-.*_en-US.exe",
                     # Mike won't sign Torbutton; He doesn't get gettor support
                     #"torbutton": "torbutton-current.xpi$",
                   }

    def __init__(self, mirror, config, silent=False):
        self.mirror = mirror
        self.packageList = {}
        self.distDir = config.getDistDir()
        try:
            entry = os.stat(self.distDir)
        except OSError, e:
            log.error("Bad dist dir %s: %s" % (self.distDir, e))
            raise IOError
        self.packDir = config.getPackDir()
        try:
            entry = os.stat(self.packDir)
        except OSError, e:
            log.error("Bad pack dir %s: %s" % (self.packDir, e))
            raise IOError
        self.rsync = ["rsync"]
        self.rsync.append("-a")
        # Don't download dotdirs
        self.rsync.append("--exclude='.*'")
        if not silent:
            self.rsync.append("--progress")
        self.rsync.append("rsync://%s/tor/dist/current/" % self.mirror)
        self.rsync.append(self.distDir)

    def getPackageList(self):
        # Build dict like 'name': 'name.z'
        try:
            for filename in os.listdir(self.packDir):
                self.packageList[filename[:-2]] = self.packDir + "/" + filename
        except OSError, (strerror):
            log.error(_("Failed to build package list: %s") % strerror)
            return None

        # Check sanity
        for key, val in self.packageList.items():
            # Remove invalid packages
            if not os.access(val, os.R_OK):
                log.info(_("Warning: %s not accessable. Removing from list.") % val)
                del self.packageList[key]
        return self.packageList

    def buildPackages(self):
        for filename in os.listdir(self.distDir):
            for (pack, regex) in self.packageRegex.items():
                if re.compile(regex).match(filename):
                    file = self.distDir + "/" + filename
                    ascfile = file + ".asc"
                    zipFileName  = self.packDir + "/" + pack + ".z"
                    # If .asc file is there, build Zip file
                    if os.access(ascfile, os.R_OK):
                        zip = zipfile.ZipFile(zipFileName, "w")
                        zip.write(file, os.path.basename(file))
                        zip.write(ascfile, os.path.basename(ascfile))
                        zip.close()
                        self.packageList[pack] = zipFileName
                        break
        if len(self.packageList) > 0:
            return True
        else:
            log.error(_("Failed at building packages"))
            return False

    def syncWithMirror(self):
        process = subprocess.Popen(self.rsync)
        process.wait()
        return process.returncode

    def getCommandToStr(self):
        """This is useful for cronjob installations
        """
        return ''.join(self.rsync)

if __name__ == "__main__" :
    c = gettor_config.gettorConf()
    p = gettorPackages("rsync.torproject.org", c)
    print "Building packagelist.."
    if p.syncwithMirror() != 0:
        print "Failed."
        exit(1)
    if not p.buildPackageList():
        print "Failed."
        exit(1)
    print "Done."
    for (pack, file) in p.getPackageList().items():
        print "Bundle is mapped to file: ", pack, file
