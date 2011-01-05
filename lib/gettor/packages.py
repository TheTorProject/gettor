#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 Copyright (c) 2008, Jacob Appelbaum <jacob@appelbaum.net>, 
                     Christian Fromme <kaner@strace.org>

 This is Free Software. See LICENSE for license information.
'''

import os
import shutil
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
                     "tor-browser-bundle_fa": ("tor-browser-.*_fa.exe$", "tor-browser-.*_fa_split"),
                     "tor-im-browser-bundle_fa": ("tor-im-browser-.*_fa.exe$", "tor-im-browser-.*_fa_split"),
                     "tor-browser-bundle_fr": ("tor-browser-.*_fr.exe$", "tor-browser-.*_fr_split"),
                     "tor-im-browser-bundle_fr": ("tor-im-browser-.*_fr.exe$", "tor-im-browser-.*_fr_split"),
                     "tor-browser-bundle_it": ("tor-browser-.*_it.exe$", "tor-browser-.*_it_split"),
                     "tor-im-browser-bundle_it": ("tor-im-browser-.*_it.exe$", "tor-im-browser-.*_it_split"),
                     "tor-browser-bundle_nl": ("tor-browser-.*_nl.exe$", "tor-browser-.*_nl_split"),
                     "tor-im-browser-bundle_nl": ("tor-im-browser-.*_nl.exe$", "tor-im-browser-.*_nl_split"),
                     "tor-browser-bundle_pl": ("tor-browser-.*_pl.exe$", "tor-browser-.*_pl_split"),
                     "tor-im-browser-bundle_pl": ("tor-im-browser-.*_pl.exe$", "tor-im-browser-.*_pl_split"),
                     "tor-browser-bundle_pt": ("tor-browser-.*_pt-PT.exe$", "tor-browser-.*_pt-PT_split"),
                     "tor-im-browser-bundle_pt": ("tor-im-browser-.*_pt-PT.exe$", "tor-im-browser-.*_pt-PT_split"),
                     "tor-browser-bundle_ru": ("tor-browser-.*_ru.exe$", "tor-browser-.*_ru_split"),
                     "tor-im-browser-bundle_ru": ("tor-im-browser-.*_ru.exe$", "tor-im-browser-.*_ru_split"),
                     "tor-browser-bundle_zh_CN": ("tor-browser-.*_zh-CN.exe$", "tor-browser-.*_zh-CN_split"),
                     "tor-im-browser-bundle_zh_CN": ("tor-im-browser-.*_zh-CN.exe$", "tor-im-browser-.*_zh-CN_split"),
                     "source-bundle": ("tor-.*.tar.gz$", "Now to something completely different"),
                     "windows-bundle": ("vidalia-bundle-.*.exe$", "vidalia-bundle-.*_split"),
                     "macosx-ppc-bundle": ("vidalia-bundle-.*-ppc.dmg$", "vidalia-bundle-.*-ppc_split"),
                     "macosx-i386-bundle": ("vidalia-bundle-.*-i386.dmg$", "vidalia-bundle-.*-universal_split"),
                     "linux-browser-bundle-i386": ("tor-browser-gnu-linux-i686-.*-en-US.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_en": ("tor-browser-gnu-linux-i686-.*-en-US.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_ar": ("tor-browser-gnu-linux-i686-.*-ar.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_de": ("tor-browser-gnu-linux-i686-.*-de.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_es-ES": ("tor-browser-gnu-linux-i686-.*-es-ES.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_fa": ("tor-browser-gnu-linux-i686-.*-fa.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_fr": ("tor-browser-gnu-linux-i686-.*-fr.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_it": ("tor-browser-gnu-linux-i686-.*-it.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_nl": ("tor-browser-gnu-linux-i686-.*-nl.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_pl": ("tor-browser-gnu-linux-i686-.*-pl.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_pt_PT": ("tor-browser-gnu-linux-i686-.*-pt_PT.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_ru": ("tor-browser-gnu-linux-i686-.*-ru.tar.gz$", "not available"),
                     "linux-browser-bundle-i386_zh_CN": ("tor-browser-gnu-linux-i686-.*-zh-CN.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64": ("tor-browser-gnu-linux-x86_64-.*-en-US.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_en": ("tor-browser-gnu-linux-x86_64-.*-en-US.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_ar": ("tor-browser-gnu-linux-x86_64-.*-ar.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_de": ("tor-browser-gnu-linux-x86_64-.*-de.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_es-ES": ("tor-browser-gnu-linux-x86_64-.*-es-ES.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_fa": ("tor-browser-gnu-linux-x86_64-.*-fa.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_fr": ("tor-browser-gnu-linux-x86_64-.*-fr.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_it": ("tor-browser-gnu-linux-x86_64-.*-it.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_nl": ("tor-browser-gnu-linux-x86_64-.*-nl.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_pl": ("tor-browser-gnu-linux-x86_64-.*-pl.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_pt_PT": ("tor-browser-gnu-linux-x86_64-.*-pt_PT.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_ru": ("tor-browser-gnu-linux-x86_64-.*-ru.tar.gz$", "not available"),
                     "linux-browser-bundle-x86_64_zh_CN": ("tor-browser-gnu-linux-x86_64-.*-zh-CN.tar.gz$", "not available"),
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
        """Build dict like 'name': 'name.z'
        """
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

    def preparePackages(self):
        """Move some stuff around the way we need it: GetTor expects a flat
           file system after rsync is finished   
        """
        log.info("Preparing Linux Bundles..")
        # Prepare Linux Bundles: Move them from linux/i386/* to 
        # ./i386-* and from linux/x86_64/* to ./x86_64-*
        tbbdir = os.path.join(self.distDir, "_tbb")
        lxdir = os.path.join(tbbdir, "linux")
        if os.path.isdir(lxdir):
            # Loop through linux/i386 and linux/x86_64 and whatever might
            # come in the future
            for archdir in os.listdir(lxdir):
                lxarchdir = os.path.join(lxdir, archdir)
                for srcfile in os.listdir(lxarchdir):
                    renameTo = archdir + "-" + srcfile
                    destfile = os.path.join(tbbdir, renameTo)
                    shutil.move(os.path.join(lxarchdir, srcfile), destfile)

    def buildPackages(self):
        """Action! Take all packages in distdir and turn them into GetTor-
           digestables in packdir
        """
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
        if len(self.packageList) > 0:
            return True
        else:
            log.error("Failed to build packages")
            return False

    def buildSplitFiles(self, pack, dirname, filename):
        """Build split file packages
        """
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
                ascfile = os.path.join(splitdir, ascsplit)
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
                match = re.match(".*(part[0-9][0-9].*$)", splitfile)
                if match:
                    partNo = match.group(1)
                else:
                    log.error("Can't happen: No part string in %s" % splitfile)
                    continue
                zsplitfile = pack + "." + partNo + ".z"
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

        return True

    def initRsync(self, mirror="rsync.torproject.org", silent=False):
        """Build rsync command for fetching packages
        """
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
        self.rsync += "--exclude='*vidalia*'"
        self.rsync += " "
        self.rsync += "--exclude='*torbrowser*'"
        self.rsync += " "
        self.rsync += "--exclude='*torbutton*'"
        self.rsync += " "
        self.rsync += "--exclude='*win32*'"
        self.rsync += " "
        self.rsync += "--exclude='*android*'"
        self.rsync += " "
        self.rsync += "--exclude='*misc*'"
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
        self.rsync += "rsync://%s/tor/dist/torbrowser/" % mirror
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
        """Actually execute rsync
        """
        process = subprocess.Popen(self.rsync, shell=True)
        process.wait()

        return process.returncode

    def getCommandToStr(self, mirror, silent):
        """This is useful for cronjob installations
        """
        return self.rsync

