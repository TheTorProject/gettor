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
import gettor_log
import gettor_config
import re

__all__ = ["gettorPackages"]

class gettorPackages:

    packageRegex = { "windows-bundle": "vidalia-bundle-.*.exe$",
                     "panther-bundle": "vidalia-bundle-.*-panther.dmg$",
                     "tiger-bundle": "vidalia-bundle-.*-tiger.dmg$",
                     "source-bundle": "tor-.*.tar.gz",
                   }

    def __init__(self, mirror, config, silent=False):
        self.mirror = mirror
        self.packageList = {}
        self.distDir = config.getDistDir()
        self.packDir = config.getPackDir()
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
        for filename in os.listdir(self.packDir):
            self.packageList[filename[:-2]] = self.packDir + "/" + filename
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
                        zip.write(file)
                        zip.write(ascfile)
                        zip.close()
                        self.packageList[pack] = zipFileName
                        break
        if len(self.packageList) > 0:
            return True
        else:
            return False

    def syncWithMirror(self):
        process = subprocess.Popen(self.rsync)
        process.wait()
        return process.returncode

    def getCommandToStr(self):
        """This is useful for cronjob installations
        """
        rsyncstr = ""
        for i,v in enumerate(self.rsync):
            rsyncstr += self.rsync[i] + " "
        return rsyncstr

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
