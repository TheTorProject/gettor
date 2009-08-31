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

# XXX
def createDir(path):
    try:
        log.info("Creating directory %s.." % path)
        os.makedirs(path)
    except OSError, e:
        log.error("Failed to create directory %s: %s" % (path, e))
        return False
    return True

class gettorPackages:
    #                "bundle name": ("single file regex", "split file regex")
    packageRegex = { "windows-bundle": ("vidalia-bundle-.*.exe$", "vidalia-bundle-.*_split$"),
                     "panther-bundle": ("vidalia-bundle-.*-ppc.dmg$", "vidalia-bundle-.*-ppc_split$"),
                     "macosx-universal-bundle": ("vidalia-bundle-.*-universal.dmg$", "vidalia-bundle-.*-universal_split$"),
                     "source-bundle": ("tor-.*.tar.gz$", "none"),
                     "tor-browser-bundle": ("tor-browser-.*_en-US.exe$", "tor-browser-.*_en-US_split$"),
                     "tor-im-browser-bundle": ("tor-im-browser-.*_en-US.exe$", "tor-im-browser-.*_en-US_split$"),
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
            if not createDir(self.Distdir):
                log.error("Bad dist dir %s: %s" % (self.distDir, e))
                raise IOError
        self.packDir = config.getPackDir()
        try:
            entry = os.stat(self.packDir)
        except OSError, e:
            if not createDir(self.packDir):
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
            for (pack, (regex_single, regex_split)) in self.packageRegex.items():
                # Splitfile hacks. XXX: Refactor
                if re.compile(regex_split).match(filename):
                    packSplitDir = None
                    try:
                        packSplitDir = self.packDir + "/" + pack + ".split"
                        if not os.access(packSplitDir, os.R_OK):
                            os.mkdir(packSplitDir)
                    except OSError, e:
                        log.error(_("Could not create dir %s: %s" % (packSplitDir, e)))
                    # Loop through split dir, look if every partXX.ZZZ has a matching signature,
                    # pack them together in a .z
                    splitdir = self.distDir + "/" + filename
                    for splitfile in os.listdir(splitdir):
                        if re.compile(".*split.part.*").match(splitfile):
                            ascfile = splitdir + "/signatures/" + splitfile + ".asc"
                            file = splitdir + "/" + splitfile
                            zipFileName = packSplitDir + "/" + splitfile + ".z"
                            if os.access(ascfile, os.R_OK) and os.access(file, os.R_OK):
                                print "ok: ", zipFileName
                                zip = zipfile.ZipFile(zipFileName, "w")
                                zip.write(splitdir + "/" + splitfile, os.path.basename(file))
                                zip.write(ascfile, os.path.basename(ascfile))
                                zip.close()
                            else:
                                log.error(_("Uhm, no signature for %s found" % splitfile))
                                return False
                if re.compile(regex_single).match(filename):
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
