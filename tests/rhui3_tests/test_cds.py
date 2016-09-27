#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_cds import *
from rhui3_tests_lib.cds import *

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

with open('/tmp/rhui3-tests/tests/rhui3_tests/rhui_manager.yaml', 'r') as file:
    doc = yaml.load(file)

rhui_login = doc['rhui_login']
rhui_pass = doc['rhui_pass']

def test_01_initial_run():
    '''
        log in into RHUI
        see roles/tests/tasks/main.yml
    '''
    RHUIManager.initial_run(connection, username  = rhui_login, password = rhui_pass)

def test_02_add_cds():
    '''
        add a CDS
    '''
    cds_list = RHUIManagerCds.list(connection)
    nose.tools.assert_equal(cds_list, [])
    cds = Cds()
    RHUIManagerCds.add_cds(connection, cds)


def test_02_list_cds():
    '''
        list CDSs
    '''
    cds_list2 = RHUIManagerCds.list(connection)
    nose.tools.assert_not_equal(cds_list2, [])
 
 
def test_04_delete_cds():
    '''
        delete a CDS
    '''
    cds = Cds()
    RHUIManagerCds.delete_cdses(connection, cds)
    cds_list3 = RHUIManagerCds.list(connection)
    nose.tools.assert_equal(cds_list3, [])


def test_03_list_cds():
    '''
        list CDSs
    '''
    cds_list3 = RHUIManagerCds.list(connection)
    nose.tools.assert_equal(cds_list3, [])


