""" Test case for the RHUI SKU and the RHUI 3 repo """

from os.path import basename

import logging
import stitches
from stitches.expect import Expect
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setup():
    '''
        announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_00_update_subman():
    '''
        make sure subscription-manager is up to date
    '''
    Expect.expect_retval(CONNECTION, "yum -y update subscription-manager", timeout=30)

def test_01_register_system():
    '''
        register with RHSM
    '''
    Expect.expect_retval(CONNECTION, "source /tmp/extra_rhui_files/rhaccount.sh && " +
                         "subscription-manager register --type=rhui " +
                         "--username=$SM_USERNAME --password=$SM_PASSWORD",
                         timeout=40)

def test_02_attach_rhui_sku():
    '''
        check if the RHUI SKU is available and attach it if so
    '''
    Expect.expect_retval(CONNECTION, "subscription-manager list --available --matches=RC1116415 " +
                         "--pool-only > /tmp/rhuipool.txt && " +
                         "test -s /tmp/rhuipool.txt && " +
                         "[[ \"$(cat /tmp/rhuipool.txt)\" =~ ^[0-9a-f]+$ ]] && " +
                         "subscription-manager attach --pool=$(< /tmp/rhuipool.txt)",
                         timeout=30)

def test_03_enable_rhui_3_repo():
    '''
        enable the RHUI 3 repo
    '''
    rhel_version = Util.get_rhua_version(CONNECTION)
    # the RHUI 3 for RHEL 6 repo tends to be unavailable with the test account :/ try using beta
    if rhel_version == 6:
        Expect.expect_retval(CONNECTION, "subscription-manager repos " +
                             "--enable=rhel-6-server-rhui-3-rpms || " +
                             "subscription-manager repos --enable=rhel-6-server-rhui-3-beta-rpms",
                             timeout=60)
    else:
        Expect.expect_retval(CONNECTION, "subscription-manager repos --enable=rhel-" +
                             str(rhel_version) + "-server-rhui-3-rpms",
                             timeout=30)

def test_04_unregister_system():
    '''
        unregister from RHSM
    '''
    Expect.expect_retval(CONNECTION, "rm -f /tmp/rhuipool.txt")
    Expect.expect_retval(CONNECTION, "subscription-manager unregister")

def teardown():
    '''
        announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
