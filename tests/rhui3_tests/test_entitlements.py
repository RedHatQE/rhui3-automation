'''Entitlement management tests'''

#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml
from nose.tools import *

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_entitlement import *
from rhui3_tests_lib.rhuimanager_repo import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

class TestEntitlement:

    def setUp(self):
        print "*** Running %s: *** " % basename(__file__)

    def test_01_initial_run(self):
        '''
            log in into RHUI
            see roles/tests/tasks/main.yml
        '''
        RHUIManager.initial_run(connection)

    def test_02_list_rh_entitlements(self):
        '''
           list Red Hat content certificate entitlements
        '''
        entitlements = RHUIManagerEntitlements.list_rh_entitlements(connection)
        nose.tools.eq_(isinstance(entitlements, list), True)

    def test_03_list_custom_entitlements(self):
        '''
           list custom content certificate entitlements, expect none
        '''
        list = RHUIManagerEntitlements.list_custom_entitlements(connection)
        nose.tools.assert_equal(len(list), 0)

    def test_04_upload_rh_certificate(self):
        '''
           upload a new or updated Red Hat content certificate
        '''
        list = RHUIManagerEntitlements.upload_rh_certificate(connection)
        nose.tools.assert_not_equal(len(list), 0)

    def test_05_list_rh_entitlements(self):
        '''
           list Red Hat content certificate entitlements
        '''
        entitlements = RHUIManagerEntitlements.list_rh_entitlements(connection)
        nose.tools.eq_(isinstance(entitlements, list), True)

    def test_06_add_custom_repo(self):
        '''
           add a custom repo to protect by a client entitlement certificate
        '''
        RHUIManagerRepo.add_custom_repo(connection, "custom-enttest", "", "", "1", "y")

    def test_07_list_custom_entitlements(self):
        '''
           list custom content certificate entitlements, expect one
        '''
        list = RHUIManagerEntitlements.list_custom_entitlements(connection)
        nose.tools.assert_equal(len(list), 1)

    def test_08_remove_custom_repo(self):
        '''
           remove the custom repo
        '''
        RHUIManagerRepo.delete_repo(connection, ["custom-enttest"])
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    def test_09_list_custom_entitlements(self):
        '''
           list custom content certificate entitlements, expect none
        '''
        list = RHUIManagerEntitlements.list_custom_entitlements(connection)
        nose.tools.assert_equal(len(list), 0)

    def test_10_remove_existing_entitlement_certificates(self):
        '''Clean up uploaded entitlement certificates'''
        RHUIManager.remove_rh_certs(connection)

    @raises(BadCertificate)
    def test_11_upload_expired_certificate(self):
        '''
           upload an expired certificate, expect a proper refusal
        '''
        RHUIManagerEntitlements.upload_rh_certificate(connection, "/tmp/extra_rhui_files/rhcert_expired.pem")

    @raises(IncompatibleCertificate)
    def test_12_upload_incompatible_certificate(self):
        '''
           upload an incompatible certificate, expect a proper refusal
        '''
        RHUIManagerEntitlements.upload_rh_certificate(connection, "/tmp/extra_rhui_files/rhcert_incompatible.pem")

    def tearDown(self):
        print "*** Finished running %s. *** " % basename(__file__)
