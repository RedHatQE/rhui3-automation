#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_entitlement import *
from rhui3_tests_lib.rhuimanager_repo import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_initial_run():
    '''
        log in into RHUI
        see roles/tests/tasks/main.yml
    '''
    RHUIManager.initial_run(connection)

def test_02_list_rh_entitlements():
    '''
       list Red Hat content certificate entitlements
    '''
    entitlements = RHUIManagerEntitlements.list_rh_entitlements(connection)
    nose.tools.eq_(isinstance(entitlements, list), True)

def test_03_list_custom_entitlements():
    '''
       list custom content certificate entitlements, expect none
    '''
    list = RHUIManagerEntitlements.list_custom_entitlements(connection)
    nose.tools.assert_equal(len(list), 0)

def test_04_upload_rh_certificate():
    '''
       upload a new or updated Red Hat content certificate
    '''
    list = RHUIManagerEntitlements.upload_rh_certificate(connection)
    nose.tools.assert_not_equal(len(list), 0)

def test_05_list_rh_entitlements():
    '''
       list Red Hat content certificate entitlements
    '''
    entitlements = RHUIManagerEntitlements.list_rh_entitlements(connection)
    nose.tools.eq_(isinstance(entitlements, list), True)

def test_06_add_custom_repo():
    '''
       add a custom repo to protect by a client entitlement certificate
    '''
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    RHUIManagerRepo.add_custom_repo(connection, "custom-enttest", "", "", "1", "y")

def test_07_list_custom_entitlements():
    '''
       list custom content certificate entitlements, expect one
    '''
    list = RHUIManagerEntitlements.list_custom_entitlements(connection)
    nose.tools.assert_equal(len(list), 1)

def test_08_remove_custom_repo():
    '''
       remove the custom repo
    '''
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    RHUIManagerRepo.delete_repo(connection, ["custom-enttest"])
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

def test_09_list_custom_entitlements():
    '''
       list custom content certificate entitlements, expect none
    '''
    Expect.enter(connection, "home")
    list = RHUIManagerEntitlements.list_custom_entitlements(connection)
    nose.tools.assert_equal(len(list), 0)

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)
