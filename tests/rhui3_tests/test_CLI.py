'''RHUI CLI tests'''

#! /usr/bin/python -tt

import nose, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanagercli import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
custom_repo_name = "my_custom_repo"

class TestCLI(object):
    '''
        class for CLI tests
    '''

    def __init__(self):
        with open('/tmp/rhui3-tests/tests/rhui3_tests/tested_repos.yaml', 'r') as file:
            doc = yaml.load(file)

        self.yum_repo_name_1 = doc['CLI_repo1']['name']
        self.yum_repo_id_1 = doc['CLI_repo1']['id']
        self.yum_repo_name_2 = doc['CLI_repo2']['name']
        self.yum_repo_id_2 = doc['CLI_repo2']['id']

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_initial_run():
        '''Do an initial rhui-manager run to make sure we are logged in'''
        RHUIManager.initial_run(connection)

    @staticmethod
    def test_02_check_empty_repo_list():
        '''Check if the repolist is empty (interactively; not currently supported by the CLI)'''
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_03_remove_existing_entitlement_certificates():
        '''Clean up uploaded entitlement certificates'''
        RHUIManager.remove_rh_certs(connection)

    @staticmethod
    def test_04_create_custom_repo():
        '''Create a custom repo for further testing (interactively; not currently supported by the CLI)'''
        RHUIManagerRepo.add_custom_repo(connection, custom_repo_name, entitlement="n")

    @staticmethod
    def test_05_check_custom_repo():
        '''Check if the custom repo was actually created'''
        RHUIManagerCLI.repo_list(connection, custom_repo_name, custom_repo_name)

    @staticmethod
    def test_06_upload_rpm_to_custom_repo():
        '''Upload content to the custom repo'''
        RHUIManagerCLI.packages_upload(connection, custom_repo_name, "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")

    @staticmethod
    def test_07_check_package_in_custom_repo():
        '''Check that the uploaded package is now in the repo'''
        RHUIManagerCLI.packages_list(connection, custom_repo_name, "rhui-rpm-upload-test-1-1.noarch.rpm")

    @staticmethod
    def test_08_upload_entitlement_certificate():
        '''Upload the Atomic (the small) entitlement certificate'''
        RHUIManagerCLI.cert_upload(connection, "/tmp/extra_rhui_files/rhcert_atomic.pem", "Atomic")

    @staticmethod
    def test_09_check_certificate_info():
        '''Check certificate info for validity'''
        RHUIManagerCLI.cert_info(connection)

    @staticmethod
    def test_10_check_certificate_expiration():
        '''Check if the certificate expiration date is OK'''
        RHUIManagerCLI.cert_expiration(connection)

    def test_11_check_unused_product(self):
        '''Check if a repo is available'''
        RHUIManagerCLI.repo_unused(connection, self.yum_repo_name_1)

    def test_12_add_rh_repo_by_product(self):
        '''Add a Red Hat repo by its product name'''
        RHUIManagerCLI.repo_add(connection, self.yum_repo_name_1)

    def test_13_add_rh_repo_by_id(self):
        '''Add a Red Hat repo by its ID'''
        RHUIManagerCLI.repo_add_by_repo(connection, [self.yum_repo_id_2])

    def test_14_repo_list(self):
        '''Check the added repos'''
        RHUIManagerCLI.repo_list(connection, self.yum_repo_id_1, self.yum_repo_name_1)
        RHUIManagerCLI.repo_list(connection, self.yum_repo_id_2, self.yum_repo_name_2)

    def test_15_no_unexpected_repos(self):
        '''Check if no stray repo was added'''
        RHUIManagerCLI.validate_repo_list(connection, [self.yum_repo_id_1, self.yum_repo_id_2, custom_repo_name])

    def test_16_start_syncing_repo(self):
        '''Sync one of the repos'''
        RHUIManagerCLI.repo_sync(connection, self.yum_repo_id_2, self.yum_repo_name_2)

    def test_17_repo_info(self):
        '''Verify that the repo name is part of the information about the specified repo ID'''
        RHUIManagerCLI.repo_info(connection, self.yum_repo_id_2, self.yum_repo_name_2)

    def test_18_check_package_in_repo(self):
        '''Check a random package in the repo'''
        RHUIManagerCLI.packages_list(connection, self.yum_repo_id_2, "ostree")

    def test_19_list_labels(self):
        '''Check repo labels'''
        repo_label = self.yum_repo_id_1.replace("-x86_64", "")
        RHUIManagerCLI.repo_labels(connection, repo_label)

    def test_20_generate_entitlement_certificate(self):
        '''Generate an entitlement certificate'''
        repo_label_1 = self.yum_repo_id_1.replace("-x86_64", "")
        repo_label_2 = self.yum_repo_id_2.replace("-x86_64", "")
        RHUIManagerCLI.client_cert(connection, [repo_label_1, repo_label_2], "atomic_and_my", 365, "/tmp")

    @staticmethod
    def test_21_create_client_configuration_rpm():
        '''Create a client configuration RPM'''
        RHUIManagerCLI.client_rpm(connection, "/tmp/atomic_and_my.key", "/tmp/atomic_and_my.crt", "1.0", "atomic_and_my", "/tmp", [custom_repo_name])

    @staticmethod
    def test_22_ensure_gpgcheck_in_client_configuration():
        '''Ensure that GPG checking is enabled in the client configuration'''
        raise nose.exc.SkipTest('currently not enabled (RHBZ#1428756)')
        Expect.expect_retval(connection, "grep -q '^gpgcheck\s*=\s*1$' /tmp/atomic_and_my-1.0/build/BUILD/atomic_and_my-1.0/rh-cloud.repo")

    @staticmethod
    def test_23_upload_expired_entitlement_certificate():
        '''Bonus: Check expired certificate handling'''
        # currently, an error occurs
        RHUIManagerCLI.cert_upload(connection, "/tmp/extra_rhui_files/rhcert_expired.pem", "An unexpected error has occurred during the last operation")
        # a relevant traceback is logged, though; check it
        Expect.ping_pong(connection, "tail -1 /root/.rhui/rhui.log", "InvalidOrExpiredCertificate")

    @staticmethod
    def test_24_upload_incompatible_entitlement_certificate():
        '''Bonus #2: Check incompatible certificate handling'''
        # an error message is printed right away
        RHUIManagerCLI.cert_upload(connection, "/tmp/extra_rhui_files/rhcert_incompatible.pem", "not compatible with the RHUI")

    @staticmethod
    def test_99_cleanup():
        '''Cleanup: Delete all repositories from RHUI (interactively; not currently supported by the CLI), remove certs and other files'''
        RHUIManagerRepo.delete_all_repos(connection)
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])
        RHUIManager.remove_rh_certs(connection)
        Expect.ping_pong(connection, "rm -rf /tmp/atomic_and_my* ; ls /tmp/atomic_and_my* 2>&1", "No such file or directory")

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
