#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_hap import *
from rhui3_tests_lib.hap import *

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

with open('/tmp/rhui3-tests/tests/rhui3_tests/rhui_manager.yaml', 'r') as file:
    doc = yaml.load(file)

rhui_login = doc['rhui_login']
rhui_pass = doc['rhui_pass']

def test_01_initial_run():
    '''
        log in to RHUI
        see roles/tests/tasks/main.yml
    '''
    RHUIManager.initial_run(connection, username  = rhui_login, password = rhui_pass)

def test_02_list_empty_hap():
    '''
        check if there are no HAProxy Load-balancers
    '''
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_equal(hap_list, [])

def test_03_add_hap():
    '''
        add an HAProxy Load-balancer
    '''
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_equal(hap_list, [])
    hap = Hap()
    RHUIManagerHap.add_hap(connection, hap)


def test_04_list_hap():
    '''
        check if the HAProxy Load-balancer was added
    '''
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_not_equal(hap_list, [])


def test_05_readd_hap():
    '''
        add the HAProxy Load-balancer again (reapply the configuration)
    '''
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_not_equal(hap_list, [])
    hap = Hap()
    RHUIManagerHap.add_hap(connection, hap, update=True)


def test_06_list_hap():
    '''
        check if the HAProxy Load-balancer is still tracked
    '''
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_not_equal(hap_list, [])


def test_07_delete_hap():
    '''
        delete the HAProxy Load-balancer
    '''
    hap = Hap()
    RHUIManagerHap.delete_haps(connection, hap)
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_equal(hap_list, [])


def test_08_list_hap():
    '''
        list HAProxy Load-balancers again, expect none
    '''
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_equal(hap_list, [])

