#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 gettor_packages.py: Package related stuff

 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.


'''

import os
import zipfile
import subprocess
import gettor_log
import gettor_config
import re

class gettorPackages:

    packageRegex = { "vidalia-windows-bundle": "vidalia-bundle-.*.exe$",
                     "vidalia-panther-bundle": "vidalia-bundle-.*-panther.dmg$",
                     "vidalia-tiger-bundle": "vidalia-bundle-.*-tiger.dmg$",
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
        for (pack, reg) in self.packageRegex.items():
            self.rsync.append("--include='"+reg+"'")
        if not silent:
            self.rsync.append("--progress")
        self.rsync.append("rsync://%s/tor/dist/current/" % self.mirror)
        self.rsync.append(self.distDir)

    def getPackageList(self):
        return self.packageList

    def buildPackageList(self):
        process = subprocess.Popen(self.rsync)
        process.wait()
        # Packagelist building, part I: Set up basic bundle/file mapping
        for filename in os.listdir(self.distDir):
            for (pack, regex) in self.packageRegex.items():
                if re.compile(regex).match(filename):
                    print "Match: ", filename
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
            #else:
                 # XXX: Maybe tell rsync to only sync needed files instead of
                 # deleting them hereafter
                 #print "Removing unneeded file: ", filename
                 #os.unlink(self.distDir + "/" + filename)

if __name__ == "__main__" :
    c = gettor_config.gettorConf()
    p = gettorPackages("rsync.torproject.org", c)
    print "Building packagelist.."
    p.buildPackageList()
    print "Done."
    for (pack, file) in p.getPackageList().items():
        print "Bundle is mapped to file: ", pack, file
