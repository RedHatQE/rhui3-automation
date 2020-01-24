'''Atomic Host Checks'''

from __future__ import print_function

from os.path import basename
import re
import socket

import json
import logging
import nose
import requests
import stitches

logging.basicConfig(level=logging.DEBUG)

AH = "atomiccli.example.com"
try:
    socket.gethostbyname(AH)
    AH_EXISTS = True
except socket.error:
    AH_EXISTS = False
AH_CON = stitches.Connection(AH, "root", "/root/.ssh/id_rsa_test")
DOC = "https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_atomic_host/" + \
      "7/html/release_notes/overview"
VERSION_STRING = "page-next.*Red Hat Enterprise Linux Atomic Host ([0-9.]*)"

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_check_version():
    '''
       check if the Atomic host is running the latest documented version
    '''
    if not AH_EXISTS:
        raise nose.exc.SkipTest("No known Atomic host")

    # find the latest version in the docs
    page = requests.get(DOC)
    pattern_object = re.compile(VERSION_STRING)
    match_object = pattern_object.search(page.text)
    expected_version = match_object.group(1)

    # determine the latest version on the Atomic host
    _, stdout, _ = AH_CON.exec_command("atomic host status -j")
    ah_data = json.load(stdout)
    actual_version = ah_data["deployments"][0]["version"]
    # sometimes a respin is made and then another element is added to the version
    # (e.g. 7.7.1.1)
    # use only the first three elements if so; respins aren't documented
    version_numbers = actual_version.split(".")
    if len(version_numbers) > 3:
        actual_version = ".".join(version_numbers[:3])

    # compare the versions
    nose.tools.eq_(expected_version, actual_version)

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
