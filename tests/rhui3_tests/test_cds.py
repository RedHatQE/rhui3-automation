'''CDS management tests'''

from os.path import basename
import random

import logging
import nose
import stitches

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
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

def test_07_delete_cds():
    '''
        delete all CDSs
    '''
    RHUIManagerInstance.delete_all(CONNECTION, "cds")

def test_08_list_cds():
    '''
        list CDSs, expect none
    '''
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(cds_list, [])

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
