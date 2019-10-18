'''CDS management tests'''

from __future__ import print_function

from os.path import basename
import random
import re

import logging
import nose
import stitches
from stitches.expect import Expect

from rhui3_tests_lib.helpers import Helpers
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance, NoSuchInstance
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

CDS_HOSTNAMES = Util.get_cds_hostnames()

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
CDS = [stitches.Connection(host, "root", "/root/.ssh/id_rsa_test") for host in CDS_HOSTNAMES]

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_initial_run():
    '''
        log in to RHUI
    '''
    RHUIManager.initial_run(CONNECTION)

def test_02_list_empty_cds():
    '''
        check if there are no CDSs
    '''
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(cds_list, [])

def test_03_add_cds():
    '''
        add all known CDSs
    '''
    for cds in CDS_HOSTNAMES:
        RHUIManagerInstance.add_instance(CONNECTION, "cds", cds)

def test_04_list_cds():
    '''
        list CDSs, expect as many as there are in /etc/hosts
    '''
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(len(cds_list), len(CDS_HOSTNAMES))

def test_05_readd_cds():
    '''
        add one of the CDSs again (reapply the configuration)
    '''
    # choose a random CDS hostname from the list
    RHUIManagerInstance.add_instance(CONNECTION, "cds", random.choice(CDS_HOSTNAMES), update=True)

def test_06_list_cds():
    '''
        check if the CDSs are still tracked
    '''
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(len(cds_list), len(CDS_HOSTNAMES))

def test_07_delete_nonexisting_cds():
    '''
        try deleting an untracked CDS, should be rejected (by rhui3_tests_lib)
    '''
    nose.tools.assert_raises(NoSuchInstance,
                             RHUIManagerInstance.delete,
                             CONNECTION,
                             "cds",
                             ["cdsfoo.example.com"])

def test_08_delete_cds():
    '''
        delete all CDSs
    '''
    RHUIManagerInstance.delete_all(CONNECTION, "cds")

def test_09_list_cds():
    '''
        list CDSs, expect none
    '''
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(cds_list, [])

def test_10_check_cleanup():
    '''
        check if Apache was stopped and the remote file system unmounted on all CDSs
    '''
    service = "httpd"
    mdir = "/var/lib/rhui/remote_share"
    dirty_hosts = dict()
    errors = []

    dirty_hosts["httpd"] = [cds.hostname for cds in CDS if Helpers.check_service(cds, service)]
    dirty_hosts["mount"] = [cds.hostname for cds in CDS if Helpers.check_mountpoint(cds, mdir)]

    if dirty_hosts["httpd"]:
        errors.append("Apache is still running on %s" % dirty_hosts["httpd"])
    if dirty_hosts["mount"]:
        errors.append("The remote file system is still mounted on %s" % dirty_hosts["mount"])

    nose.tools.ok_(not errors, msg=errors)

def test_11_add_cds_uppercase():
    '''
        add (and delete) a CDS with uppercase characters
    '''
    # for RHBZ#1572623
    # choose a random CDS hostname from the list
    cds_up = random.choice(CDS_HOSTNAMES).replace("cds", "CDS")
    RHUIManagerInstance.add_instance(CONNECTION, "cds", cds_up)
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(len(cds_list), 1)
    RHUIManagerInstance.delete(CONNECTION, "cds", [cds_up])
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(len(cds_list), 0)

def test_12_delete_unreachable():
    '''
    add a CDS, make it unreachable, and see if it can still be deleted from the RHUA
    '''
    # for RHBZ#1639996
    # choose a random CDS hostname from the list
    cds = random.choice(CDS_HOSTNAMES)
    RHUIManagerInstance.add_instance(CONNECTION, "cds", cds)
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_not_equal(cds_list, [])

    Helpers.break_hostname(CONNECTION, cds)

    # delete it
    RHUIManagerInstance.delete(CONNECTION, "cds", [cds])
    # check it
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(cds_list, [])

    Helpers.unbreak_hostname(CONNECTION)

    # the node remains configured (RHUI mount point, httpd)... unconfigure it properly
    RHUIManagerInstance.add_instance(CONNECTION, "cds", cds)
    RHUIManagerInstance.delete(CONNECTION, "cds", [cds])

def test_13_delete_select_0():
    '''
    add a CDS and see if no issue occurs if it and "a zeroth" (ghost) CDSs are selected for deletion
    '''
    # for RHBZ#1305612
    # choose a random CDS and add it
    cds = random.choice(CDS_HOSTNAMES)
    RHUIManagerInstance.add_instance(CONNECTION, "cds", cds)
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_not_equal(cds_list, [])

    # try the deletion
    RHUIManager.screen(CONNECTION, "cds")
    Expect.enter(CONNECTION, "d")
    Expect.expect(CONNECTION, "Enter value")
    Expect.enter(CONNECTION, "0")
    Expect.expect(CONNECTION, "Enter value")
    Expect.enter(CONNECTION, "1")
    Expect.expect(CONNECTION, "Enter value")
    Expect.enter(CONNECTION, "c")
    state = Expect.expect_list(CONNECTION,
                               [(re.compile(".*Are you sure.*", re.DOTALL), 1),
                                (re.compile(".*An unexpected error.*", re.DOTALL), 2)])
    if state == 1:
        Expect.enter(CONNECTION, "y")
        RHUIManager.quit(CONNECTION, timeout=180)
    else:
        Expect.enter(CONNECTION, "q")

    # the CDS list ought to be empty now; if not, delete the CDS and fail
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    if cds_list:
        RHUIManagerInstance.delete_all(CONNECTION, "cds")
        raise AssertionError("The CDS list is not empty after the deletion attempt: %s." % cds_list)

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
