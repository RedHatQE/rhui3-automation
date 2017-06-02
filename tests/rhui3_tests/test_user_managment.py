#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_initial_run():
    '''
        TODO a test case for an initial password
        see roles/tests/tasks/main.yml
    '''
    RHUIManager.initial_run(connection)

def test_02_change_password():
    '''
        change a user's password and logout
    '''
    RHUIManager.screen(connection, "users")
    RHUIManager.change_user_password(connection, password = "new_rhui_pass")
    RHUIManager.logout(connection, "Password successfully updated")

def test_03_login_with_new_pass():
    '''
       login with a new password
    '''
    RHUIManager.initial_run(connection, password = "new_rhui_pass")

def test_04():
    '''
        change a user's password back to the default one and logout
    '''
    RHUIManager.screen(connection, "users")
    RHUIManager.change_user_password(connection)
    RHUIManager.logout(connection, "Password successfully updated")

def test_05_login_with_wrong_password():
    '''
        BZ 1282522. Doing initial run with wrong password.
    '''
    Expect.enter(connection, "rhui-manager")
    Expect.expect(connection, ".*RHUI Username:.*")
    Expect.enter(connection, "admin")
    Expect.expect(connection, "RHUI Password:")
    Expect.enter(connection, "wrong_pass")
    Expect.expect(connection, ".*Invalid login, please check the authentication credentials and try again.")

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)

