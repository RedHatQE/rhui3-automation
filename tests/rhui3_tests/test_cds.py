'''CDS management tests'''

from os.path import basename
import random

import logging
import nose
import stitches

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance, NoSuchInstance
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

CDS_HOSTNAMES = Util.get_cds_hostnames()

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

def test_10_add_cds_uppercase():
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

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
