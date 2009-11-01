#!/usr/bin/python2.5
# (c) 2009 The Tor project
# GetTor installer & packer

import glob

from distutils.core import setup

setup(name='GetTor',
      version='0.1',
      description='GetTor enables users to obtain Tor via email',
      author='Jacob Appelbaum, Christian Fromme',
      author_email='jacob at appelbaum dot net, kaner at strace dot org',
      url='https://www.torproject.org/gettor/',
      package_dir={'': 'lib'},
      packages=['gettor'],
      scripts = ["GetTor.py"],
      py_modules=['GetTor'],
      long_description = """Really long text here."""
     )
