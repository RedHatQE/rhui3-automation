'''User management tests'''

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
        TODO a test case for an initial password
    '''
    RHUIManager.initial_run(CONNECTION)

def test_02_change_password():
    '''
        change a user's password (will log the user out automatically)
    '''
    RHUIManager.screen(CONNECTION, "users")
    RHUIManager.change_user_password(CONNECTION, password="new_rhui_pass")

def test_03_login_with_new_pass():
    '''
       log in with a new password
    '''
    RHUIManager.initial_run(CONNECTION, password="new_rhui_pass")

def test_04():
    '''
        change a user's password back to the default one
    '''
    RHUIManager.screen(CONNECTION, "users")
    RHUIManager.change_user_password(CONNECTION)

def test_05_login_with_wrong_pass():
    '''
        BZ 1282522. Doing initial run with the wrong password.
    '''
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
