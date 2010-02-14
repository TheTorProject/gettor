#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 packages.py: Package related stuff

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
import gettor.utils
import re

__all__ = ["Packages"]

log = gettor.gtlog.getLogger()

class Packages:
    #                "bundle name": ("single file regex", "split file regex")
    packageRegex = { "tor-browser-bundle": ("tor-browser-.*_en-US.exe$", "tor-browser-.*_en-US_split"),
                     "tor-im-browser-bundle": ("tor-im-browser-.*_en-US.exe$", "tor-im-browser-.*_en-US_split"),
                     "tor-browser-bundle_en": ("tor-browser-.*_en-US.exe$", "tor-browser-.*_en-US_split"),
                     "tor-im-browser-bundle_en": ("tor-im-browser-.*_en-US.exe$", "tor-im-browser-.*_en-US_split"),
                     "tor-browser-bundle_de": ("tor-browser-.*_de.exe$", "tor-browser-.*_de_split"),
                     "tor-im-browser-bundle_de": ("tor-im-browser-.*_de.exe$", "tor-im-browser-.*_de_split"),
                     "tor-browser-bundle_ar": ("tor-browser-.*_ar.exe$", "tor-browser-.*_ar_split"),
                     "tor-im-browser-bundle_ar": ("tor-im-browser-.*_ar.exe$", "tor-im-browser-.*_ar_split"),
                     "tor-browser-bundle_es": ("tor-browser-.*_es-ES.exe$", "tor-browser-.*_es-ES_split"),
                     "tor-im-browser-bundle_es": ("tor-im-browser-.*_es-ES.exe$", "tor-im-browser-.*_es-ES_split"),
                     "tor-browser-bundle_fa": ("tor-browser-.*_fa-IR.exe$", "tor-browser-.*_fa-IR_split"),
                     "tor-im-browser-bundle_fa": ("tor-im-browser-.*_fa-IR.exe$", "tor-im-browser-.*_fa-IR_split"),
                     "tor-browser-bundle_fr": ("tor-browser-.*_fr.exe$", "tor-browser-.*_fr_split"),
                     "tor-im-browser-bundle_fr": ("tor-im-browser-.*_fr.exe$", "tor-im-browser-.*_fr_split"),
                     "tor-browser-bundle_it": ("tor-browser-.*_it.exe$", "tor-browser-.*_it_split"),
                     "tor-im-browser-bundle_it": ("tor-im-browser-.*_it.exe$", "tor-im-browser-.*_it_split"),
                     "tor-browser-bundle_nl": ("tor-browser-.*_nl.exe$", "tor-browser-.*_nl_split"),
                     "tor-im-browser-bundle_nl": ("tor-im-browser-.*_nl.exe$", "tor-im-browser-.*_nl_split"),
                     "tor-browser-bundle_pl": ("tor-browser-.*_pl.exe$", "tor-browser-.*_pl_split"),
                     "tor-im-browser-bundle_pl": ("tor-im-browser-.*_pl.exe$", "tor-im-browser-.*_pl_split"),
                     "tor-browser-bundle_pt": ("tor-browser-.*_pt.exe$", "tor-browser-.*_pt_split"),
                     "tor-im-browser-bundle_pt": ("tor-im-browser-.*_pt.exe$", "tor-im-browser-.*_pt_split"),
                     "tor-browser-bundle_ru": ("tor-browser-.*_ru.exe$", "tor-browser-.*_ru_split"),
                     "tor-im-browser-bundle_ru": ("tor-im-browser-.*_ru.exe$", "tor-im-browser-.*_ru_split"),
                     "tor-browser-bundle_zh_CN": ("tor-browser-.*_zh-CN.exe$", "tor-browser-.*_zh-CN_split"),
                     "tor-im-browser-bundle_zh_CN": ("tor-im-browser-.*_zh-CN.exe$", "tor-im-browser-.*_zh-CN_split"),
                     "source-bundle": ("tor-.*.tar.gz$", "Now to something completely different"),
                     "windows-bundle": ("vidalia-bundle-.*.exe$", "vidalia-bundle-.*_split"),
                     "macosx-ppc-bundle": ("vidalia-bundle-.*-ppc.dmg$", "vidalia-bundle-.*-ppc_split"),
                     "macosx-i386-bundle": ("vidalia-bundle-.*-i386.dmg$", "vidalia-bundle-.*-universal_split"),
                     # Mike won't sign Torbutton; He doesn't get gettor support
                     #"torbutton": "torbutton-current.xpi$",
                   }

    def __init__(self, config, mirror="rsync.torproject.org", silent=False):
        self.packageList = {}
        self.distDir = config.getDistDir()
        self.initRsync(mirror, silent)
        try:
            entry = os.stat(self.distDir)
        except OSError, e:
            if not gettor.utils.createDir(self.distDir):
                log.error("Bad dist dir %s: %s" % (self.distDir, e))
                raise IOError
        self.packDir = config.getPackDir()
        try:
            entry = os.stat(self.packDir)
        except OSError, e:
            if not gettor.utils.createDir(self.packDir):
                log.error("Bad pack dir %s: %s" % (self.packDir, e))
                raise IOError

    def getPackageList(self):
        # Build dict like 'name': 'name.z'
        try:
            for filename in os.listdir(self.packDir):
                self.packageList[filename[:-2]] = os.path.join(self.packDir, filename)
        except OSError, (strerror):
            log.error("Failed to build package list: %s" % strerror)
            return None

        # Check sanity
        for key, val in self.packageList.items():
            # Remove invalid packages
            if not os.access(val, os.R_OK):
                log.info("Warning: %s not accessable. Removing from list." \
                            % val)
                del self.packageList[key]
        return self.packageList

    def buildPackages(self):
        for (pack, (regex_single, regex_split)) in self.packageRegex.items():
            for dirname in os.listdir(self.distDir):
                subdir = os.path.join(self.distDir, dirname)
                # Ignore non-dir directory members and non-gettor dirs
                if not os.path.isdir(subdir) or not dirname.startswith("_"):
                    continue
                for filename in os.listdir(subdir):
                    # Splitfile hacks. XXX: Refactor
                    if re.compile(regex_split).match(filename):
                        if not self.buildSplitFiles(pack, subdir, filename):
                            log.error("Could not build split files packages")
                            return False
                    if re.compile(regex_single).match(filename):
                        file = os.path.join(subdir, filename)
                        ascfile = file + ".asc"
                        zpack = pack + ".z"
                        zipFileName  = os.path.join(self.packDir, zpack)
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
            log.error("Failed to build packages")
            return False

    def buildSplitFiles(self, pack, dirname, filename):
        log.info("Building split files..")
        packSplitDir = None
        try:
            splitpack = pack + ".split"
            packSplitDir = os.path.join(self.packDir, splitpack)
            if not os.access(packSplitDir, os.R_OK):
                os.mkdir(packSplitDir)
        except OSError, e:
            log.error("Could not create dir %s: %s" \
                            % (packSplitDir, e))
        # Loop through split dir, look if every partXX.ZZZ has a 
        # matching signature, pack them together in a .z
        splitdir = os.path.join(dirname, filename)
        for splitfile in os.listdir(splitdir):
            # Skip signature files
            if splitfile.endswith(".asc"):
                continue
            if re.compile(".*split.part.*").match(splitfile):
                ascsplit = splitfile + ".asc"
                ascfile = os.path.join(splitdir, "signatures", ascsplit)
                # Rename .exe if needed
                if gettor.utils.hasExe(ascfile):
                    try:
                        ascfile = gettor.utils.renameExe(ascfile)
                    except:
                        log.error("Could not rename exe file")
                file = os.path.join(splitdir, splitfile)
                if gettor.utils.hasExe(file):
                    try:
                        file = gettor.utils.renameExe(file)
                    except:
                        log.error("Could not rename exe file")
                zsplitfile = splitfile + ".z"
                zipFileName = os.path.join(packSplitDir, zsplitfile)
                if gettor.utils.hasExe(zipFileName):
                    try:
                        zipFileName = gettor.utils.renameExe(zipFileName, False)
                    except:
                        log.error("Could not rename zip file exe")
                        return False
                if os.access(ascfile, os.R_OK) and os.access(file, os.R_OK):
                    zip = zipfile.ZipFile(zipFileName, "w")
                    zip.write(file, os.path.basename(file))
                    zip.write(ascfile, os.path.basename(ascfile))
                    zip.close()
                else:
                    log.error("Uhm, expected signature file for %s to be: %s" % (file, ascfile))

        log.info("Done.")
        return True

    def initRsync(self, mirror="rsync.torproject.org", silent=False):
        # Rsync command 1
        self.rsync = "rsync -a" 
        self.rsync += " "
        self.rsync += "--delete"
        self.rsync += " "
        self.rsync += "--exclude='*current*'"
        self.rsync += " "
        self.rsync += "--exclude='*osx*'"
        self.rsync += " "
        self.rsync += "--exclude='*rpm*'"
        self.rsync += " "
        self.rsync += "--exclude='*privoxy*'"
        self.rsync += " "
        self.rsync += "--exclude='*alpha*'"
        self.rsync += " "
        self.rsync += "--exclude='*vidalia-bundles*'"
        self.rsync += " "
        if not silent:
            self.rsync += "--progress"
            self.rsync += " "
        self.rsync += "rsync://%s/tor/dist/" % mirror
        self.rsync += " "
        self.rsync += self.distDir + "_source"
        self.rsync += " "
        self.rsync += "&&"
        self.rsync += " "
        # Rsync command 2
        self.rsync += "rsync -a"
        self.rsync += " "
        self.rsync += "--delete"
        self.rsync += " "
        self.rsync += "--exclude='*current*'"
        self.rsync += " "
        self.rsync += "--exclude='*osx*'"
        self.rsync += " "
        self.rsync += "--exclude='*rpm*'"
        self.rsync += " "
        self.rsync += "--exclude='*privoxy*'"
        self.rsync += " "
        self.rsync += "--exclude='*alpha*'"
        self.rsync += " "
        self.rsync += "--exclude='*vidalia-bundles*'"
        self.rsync += " "
        if not silent:
            self.rsync += "--progress"
            self.rsync += " "
        self.rsync += "rsync://%s/tor/torbrowser/dist/" % mirror
        self.rsync += " "
        self.rsync += self.distDir + "_tbb"
        self.rsync += " "
        self.rsync += "&&"
        self.rsync += " "
        # Rsync command 3
        self.rsync += "rsync -a"
        self.rsync += " "
        self.rsync += "--delete"
        self.rsync += " "
        self.rsync += "--exclude='*alpha*'"
        self.rsync += " "
        if not silent:
            self.rsync += "--progress"
            self.rsync += " "
        self.rsync += "rsync://%s/tor/dist/vidalia-bundles/" % mirror
        self.rsync += " "
        self.rsync += self.distDir + "_vidalia"
        self.rsync += " "

    def syncWithMirror(self):
        process = subprocess.Popen(self.rsync, shell=True)
        process.wait()

        return process.returncode

    def getCommandToStr(self, mirror, silent):
        """This is useful for cronjob installations
        """
        return self.rsync

