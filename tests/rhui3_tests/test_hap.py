'''HAProxy management tests'''

#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_instance import *
from rhui3_tests_lib.instance import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_initial_run():
    '''
        log in to RHUI
    '''
    RHUIManager.initial_run(connection)

def test_02_list_empty_hap():
    '''
        check if there are no HAProxy Load-balancers
    '''
    hap_list = RHUIManagerInstance.list(connection, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])

def test_03_add_hap():
    '''
        add an HAProxy Load-balancer
    '''
    RHUIManagerInstance.add_instance(connection, "loadbalancers", "hap01.example.com")

def test_04_list_hap():
    '''
        check if the HAProxy Load-balancer was added
    '''
    hap_list = RHUIManagerInstance.list(connection, "loadbalancers")
    nose.tools.assert_not_equal(hap_list, [])

def test_05_readd_hap():
    '''
        add the HAProxy Load-balancer again (reapply the configuration)
    '''
    RHUIManagerInstance.add_instance(connection, "loadbalancers", "hap01.example.com", update=True)

def test_06_list_hap():
    '''
        check if the HAProxy Load-balancer is still tracked
    '''
    hap_list = RHUIManagerInstance.list(connection, "loadbalancers")
    nose.tools.assert_not_equal(hap_list, [])

def test_07_delete_hap():
    '''
        delete the HAProxy Load-balancer
    '''
    RHUIManagerInstance.delete(connection, "loadbalancers", ["hap01.example.com"])

def test_08_list_hap():
    '''
        list HAProxy Load-balancers again, expect none
    '''
    hap_list = RHUIManagerInstance.list(connection, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
