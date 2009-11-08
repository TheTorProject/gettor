#!/usr/bin/python2.5
# (c) 2009 The Tor project
# GetTor installer & packer

import glob
import os
import sys

from distutils.core import setup

TRANSLATION_DIR='i18n'
data_files = dict()
for filename in os.listdir(TRANSLATION_DIR):
    if filename.endswith('.svn'):
        continue
    dir = os.path.join(TRANSLATION_DIR, filename)
    if dir.endswith('templates'):
        file = "gettor.pot"
    else:
        file = "gettor.po"
    pofile = os.path.join(dir, file)
    data_files[dir] = [pofile]

setup(name='GetTor',
      version='0.1',
      description='GetTor enables users to obtain Tor via email',
      author='Jacob Appelbaum, Christian Fromme',
      author_email='jacob at appelbaum dot net, kaner at strace dot org',
      url='https://www.torproject.org/gettor/',
      package_dir={'': 'lib'},
      packages=['gettor'],
      data_files = data_files.items(),
      scripts = ["GetTor.py"],
      py_modules=['GetTor'],
      long_description = """Really long text here."""
     )
