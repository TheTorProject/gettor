# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

import os
import shutil
import zipfile
import subprocess
import logging
import gettor.config
import gettor.utils
import re
import glob

# Stolen from Mike's TorCtl:
class RouterVersion:
  """ Represents a Router's version. Overloads all comparison operators
      to check for newer, older, or equivalent versions. """
  def __init__(self, version):
    if version:
      v = re.search("(\d+)\.(\d+)\.(\d+)\.(\d+)", version).groups()
      self.version = int(v[0])*0x1000000 + int(v[1])*0x10000 + int(v[2])*0x100 + int(v[3])
      self.ver_string = version
    else:
      self.version = version
      self.ver_string = "unknown"

  def __lt__(self, other): return self.version < other.version
  def __gt__(self, other): return self.version > other.version
  def __ge__(self, other): return self.version >= other.version
  def __le__(self, other): return self.version <= other.version
  def __eq__(self, other): return self.version == other.version
  def __ne__(self, other): return self.version != other.version
  def __str__(self): return self.ver_string

class TBBVersion:
  """ Represents a TBB's version. Overloads all comparison operators
      to check for newer, older, or equivalent versions. """
  def __init__(self, version):
    if version:
      v = re.search("(\d+)\.(\d+)\.(\d+)", version).groups()
      self.version = int(v[0])*0x10000 + int(v[1])*0x100 + int(v[2])
      self.ver_string = version
    else:
      self.version = version
      self.ver_string = "unknown"

  def __lt__(self, other): return self.version < other.version
  def __gt__(self, other): return self.version > other.version
  def __ge__(self, other): return self.version >= other.version
  def __le__(self, other): return self.version <= other.version
  def __eq__(self, other): return self.version == other.version
  def __ne__(self, other): return self.version != other.version
  def __str__(self): return self.ver_string


class Packages:

    def __init__(self, config, silent=False):
        self.packageList = {}
        self.distDir = os.path.join(config.BASEDIR, "dist")
        self.packDir = os.path.join(config.BASEDIR, "packages")
        self.initRsync(config.RSYNC_MIRROR, silent)
        self.packageList = config.PACKAGES

        # Create distdir and packdir if necessary
        gettor.utils.createDir(self.distDir)
        gettor.utils.createDir(self.packDir)

    def getDistFileFromRegex(self, regex):
        """Do a quick check whether a given regex matches a real file on the
           file system. If it does, return the full path.
        """
        fileName = os.path.join(self.distDir, regex)
        fileList = glob.glob(fileName)
        if len(fileList) != 1:
            # Looks like we have more than one file to choose from. Great. 
            # Let's do some more or less intelligent tricks.

            # Remove all alphas
            fileList = gettor.utils.removeFromListByRegex(fileList, "-alpha")
            if len(fileList) == 1:
                return fileList[0]

            # Remove all betas
            fileList = gettor.utils.removeFromListByRegex(fileList, "-beta")
            if len(fileList) == 1:
                return fileList[0]

            # Remove all release candidates
            fileList = gettor.utils.removeFromListByRegex(fileList, "-rc")
            if len(fileList) == 1:
                return fileList[0]

            # Still more than 1 file? Look at the version strings.
            r = RouterVersion("0.0.0.0")
            ret = None
            for f in fileList:
                try:
                    if RouterVersion(f) > r:
                        r = RouterVersion(f)
                        ret = f
                except:
                    return ""

            if ret is not None:
                logging.debug("Of the list %s, I return %s" % (fileList, ret))
                return ret

            # Still no result? Sort by TBB versions
            r = TBBVersion("0.0.0")
            ret = None
            for f in fileList:
                try:
                    if TBBVersion(f) > r:
                        r = TBBVersion(f)
                        ret = f
                except:
                    return ""

            if ret is not None:
                logging.debug("Of the list %s, I return %s" % (fileList, ret))
                return ret

            return ""

        return fileList[0]

    def preparePackages(self):
        """Go through the configured package list and make some sanity checks.
           Does the configured file exist? Does the split package exist?
        """
        logging.debug("Checking package configuration..")
        for (pack, (regexSingle, regexSplit)) in self.packageList.items():
            fileSingle = self.getDistFileFromRegex(regexSingle)
            if fileSingle == "":
                logging.error("Can't match `single' for %s" % pack)
                logging.error("Please fix this. I will stop here.")
                return False
            fileSplit = self.getDistFileFromRegex(regexSplit)
            if regexSplit != "unavailable" and fileSplit == "":
                logging.error("Can't match `split' for %s" % pack)
                logging.error("Please fix this. I will stop here.")
                return False
            logging.debug("Ok: %s" % pack)

        logging.debug("Checks passed. Package configuration looks good.")
        return True

    def buildPackages(self):
        """Take all packages in distdir and turn them into GetTor- digestables 
           in the package directory.
        """
        for (pack, (regexSingle, regexSplit)) in self.packageList.items():
            logging.debug("Building package(s) for %s.." % pack)
            singleFile = self.getDistFileFromRegex(regexSingle)
            if not self.buildSinglePackage(pack, singleFile):
                logging.error("Could not build (single) package %s." % pack)
                return False
            if regexSplit != "unavailable":
                splitDir = self.getDistFileFromRegex(regexSplit)
                if not self.buildSplitPackages(pack, splitDir):
                    logging.error("Could not build (split) package %s." % pack)
                    return False

        logging.debug("All packages built successfully.")
        return True

    def buildSinglePackage(self, pack, packFile):
        """Build a zip file from a single file.
        """
        ascFile = packFile + ".asc"
        zipFile = os.path.join(self.packDir, pack + ".z")

        gettor.utils.makeZip(zipFile, [packFile, ascFile])
        logging.debug("Zip file %s created successfully." % zipFile)
        return True

    def buildSplitPackages(self, pack, splitDir):
        """Build several zip files from a directory containing split files
        """

        zipDir = os.path.join(self.packDir, pack + ".split")
        gettor.utils.createDir(zipDir)
        for item in glob.glob(splitDir + "/*.part[0-9][0-9].*.asc"):
            packFile = item.replace(".asc", "")    
            ascFile = item
            zipFileName =  pack + "." + self.getPart(item) + ".z"
            zipFile = os.path.join(zipDir, zipFileName)

            gettor.utils.makeZip(zipFile, [packFile, ascFile])
            logging.debug("Zip file %s created successfully." % zipFile)

        logging.debug("All split files for package %s created." % pack)
        return True

    def getPart(self, fileName):
        """Helper function: Extract the `partXX' part of the file name.
        """
        match = re.match(".*(part[0-9][0-9]).*", fileName)
        if match:
            return match.group(1)

        logging.error("Ugh. No .partXX. part in the filename.")
        return ""

    def initRsync(self, mirror="rsync.torproject.org", silent=False):
        """Build rsync command for fetching packages. This basically means
           'exclude everything we don't want'
        """
        # Rsync command 1
        self.rsync = "rsync -a" 
        self.rsync += " "
        self.rsync += "--delete"
        self.rsync += " "
        self.rsync += "--exclude='*current*'"
        self.rsync += " "
        self.rsync += "--exclude='*rpm*'"
        self.rsync += " "
        self.rsync += "--exclude='*privoxy*'"
        self.rsync += " "
#self.rsync += "--exclude='*alpha*'"
#       self.rsync += " "
        self.rsync += "--exclude='*torbutton*'"
        self.rsync += " "
        # Exclude tor-im bundles for now. Too large. XXX 
        self.rsync += "--exclude='*torbrowser/tor-im*'"
        self.rsync += " "
        self.rsync += "--exclude='*win32*'"
        self.rsync += " "
        self.rsync += "--exclude='*misc*'"
        self.rsync += " "
        if not silent:
            self.rsync += "--progress"
            self.rsync += " "
        self.rsync += "rsync://%s/tor/dist/" % mirror
        self.rsync += " "
        self.rsync += self.distDir + "/"

    def syncWithMirror(self):
        """Actually execute rsync
        """
        process = subprocess.Popen(self.rsync, shell=True)
        process.wait()

        return process.returncode

    def getCommandToStr(self, mirror, silent):
        """This is needed for cronjob installation.
        """
        return self.rsync

