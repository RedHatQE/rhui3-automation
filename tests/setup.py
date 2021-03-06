#!/usr/bin/env python
'''
   Setup file for the rhui3-automation test suite.
   Use "pip install ." in this directory to install the test suite and its dependencies.
'''

from glob import glob

from setuptools import setup

REQUIREMENTS = ['nose', 'pytoml', 'requests', 'stitches', 'xmltodict']

DATAFILES = [('share/rhui3_tests_lib/rhui3_tests', glob('rhui3_tests/test_*.py')),
             ('/etc/rhui3_tests/', ['rhui3_tests/tested_repos.yaml']),
             ('/etc/bash_completion.d/', ['bash_completion/rhuitests'])]

setup(name='rhui3_tests_lib',
      version='1.0',
      description='RHUI 3 Testing Library',
      long_description='libraries to control the rhui-manager UI and facilitate other useful tasks',
      author='RHUI QE Team',
      author_email='noreply@redhat.com',
      platforms='Linux',
      url='https://github.com/RedHatQE/rhui3-automation',
      license="GPLv3+",
      packages=[
          'rhui3_tests_lib'
      ],
      data_files=DATAFILES,
      install_requires=REQUIREMENTS,
      zip_safe=False,
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Operating System :: POSIX',
          'Intended Audience :: Developers',
          'Development Status :: 5 - Production/Stable'
      ],
      scripts=glob('scripts/*')
     )
