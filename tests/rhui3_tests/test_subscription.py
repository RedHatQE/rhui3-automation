""" Test case for the RHUI SKU, the RHUI 3 repo, and subscription registration in RHUI """

import logging
from os.path import basename

import nose
import stitches
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_subman import RHUIManagerSubMan
from rhui3_tests_lib.subscription import RHSMRHUI

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

class TestSubscription(object):
    '''
        class for tests for subscription registration in RHUI
    '''

    def __init__(self):
        with open('/usr/share/rhui3_tests_lib/config/tested_repos.yaml', 'r') as configfile:
            doc = yaml.load(configfile)
        self.subscription_name_1 = doc['subscription1']['name']

    @staticmethod
    def setup_class():
        '''
            announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_00_initial_run():
        '''log in to RHUI'''
        RHUIManager.initial_run(CONNECTION)

    @staticmethod
    def test_01_register_system():
        '''
            register with RHSM
        '''
        RHSMRHUI.register_system(CONNECTION)

    @staticmethod
    def test_02_attach_rhui_sku():
        '''
            check if the RHUI SKU is available and attach it if so
        '''
        RHSMRHUI.attach_rhui_sku(CONNECTION)

    @staticmethod
    def test_03_enable_rhui_3_repo():
        '''
            enable the RHUI 3 repo
        '''
        RHSMRHUI.enable_rhui_3_repo(CONNECTION)

    def test_04_check_available_subs(self):
        '''
            check if the subscription available to RHUI is indeed RHUI for CCSP
        '''
        avail_sub = RHUIManagerSubMan.subscriptions_list(CONNECTION, "available")
        nose.tools.assert_not_equal(len(avail_sub), 0)
        nose.tools.assert_equal(self.subscription_name_1, avail_sub[0])

    def test_05_register_sub_in_rhui(self):
        '''
            register the RHUI for CCSP subscription in RHUI
        '''
        RHUIManagerSubMan.subscriptions_register(CONNECTION, [self.subscription_name_1])

    def test_06_check_registered_subs(self):
        '''
            check if the subscription is now tracked as registered
        '''
        reg_sub = RHUIManagerSubMan.subscriptions_list(CONNECTION, "registered")
        nose.tools.assert_not_equal(len(reg_sub), 0)
        nose.tools.assert_equal(self.subscription_name_1, reg_sub[0])

    def test_07_unregister_sub_in_rhui(self):
        '''
            unregister the subscription in RHUI
        '''
        RHUIManagerSubMan.subscriptions_unregister(CONNECTION, [self.subscription_name_1])
        # also delete the cert file
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def test_08_check_registered_subs():
        '''
            check if the subscription is no longer tracked as registered
        '''
        reg_sub = RHUIManagerSubMan.subscriptions_list(CONNECTION, "registered")
        nose.tools.assert_equal(len(reg_sub), 0)

    @staticmethod
    def test_09_unregister_system():
        '''
            unregister from RHSM
        '''
        RHSMRHUI.unregister_system(CONNECTION)

    @staticmethod
    def teardown_class():
        '''
            announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
