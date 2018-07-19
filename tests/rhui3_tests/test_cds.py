'''CDS management tests'''

from os.path import basename

import logging
import nose
import stitches

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

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
        add two CDSs
    '''
    RHUIManagerInstance.add_instance(CONNECTION, "cds", "cds01.example.com")
    RHUIManagerInstance.add_instance(CONNECTION, "cds", "cds02.example.com")

def test_04_list_cds():
    '''
        list CDSs, expect two
    '''
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(len(cds_list), 2)

def test_05_readd_cds():
    '''
        add the CDS again (reapply the configuration)
    '''
    RHUIManagerInstance.add_instance(CONNECTION, "cds", "cds01.example.com", update=True)

def test_06_list_cds():
    '''
        check if the CDSs are still tracked
    '''
    cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
    nose.tools.assert_equal(len(cds_list), 2)

def test_07_delete_cds():
    '''
        delete both CDSs
    '''
    RHUIManagerInstance.delete(CONNECTION, "cds", ["cds01.example.com", "cds02.example.com"])

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
