""" Test case for the RHUI SKU, the RHUI 3 repo, and subscription registration in RHUI """

from __future__ import print_function

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
    """class for tests for subscription registration in RHUI"""

    def __init__(self):
        with open("/etc/rhui3_tests/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)
            self.subscriptions = doc["subscriptions"]

    @staticmethod
    def setup_class():
        """announce the beginning of the test run"""
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_00_initial_run():
        """log in to RHUI"""
        RHUIManager.initial_run(CONNECTION)

    @staticmethod
    def test_01_register_system():
        """register with RHSM"""
        RHSMRHUI.register_system(CONNECTION)

    def test_02_attach_rhui_sub(self):
        """attach the RHUI subscription"""
        RHSMRHUI.attach_subscription(CONNECTION, self.subscriptions["RHUI"])

    def test_03_attach_atomic_sub(self):
        """attach the Atomic subscription"""
        RHSMRHUI.attach_subscription(CONNECTION, self.subscriptions["Atomic"])

    def test_04_check_available_subs(self):
        """check if the subscriptions available to RHUI are the known ones"""
        avail_subs = RHUIManagerSubMan.subscriptions_list(CONNECTION, "available")
        nose.tools.eq_(sorted(avail_subs), sorted(self.subscriptions.values()))

    def test_05_reg_rhui_sub_in_rhui(self):
        """register the RHUI subscription in RHUI"""
        RHUIManagerSubMan.subscriptions_register(CONNECTION, [self.subscriptions["RHUI"]])

    def test_06_reg_atomic_sub_in_rhui(self):
        """register the Atomic subscription in RHUI"""
        RHUIManagerSubMan.subscriptions_register(CONNECTION, [self.subscriptions["Atomic"]])

    def test_07_check_registered_subs(self):
        """check if the subscriptions are now tracked as registered"""
        reg_subs = RHUIManagerSubMan.subscriptions_list(CONNECTION, "registered")
        nose.tools.eq_(sorted(reg_subs), sorted(self.subscriptions.values()))

    def test_08_unregister_sub_in_rhui(self):
        """unregister the subscriptions in RHUI"""
        RHUIManagerSubMan.subscriptions_unregister(CONNECTION, self.subscriptions.values())
        # also delete the cert files
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def test_09_check_registered_subs():
        """check if the subscriptions are no longer tracked as registered"""
        reg_sub = RHUIManagerSubMan.subscriptions_list(CONNECTION, "registered")
        nose.tools.ok_(not reg_sub, msg="something remained: %s" % reg_sub)

    @staticmethod
    def test_10_unregister_system():
        """unregister from RHSM"""
        RHSMRHUI.unregister_system(CONNECTION)

    @staticmethod
    def teardown_class():
        """announce the end of the test run"""
        print("*** Finished running %s. *** " % basename(__file__))
