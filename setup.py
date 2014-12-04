#!/usr/bin/env python

from version import get_git_version

setup_args = dict(
  name = 'pynex',
  version = get_git_version(),
  description = 'Python RINEX utilities',
  license = 'LGPLv3',
  url = 'http://www.swift-nav.com',

  author = 'Swift Navigation Inc.',
  maintainer = 'Fergus Noble',
  maintainer_email = 'fergus@swift-nav.com',

  packages = ['pynex'],

  entry_points = {
    'console_scripts': [
      'pynex = pynex.rinex_file:main',
      'ddtool = pynex.dd_tools:main',
      'ephtool = pynex.eph_tool:main',
    ]
  },

  install_requires = [
    'pandas',
  ],
)

if __name__ == "__main__":
  # Bootstrap Distribute if the user doesn't have it
  from distribute_setup import use_setuptools
  use_setuptools()

  from setuptools import setup

  setup(**setup_args)
