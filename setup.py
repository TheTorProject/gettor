#!/usr/bin/python2.5
# (c) 2009 The Tor project
# GetTor installer & packer

from distutils.core import setup

setup(name='GetTor',
      version='0.1',
      description='GetTor enables users to obtain Tor via email',
      author='Jacob Appelbaum, Christian Fromme',
      author_email='jacob at appelbaum dot net, kaner at strace dot org',
      url='https://www.torpeoject.org/gettor/',
      package_dir={'': '.'},
      packages=['gettor'],
      py_modules=['GetTor']
     )
