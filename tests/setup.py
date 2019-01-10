#!/usr/bin/env python
'''
   Setup file for the rhui3-automation test suite.
   Use "pip install ." in this directory to install the test suite and its dependencies.
'''

from glob import glob
import sys

from setuptools import setup

REQUIREMENTS = ['nose>=1.3.0', 'requests', 'stitches>=0.12']

# Workarounds for packages whose latest versions cannot be installed on RHEL 6
PYTHON_VERSION = sys.version_info[0] + sys.version_info[1] / 10.0
if PYTHON_VERSION <= 2.6:
    REQUIREMENTS.append('paramiko==2.3.1')
    REQUIREMENTS.append('idna==2.7')
    REQUIREMENTS.append('pytoml==0.1.19')
else:
    REQUIREMENTS.append('pytoml')

DATAFILES = [('share/rhui3_tests_lib/rhui3_tests', glob('rhui3_tests/test_*.py')),
             ('share/rhui3_tests_lib/config', ['rhui3_tests/tested_repos.yaml'])]

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
      scripts=glob('scripts/*.py') + glob('scripts/*.sh')
     )
