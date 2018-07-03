'''User management tests'''

#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *

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
        TODO a test case for an initial password
    '''
    RHUIManager.initial_run(connection)

def test_02_change_password():
    '''
        change a user's password (will log the user out automatically)
    '''
    RHUIManager.screen(connection, "users")
    RHUIManager.change_user_password(connection, password = "new_rhui_pass")

def test_03_login_with_new_pass():
    '''
       log in with a new password
    '''
    RHUIManager.initial_run(connection, password = "new_rhui_pass")

def test_04():
    '''
        change a user's password back to the default one
    '''
    RHUIManager.screen(connection, "users")
    RHUIManager.change_user_password(connection)

def test_05_login_with_wrong_password():
    '''
        BZ 1282522. Doing initial run with the wrong password.
    '''
    Expect.enter(connection, "rhui-manager")
    Expect.expect(connection, ".*RHUI Username:.*")
    Expect.enter(connection, "admin")
    Expect.expect(connection, "RHUI Password:")
    Expect.enter(connection, "wrong_pass")
    Expect.expect(connection, ".*Invalid login, please check the authentication credentials and try again.")

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
