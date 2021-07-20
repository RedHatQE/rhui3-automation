'''Entitlement management tests'''

from __future__ import print_function

from os.path import basename

import logging
import nose

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements, \
                                                    BadCertificate, \
                                                    IncompatibleCertificate, \
                                                    MissingCertificate
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

RHUA = ConMgr.connect()

class TestEntitlement():
    '''
       class for entitlement tests
    '''

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_initial_run():
        '''
            log in to RHUI
        '''
        RHUIManager.initial_run(RHUA)

    @staticmethod
    def test_02_list_rh_entitlements():
        '''
           list Red Hat content certificate entitlements
        '''
        entitlements = RHUIManagerEntitlements.list_rh_entitlements(RHUA)
        nose.tools.eq_(isinstance(entitlements, list), True)

    @staticmethod
    def test_03_list_cus_entitlements():
        '''
           list custom content certificate entitlements, expect none
        '''
        entlist = RHUIManagerEntitlements.list_custom_entitlements(RHUA)
        nose.tools.assert_equal(len(entlist), 0)

    @staticmethod
    def test_04_upload_rh_certificate():
        '''
           upload a new or updated Red Hat content certificate
        '''
        entlist = RHUIManagerEntitlements.upload_rh_certificate(RHUA)
        nose.tools.assert_not_equal(len(entlist), 0)

    @staticmethod
    def test_05_list_rh_entitlements():
        '''
           list Red Hat content certificate entitlements
        '''
        entitlements = RHUIManagerEntitlements.list_rh_entitlements(RHUA)
        nose.tools.eq_(isinstance(entitlements, list), True)

    @staticmethod
    def test_06_add_custom_repo():
        '''
           add a custom repo to protect by a client entitlement certificate
        '''
        RHUIManagerRepo.add_custom_repo(RHUA, "custom-enttest", "", "", "1", "y")

    @staticmethod
    def test_07_list_cust_entitlements():
        '''
           list custom content certificate entitlements, expect one
        '''
        entlist = RHUIManagerEntitlements.list_custom_entitlements(RHUA)
        nose.tools.assert_equal(len(entlist), 1)

    @staticmethod
    def test_08_remove_custom_repo():
        '''
           remove the custom repo
        '''
        RHUIManagerRepo.delete_repo(RHUA, ["custom-enttest"])
        nose.tools.assert_equal(RHUIManagerRepo.list(RHUA), [])

    @staticmethod
    def test_09_list_cust_entitlements():
        '''
           list custom content certificate entitlements, expect none
        '''
        entlist = RHUIManagerEntitlements.list_custom_entitlements(RHUA)
        nose.tools.assert_equal(len(entlist), 0)

    @staticmethod
    def test_10_remove_certificates():
        '''
            clean up uploaded entitlement certificates
        '''
        RHUIManager.remove_rh_certs(RHUA)

    @staticmethod
    def test_11_upload_exp_cert():
        '''
           upload an expired certificate, expect a proper refusal
        '''
        nose.tools.assert_raises(BadCertificate,
                                 RHUIManagerEntitlements.upload_rh_certificate,
                                 RHUA,
                                 "/tmp/extra_rhui_files/rhcert_expired.pem")

    @staticmethod
    def test_12_upload_incompat_cert():
        '''
           upload an incompatible certificate, expect a proper refusal
        '''
        cert = "/tmp/extra_rhui_files/rhcert_incompatible.pem"
        if Util.cert_expired(RHUA, cert):
            raise nose.exc.SkipTest("The given certificate has already expired.")
        nose.tools.assert_raises(IncompatibleCertificate,
                                 RHUIManagerEntitlements.upload_rh_certificate,
                                 RHUA,
                                 cert)

    @staticmethod
    def test_13_upload_semi_bad_cert():
        '''
           upload a certificate containing a mix of valid and invalid repos
        '''
        # for RHBZ#1588931 & RHBZ#1584527
        cert = "/tmp/extra_rhui_files/rhcert_partially_invalid.pem"
        if Util.cert_expired(RHUA, cert):
            raise nose.exc.SkipTest("The given certificate has already expired.")
        RHUIManagerEntitlements.upload_rh_certificate(RHUA, cert)

    @staticmethod
    def test_14_remove_semi_bad_cert():
        '''
            remove the certificate
        '''
        RHUIManager.remove_rh_certs(RHUA)

    @staticmethod
    def test_15_upload_nonexist_cert():
        '''
            try uploading a certificate file that does not exist, should be handled gracefully
        '''
        nose.tools.assert_raises(MissingCertificate,
                                 RHUIManagerEntitlements.upload_rh_certificate,
                                 RHUA,
                                 "/this_file_cant_be_there")
    @staticmethod
    def test_16_upload_empty_cert():
        '''
           upload a certificate that contains no entitlements
        '''
        # for RHBZ#1497028
        cert = "/tmp/extra_rhui_files/rhcert_empty.pem"
        if Util.cert_expired(RHUA, cert):
            raise nose.exc.SkipTest("The given certificate has already expired.")
        nose.tools.assert_raises(IncompatibleCertificate,
                                 RHUIManagerEntitlements.upload_rh_certificate,
                                 RHUA,
                                 cert)


    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
