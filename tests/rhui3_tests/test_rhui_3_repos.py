'''Tests for RHUI 3 repos and EUS listings'''

from __future__ import print_function

from os.path import basename
import re

import logging
import nose
from stitches.expect import Expect
import requests

from rhui3_tests_lib.conmgr import ConMgr

logging.basicConfig(level=logging.DEBUG)

RHUA = ConMgr.connect()

DOC = "https://access.redhat.com/documentation/en-us/red_hat_update_infrastructure/3.1/html/" + \
      "release_notes/rn_updates"
VERSION_STRING = "Updates for Red Hat Update Infrastructure [0-9.]+"

def _check_rpms():
    '''
        helper method to check if the RHUI repository contains enough RPMs
        and if "rh-rhui-tools" is included (the main package and -libs, all released versions)
    '''
    cmd = "wget -q -O - " + \
          "--certificate /tmp/extra_rhui_files/rhcert.pem " + \
          "--ca-certificate /etc/rhsm/ca/redhat-uep.pem " + \
          "https://cdn.redhat.com/" + \
          "content/dist/rhel/rhui/server/7/7Server/x86_64/rhui/3/os/"

    rpm_link_pattern = r'href="[^"]+\.rpm'
    min_count = 150
    # first fetch repodata
    _, stdout, _ = RHUA.exec_command(cmd + "repodata/repomd.xml")
    repomd_xml = stdout.read().decode()
    primary_xml_gz_path = re.findall("[0-9a-f]+-primary.xml.gz", repomd_xml)[0]
    # now fetch package info, uncompressed & filtered on the RHUA, paths on separate lines
    # (not fetching the compressed or uncompressed data as it's not decode()able)
    _, stdout, _ = RHUA.exec_command(cmd + "repodata/" + primary_xml_gz_path +
                                     " | zegrep -o '%s'" % rpm_link_pattern +
                                     " | sed 's/href=\"//'")
    rpm_paths = stdout.read().decode().splitlines()
    # get just package file names
    rpms = [basename(rpm) for rpm in rpm_paths]
    # check the number of RPMs
    rpms_count = len(rpms)
    error_msg = "Not enough RPMs. Expected at least %s, found " % min_count
    if rpms_count == 0:
        error_msg += "none."
    else:
        error_msg += "the following %s: %s." % (rpms_count, str(rpms))
    nose.tools.ok_(rpms_count >= min_count, msg=error_msg)
    rhui_tools_rpms = [rpm for rpm in rpms if rpm.startswith("rh-rhui-tools")]
    nose.tools.ok_(rhui_tools_rpms, msg="rh-rhui-tools*: no such link")
    # check if the latest version in the repo is the latest documented one
    rhui_tools_rpms.sort()
    latest_rhui_rpm_in_repo = rhui_tools_rpms[-1]
    latest_documented_title = re.findall(VERSION_STRING, requests.get(DOC).text)[-1]
    nose.tools.eq_(latest_rhui_rpm_in_repo.rsplit('-', 2)[1], latest_documented_title.split()[-1])
    # can the latest version actually be fetched?
    Expect.expect_retval(RHUA,
                         cmd.replace("-q -O -", "-O /dev/null") +
                         "Packages/r/" +
                         latest_rhui_rpm_in_repo)

def _check_listing(major, min_eus, max_eus):
    '''
        helper method to check if the listings file for the given EUS version is complete
        major: RHEL X version to check
        min_eus: expected min RHEL (X.)Y version
        max_eus: expected max RHEL (X.)Y version
        for lists of X.Y versions in EUS, see:
        https://access.redhat.com/support/policy/updates/errata/#Extended_Update_Support
    '''
    cmd = "wget -q -O - " + \
          "--certificate /tmp/extra_rhui_files/rhcert.pem " + \
          "--ca-certificate /etc/rhsm/ca/redhat-uep.pem " + \
          "https://cdn.redhat.com/" + \
          "content/eus/rhel/rhui/server/%s/listing" % major
    listings_expected = [str(major + i * .1) for i in range(min_eus, max_eus + 1)]
    listings_expected.append("%sServer" % major)
    _, stdout, _ = RHUA.exec_command(cmd)
    listings_actual = stdout.read().decode().splitlines()
    nose.tools.eq_(listings_expected, listings_actual)

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_rhui_3_for_rhel_7_check():
    '''
        check if the RHUI 3 packages for RHEL 7 are available
    '''
    _check_rpms()

def test_02_eus_6_repos_check():
    '''
        check if all supported RHEL 6 EUS versions are available
    '''
    # RHEL 6.1-6.7
    _check_listing(6, 1, 7)

def test_03_eus_7_repos_check():
    '''
        check if all supported RHEL 7 EUS versions are available
    '''
    # RHEL 7.1-7.7
    _check_listing(7, 1, 7)

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
