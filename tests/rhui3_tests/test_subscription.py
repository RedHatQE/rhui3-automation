""" Test case for the RHUI SKU, the RHUI 3 repo, and subscription registration in RHUI """

from __future__ import print_function

import logging
from os.path import basename

import nose
import yaml

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_subman import RHUIManagerSubMan
from rhui3_tests_lib.subscription import RHSMRHUI

logging.basicConfig(level=logging.DEBUG)

RHUA = ConMgr.connect()

class TestSubscription(object):
    """class for tests for subscription registration in RHUI"""

    def __init__(self):
        with open("/etc/rhui3_tests/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)
            self.subscriptions = doc["subscriptions"]
            self.sca_name = doc["SCA"]["name"]

    @staticmethod
    def setup_class():
        """announce the beginning of the test run"""
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_00_initial_run():
        """log in to RHUI"""
        RHUIManager.initial_run(RHUA)

    @staticmethod
    def test_01_register_system():
        """register with RHSM"""
        RHSMRHUI.register_system(RHUA)

    def test_02_attach_rhui_sub(self):
        """attach the RHUI subscription"""
        RHSMRHUI.attach_subscription(RHUA, self.subscriptions["RHUI"])

    def test_03_attach_atomic_sub(self):
        """attach the Atomic subscription"""
        RHSMRHUI.attach_subscription(RHUA, self.subscriptions["Atomic"])

    def test_04_check_available_subs(self):
        """check if the subscriptions available to RHUI are the known ones"""
        avail_subs = RHUIManagerSubMan.subscriptions_list(RHUA, "available")
        nose.tools.eq_(sorted(avail_subs), sorted(self.subscriptions.values()))

    def test_05_reg_rhui_sub_in_rhui(self):
        """register the RHUI subscription in RHUI"""
        RHUIManagerSubMan.subscriptions_register(RHUA, [self.subscriptions["RHUI"]])

    def test_06_reg_atomic_sub_in_rhui(self):
        """register the Atomic subscription in RHUI"""
        RHUIManagerSubMan.subscriptions_register(RHUA, [self.subscriptions["Atomic"]])

    def test_07_check_registered_subs(self):
        """check if the subscriptions are now tracked as registered"""
        reg_subs = RHUIManagerSubMan.subscriptions_list(RHUA, "registered")
        nose.tools.eq_(sorted(reg_subs), sorted(self.subscriptions.values()))

    def test_08_unregister_sub_in_rhui(self):
        """unregister the subscriptions in RHUI"""
        RHUIManagerSubMan.subscriptions_unregister(RHUA, self.subscriptions.values())
        # also delete the cert files
        RHUIManager.remove_rh_certs(RHUA)

    @staticmethod
    def test_09_check_registered_subs():
        """check if the subscriptions are no longer tracked as registered"""
        reg_sub = RHUIManagerSubMan.subscriptions_list(RHUA, "registered")
        nose.tools.ok_(not reg_sub, msg="something remained: %s" % reg_sub)

    @staticmethod
    def test_10_unregister_system():
        """unregister from RHSM"""
        RHSMRHUI.unregister_system(RHUA)

    @staticmethod
    def test_11_sca_setup():
        """set up SCA"""
        RHSMRHUI.sca_setup(RHUA)

    def test_12_list_sca(self):
        """check if SCA is an available subscription"""
        avail_subs = RHUIManagerSubMan.subscriptions_list(RHUA, "available")
        nose.tools.eq_(avail_subs, [self.sca_name])

    def test_13_reg_sca_sub_in_rhui(self):
        """register the SCA subscription in RHUI"""
        RHUIManagerSubMan.subscriptions_register(RHUA, [self.sca_name])

    def test_14_check_registered_subs(self):
        """check if the SCA subscription is now tracked as registered"""
        reg_subs = RHUIManagerSubMan.subscriptions_list(RHUA, "registered")
        nose.tools.eq_(reg_subs, [self.sca_name])

    def test_15_unregister_sca(self):
        """unregister the SCA subscription"""
        RHUIManagerSubMan.subscriptions_unregister(RHUA, [self.sca_name])
        # also delete the cert file
        RHUIManager.remove_rh_certs(RHUA)

    @staticmethod
    def test_16_check_registered_subs():
        """check if the SCA subscription is no longer tracked as registered"""
        reg_subs = RHUIManagerSubMan.subscriptions_list(RHUA, "registered")
        nose.tools.ok_(not reg_subs, msg="something remained: %s" % reg_subs)

    @staticmethod
    def test_17_sca_cleanup():
        """clean up the SCA cert and key"""
        RHSMRHUI.sca_cleanup(RHUA)

    @staticmethod
    def teardown_class():
        """announce the end of the test run"""
        print("*** Finished running %s. *** " % basename(__file__))
