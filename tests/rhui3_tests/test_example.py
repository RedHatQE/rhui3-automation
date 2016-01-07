#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from distutils.version import LooseVersion
from rhui3_tests_lib.rhui_testcase import *
from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_cds import RHUIManagerCds

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_master")

with open('/tmp/rhui3-tests/tests/tests_rhui3/rhui_manager.cfg', 'r') as file:
    doc = yaml.load(file)

rhui_login = doc['rhui_login']
rhui_pass = doc['rhui_pass']
rhui_manager_version=doc['rhui_manager_version']

def test_1_dummy():
    ''' dummy test to pass'''
    pass

def test_2_dummy():
    ''' dummy test to fail'''
    assert True == False

def test_3_initial_run():
    RHUIManager.initial_run(connection, username  = rhui_login, password = rhui_pass)

def test_change_password():
    '''
        change a user's password
    '''
    RHUIManager.screen(connection, "users")
    Expect.enter(connection, "p")
    Expect.expect(connection, "Username:")
    Expect.enter(connection, 'admin')
    Expect.expect(connection, "New Password:")
    Expect.enter(connection, 'new_pass')
    Expect.expect(connection, "Re-enter Password:")
    Expect.enter(connection, 'new_pass')
    RHUIManager.quit(connection, "Password successfully updated")

def test_login_with_new_pass():
    RHUIManager.initial_run(connection, username  = rhui_login, password = 'new_pass')

def test_set_password_from_conf_file():
    '''
        return previous  user's password

    '''
    RHUIManager.screen(connection, "users")
    Expect.enter(connection, "p")
    Expect.expect(connection, "Username:")
    Expect.enter(connection, 'admin')
    Expect.expect(connection, "New Password:")
    Expect.enter(connection, rhui_pass)
    Expect.expect(connection, "Re-enter Password:")
    Expect.enter(connection, rhui_pass)
    RHUIManager.quit(connection, "Password successfully updated")


@unittest.skipIf(LooseVersion('3.0.16-1') <= rhui_manager_version, "bz to fix")
def test_login_with_wrong_password():
    '''BZ 1282522. Doing initial run with wrong password.
     Expected to fail, to be changed after BZ fix.'''
