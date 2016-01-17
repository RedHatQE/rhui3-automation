#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhui_testcase import *
from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_cds import RHUIManagerCds

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_master")

with open('/tmp/rhui3-tests/tests/rhui3_tests/rhui_manager.yaml', 'r') as file:
    doc = yaml.load(file)

rhui_login = doc['rhui_login']
rhui_pass = doc['rhui_pass']
new_rhui_pass = 'new_pass'
rhui_iso_date = doc['rhui_iso_date']

def test_01_initial_run():
    '''
        TODO a test case for an initial password
        see roles/tests/tasks/main.yml
    '''
    RHUIManager.initial_run(connection, username  = rhui_login, password = rhui_pass)

def test_02_change_password():
    '''
        change a user's password and logout
    '''
    RHUIManager.screen(connection, "users")
    RHUIManager.change_user_password(connection, password = new_rhui_pass)
    RHUIManager.logout(connection, "Password successfully updated")

def test_03_login_with_new_pass():
    '''
       login with a new password
    '''
    RHUIManager.initial_run(connection, username  = rhui_login, password = new_rhui_pass)

def test_04():
    '''
        change a user's password back to the one from rhui_manager.cfg and logout
    '''
    RHUIManager.screen(connection, "users")
    RHUIManager.change_user_password(connection)
    RHUIManager.logout(connection, "Password successfully updated")

@unittest.skipIf(rhui_iso_date == '20151013', 'skip for RHUI iso <= 20151013')
def test_05_login_with_wrong_password():
    '''
        BZ 1282522. Doing initial run with wrong password.
        Expected to fail with a traceback, to be changed after BZ fix.
    '''
    RHUIManager.initial_run(connection, password = 'wrong_pass')

@unittest.skipIf(rhui_iso_date == '20151013', 'skip for RHUI iso <= 20151013')
def test_06_change_password_several_times():
    '''
        BZ 1297538. After a rhui-manager was closed with 'logout' command, open it and
        change a user's password several times.
        Expected to fail with Pulp 401, to be updated after BZ fix.
    '''
    RHUIManager.initial_run(connection, username  = rhui_login, password = rhui_pass)
    Expect.enter(connection, "logout")
    RHUIManager.initial_run(connection, username  = rhui_login, password = rhui_pass)
    RHUIManager.screen(connection, "users")
    RHUIManager.change_user_password(connection, password = new_rhui_pass)
    Expect.expect(connection, "Password successfully updated" + ".*rhui \(users\) =>")
    RHUIManager.change_user_password(connection, password = rhui_pass + new_rhui_pass)
    Expect.expect(connection, "Password successfully updated" + ".*rhui \(users\) =>")
