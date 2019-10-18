'''Tests for RHUI 3 repos and EUS listings'''

from __future__ import print_function

from os.path import basename
import re

import logging
import nose
import stitches
from stitches.expect import Expect

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def _check_rpms():
    '''
        helper method to check if the RHUI repository contains enough RPMs
        and if "rh-rhui-tools" is included (the main package and -libs, all released versions)
    '''
    cmd = "wget -q -O - " + \
          "--certificate /tmp/extra_rhui_files/rhcert.pem " + \
          "--ca-certificate /etc/rhsm/ca/redhat-uep.pem " + \
          "https://cdn.redhat.com/" + \
          "content/dist/rhel/rhui/server/7/7Server/x86_64/rhui/3/os/repodata/"

    rpm_link_pattern = r'href="[^"]+\.rpm'
    min_count = 150
    # first fetch repodata
    _, stdout, _ = CONNECTION.exec_command(cmd + "repomd.xml")
    with stdout as output:
        repomd_xml = output.read().decode()
        primary_xml_gz_path = re.findall("[0-9a-f]+-primary.xml.gz", repomd_xml)[0]
    # now fetch package info, uncompressed & filtered on the RHUA, paths on separate lines
    # (not fetching the compressed or uncompressed data as it's not decode()able)
    _, stdout, _ = CONNECTION.exec_command(cmd + primary_xml_gz_path +
                                           " | zegrep -o '%s'" % rpm_link_pattern +
                                           " | sed 's/href=\"//'")
    with stdout as output:
        rpm_paths = output.read().decode().splitlines()
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
    _, stdout, _ = CONNECTION.exec_command(cmd)
    with stdout as output:
        listings_actual = output.read().decode().splitlines()
    nose.tools.eq_(listings_expected, listings_actual)

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_install_wget():
    '''
        make sure wget is installed on the RHUA
    '''
    Expect.expect_retval(CONNECTION, "yum -y install wget", timeout=30)

def test_02_rhui_3_for_rhel_7_check():
    '''
        check if the RHUI 3 packages for RHEL 7 are available
    '''
    _check_rpms()

def test_03_eus_6_repos_check():
    '''
        check if all supported RHEL 6 EUS versions are available
    '''
    # RHEL 6.1-6.7
    _check_listing(6, 1, 7)

def test_04_eus_7_repos_check():
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
