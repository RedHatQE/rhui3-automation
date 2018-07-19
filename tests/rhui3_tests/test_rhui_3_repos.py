''' RHUI 3 RPM availability tests'''

from os.path import basename

import logging
import stitches
from stitches.expect import Expect

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

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

def test_02_rhui_3_for_rhel_6_check():
    '''
        check if the RHUI 3 packages for RHEL 6 are available
    '''
    Expect.expect_retval(CONNECTION,
                         "test $(wget -q -O - " +
                         "--certificate /tmp/extra_rhui_files/rhcert.pem " +
                         "--ca-certificate /etc/rhsm/ca/redhat-uep.pem " +
                         "https://cdn.redhat.com/content/dist/rhel/rhui/server/" +
                         "6/6Server/x86_64/rhui/3/os/Packages/ | " +
                         r"grep -c 'A HREF.*\.rpm') -gt 90",
                         timeout=15)

def test_03_rhui_3_for_rhel_7_check():
    '''
        check if the RHUI 3 packages for RHEL 7 are available
    '''
    Expect.expect_retval(CONNECTION,
                         "test $(wget -q -O - " +
                         "--certificate /tmp/extra_rhui_files/rhcert.pem " +
                         "--ca-certificate /etc/rhsm/ca/redhat-uep.pem " +
                         "https://cdn.redhat.com/content/dist/rhel/rhui/server/" +
                         "7/7Server/x86_64/rhui/3/os/Packages/ | " +
                         r"grep -c 'A HREF.*\.rpm') -gt 90",
                         timeout=15)

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
