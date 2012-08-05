#!/usr/bin/python2.5
# (c) 2009 The Tor project
# GetTor installer & packer

import glob
import os
import sys
import subprocess

from distutils.core import setup, Command
from distutils.command.install_data import install_data as _install_data


CONFIG_DEFAULTS = {
   'BASEDIR':  "~/",
}

class Config:
    """A copy of `lib/gettor/config.py'. This is a hack. We need it here 
       because otherwise we cannot know where the user wants his i18n dir to be.
    """
    def __init__(self, path = os.path.expanduser("~/.gettor.conf")):
       """Most of the work happens here. Parse config, merge with default 
          values, prepare outConf.
       """

       self.useConf = {}
       configFile = os.path.expanduser(path)
       execfile(configFile, self.useConf)
       self.__dict__.update(self.useConf)
       self.setMissing()

    def setMissing(self):
       for k,v in CONFIG_DEFAULTS.items():
          if not hasattr(self, k):
             setattr(self,k,v)

class createTrans(Command):
    # Based on setup.py from 
    # http://wiki.maemo.org/Internationalize_a_Python_application
    description = "Install necessary translation files"
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        po_dir = os.path.join(os.path.dirname(os.curdir), 'i18n')
        for path, dirnames, filenames in os.walk(po_dir):
            for d in dirnames:
                if d.endswith("templates"):
                    continue
                # Skip dot files
                if d.startswith("."):
                    continue
                src = os.path.join('i18n', d, "gettor.po")
                lang = d
                dest_path = os.path.join('build', 'locale', lang, 'LC_MESSAGES')
                dest = os.path.join(dest_path, 'gettor.mo')
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
                if not os.path.exists(dest):
                    print 'Compiling %s' % src
                    self.msgfmt(src, dest)
                else:
                    src_mtime = os.stat(src)[8]
                    dest_mtime = os.stat(dest)[8]
                    if src_mtime > dest_mtime:
                        print 'Compiling %s' % src
                        self.msgfmt(src, dest)
    def msgfmt(self, src, dest):
        args = src + " -f -o " + dest
        try:
            ret = subprocess.call("msgfmt" + " " + args, shell=True)
            if ret < 0:
                print 'Error in msgfmt execution: %s' % ret
        except OSError, e:
            print 'Comilation failed: ' % e

class installData(_install_data):
    def run(self):
        self.data_files = []
        config = Config()
        for lang in os.listdir(os.path.join("build", "locale")):
            if lang.endswith('templates'):
                continue
            # Ignore dotfiles
            if lang.startswith('.'):
                continue
            basedirExpand = os.path.expanduser(config.BASEDIR)
            lang_dir = os.path.join(basedirExpand, 'share', 'i18n', lang, 
                                    'LC_MESSAGES')
            lang_file = os.path.join('build', 'locale', lang, 'LC_MESSAGES',
                                     'gettor.mo')
            self.data_files.append( (lang_dir, [lang_file]) )
        _install_data.run(self)

setup(name='GetTor',
      version='0.1',
      description='GetTor enables users to obtain Tor via email',
      author='Jacob Appelbaum, Christian Fromme',
      author_email='jacob at appelbaum dot net, kaner at strace dot org',
      url='https://www.torproject.org/gettor/',
      package_dir={'': 'lib'},
      packages=['gettor'],
      scripts = ["GetTor.py", "MakeStat.py", "PlotStat.py"],
      py_modules=['GetTor'],
      long_description = """Really long text here.""",
      cmdclass={'trans': createTrans,
                'install_data': installData}

     )
