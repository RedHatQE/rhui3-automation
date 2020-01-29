'''User management tests'''

from __future__ import print_function

from os.path import basename

import logging
from stitches.expect import Expect

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.rhuimanager import RHUIManager

logging.basicConfig(level=logging.DEBUG)

RHUA = ConMgr.connect()

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_initial_run():
    '''
        log in the RHUI (try the "usual" or the default admin password)
    '''
    RHUIManager.initial_run(RHUA)

def test_02_change_password():
    '''
        change the password (will log the user out automatically)
    '''
    RHUIManager.screen(RHUA, "users")
    RHUIManager.change_user_password(RHUA, password="new_rhui_pass")

def test_03_login_with_new_pass():
    '''
       log in with the new password
    '''
    RHUIManager.initial_run(RHUA, password="new_rhui_pass")

def test_04_reset_password():
    '''
        change the password back to the "usual" one
    '''
    RHUIManager.screen(RHUA, "users")
    RHUIManager.change_user_password(RHUA)

def test_05_login_with_wrong_pass():
    '''
        try logging in with the wrong password, should fail gracefully
    '''
    # for RHBZ#1282522
    Expect.enter(RHUA, "rhui-manager")
    Expect.expect(RHUA, ".*RHUI Username:.*")
    Expect.enter(RHUA, "admin")
    Expect.expect(RHUA, "RHUI Password:")
    Expect.enter(RHUA, "wrong_pass")
    Expect.expect(RHUA,
                  ".*Invalid login, please check the authentication credentials and try again.")

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
