#!/usr/bin/env python
# -*- coding: utf-8 -*-

from version import get_git_version

try:
  import sys
  reload(sys).setdefaultencoding("UTF-8")
except:
  pass

try:
  from setuptools import setup, find_packages
except ImportError:
  print 'Please install or upgrade setuptools or pip to continue.'
  sys.exit(1)

from version import get_git_version

INSTALL_REQUIRES = ['pandas', 'tables']

setup(name='pynex',
      version = get_git_version(),
      description='Python RINEX utilities',
      license='GPLv3',
      url='http://swiftnav.com',
      author='Swift Navigation Inc.',
      maintainer='Swift Navigation',
      maintainer_email='dev@swift-nav.com',
      packages=find_packages(),
      entry_points={
        'console_scripts': [
          'pynex = pynex.rinex_file:main',
          'ddtool = pynex.dd_tools:main',
      ]
      },
      install_requires=INSTALL_REQUIRES,
      platforms="Linux,Windows,Mac",
      use_2to3=False,
      zip_safe=False
)

