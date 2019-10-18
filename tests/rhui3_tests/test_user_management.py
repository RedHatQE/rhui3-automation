'''User management tests'''

from __future__ import print_function

from os.path import basename

import logging
import stitches
from stitches.expect import Expect

from rhui3_tests_lib.rhuimanager import RHUIManager

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_initial_run():
    '''
        log in the RHUI (try the "usual" or the default admin password)
    '''
    RHUIManager.initial_run(CONNECTION)

def test_02_change_password():
    '''
        change the password (will log the user out automatically)
    '''
    RHUIManager.screen(CONNECTION, "users")
    RHUIManager.change_user_password(CONNECTION, password="new_rhui_pass")

def test_03_login_with_new_pass():
    '''
       log in with the new password
    '''
    RHUIManager.initial_run(CONNECTION, password="new_rhui_pass")

def test_04_reset_password():
    '''
        change the password back to the "usual" one
    '''
    RHUIManager.screen(CONNECTION, "users")
    RHUIManager.change_user_password(CONNECTION)

def test_05_login_with_wrong_pass():
    '''
        try logging in with the wrong password, should fail gracefully
    '''
    # for RHBZ#1282522
    Expect.enter(CONNECTION, "rhui-manager")
    Expect.expect(CONNECTION, ".*RHUI Username:.*")
    Expect.enter(CONNECTION, "admin")
    Expect.expect(CONNECTION, "RHUI Password:")
    Expect.enter(CONNECTION, "wrong_pass")
    Expect.expect(CONNECTION,
                  ".*Invalid login, please check the authentication credentials and try again.")

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
