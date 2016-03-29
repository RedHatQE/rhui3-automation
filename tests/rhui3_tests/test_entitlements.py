#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_entitlement import *

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_master")

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

def test_02_list_rh_entitlements():
    '''
       list Red Hat content certificate entitlements
    '''
    entitlements = RHUIManagerEntitlements.list_rh_entitlements(connection)
    nose.tools.eq_(isinstance(entitlements, list), True)

def test_03_list_custom_entitlements():
    '''
       list custom content certificate entitlements
    '''
    list = RHUIManagerEntitlements.list_custom_entitlements(connection)
    nose.tools.assert_equal(len(list), 0)

def test_04_upload_rh_certificate():
    '''
       upload a new or updated Red Hat content certificate
    '''
    list = RHUIManagerEntitlements.upload_rh_certificate(connection)
    nose.tools.assert_not_equal(len(list), 0)

def test_02_list_rh_entitlements():
    '''
       list Red Hat content certificate entitlements
    '''
    entitlements = RHUIManagerEntitlements.list_rh_entitlements(connection)
    nose.tools.eq_(isinstance(entitlements, list), True)

