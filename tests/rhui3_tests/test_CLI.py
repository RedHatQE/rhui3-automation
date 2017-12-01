#! /usr/bin/python -tt

import nose, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanagercli import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

with open('/tmp/rhui3-tests/tests/rhui3_tests/tested_repos.yaml', 'r') as file:
    doc = yaml.load(file)

yum_repo_name_1 = doc['CLI_repo1']['name']
yum_repo_id_1 = doc['CLI_repo1']['id']
yum_repo_name_2 = doc['CLI_repo2']['name']
yum_repo_id_2 = doc['CLI_repo2']['id']

custom_repo_name = "my_custom_repo"

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_initial_run():
    '''Do an initial rhui-manager run to make sure we are logged in'''
    RHUIManager.initial_run(connection)

def test_02_check_empty_repo_list():
    '''Check if the repolist is empty (interactively; not currently supported by the CLI)'''
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

def test_03_remove_existing_entitlement_certificates():
    '''Clean up uploaded entitlement certificates'''
    RHUIManager.remove_rh_certs(connection)

def test_04_create_custom_repo():
    '''Create a custom repo for further testing (interactively; not currently supported by the CLI)'''
    RHUIManagerRepo.add_custom_repo(connection, custom_repo_name, entitlement="n")

def test_05_check_custom_repo():
    '''Check if the custom repo was actually created'''
    RHUIManagerCLI.repo_list(connection, custom_repo_name, custom_repo_name)

def test_06_upload_rpm_to_custom_repo():
    '''Upload content to the custom repo'''
    RHUIManagerCLI.packages_upload(connection, custom_repo_name, "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")

def test_07_check_package_in_custom_repo():
    '''Check that the uploaded package is now in the repo'''
    RHUIManagerCLI.packages_list(connection, custom_repo_name, "rhui-rpm-upload-test-1-1.noarch.rpm")

def test_08_upload_entitlement_certificate():
    '''Upload the Atomic (the small) entitlement certificate'''
    RHUIManagerCLI.cert_upload(connection, "/tmp/extra_rhui_files/rhcert_atomic.pem", "Atomic")

def test_09_check_certificate_info():
    '''Check certificate info for validity'''
    RHUIManagerCLI.cert_info(connection)

def test_10_check_certificate_expiration():
    '''Check if the certificate expiration date is OK'''
    RHUIManagerCLI.cert_expiration(connection)

def test_11_check_unused_product():
    '''Check if a repo is available'''
    RHUIManagerCLI.repo_unused(connection, yum_repo_name_1)

def test_12_add_rh_repo_by_product():
    '''Add a Red Hat repo by its product name'''
    RHUIManagerCLI.repo_add(connection, yum_repo_name_1)

def test_13_add_rh_repo_by_id():
    '''Add a Red Hat repo by its ID'''
    RHUIManagerCLI.repo_add_by_repo(connection, [yum_repo_id_2])

def test_14_repo_list():
    '''Check the added repos'''
    RHUIManagerCLI.repo_list(connection, yum_repo_id_1, yum_repo_name_1)
    RHUIManagerCLI.repo_list(connection, yum_repo_id_2, yum_repo_name_2)

def test_15_no_unexpected_repos():
    '''Check if no stray repo was added'''
    RHUIManagerCLI.validate_repo_list(connection, [yum_repo_id_1, yum_repo_id_2, custom_repo_name])

def test_16_start_syncing_repo():
    '''Start syncing one of the repos'''
    RHUIManagerCLI.repo_sync(connection, yum_repo_id_2, yum_repo_name_2)

def test_17_repo_info():
    '''Verify that the repo name is part of the information about the specified repo ID'''
    RHUIManagerCLI.repo_info(connection, yum_repo_id_2, yum_repo_name_2)

def test_18_check_package_in_repo():
    '''Check a random package in the repo'''
    RHUIManagerCLI.packages_list(connection, yum_repo_id_2, "ostree")

def test_19_list_labels():
    '''Check repo labels'''
    repo_label = yum_repo_id_1.replace("-x86_64", "")
    RHUIManagerCLI.repo_labels(connection, repo_label)

def test_20_generate_entitlement_certificate():
    '''Generate an entitlement certificate'''
    repo_label_1 = yum_repo_id_1.replace("-x86_64", "")
    repo_label_2 = yum_repo_id_2.replace("-x86_64", "")
    RHUIManagerCLI.client_cert(connection, [repo_label_1, repo_label_2], "atomic_and_my", 365, "/tmp")

def test_21_create_client_configuration_rpm():
    '''Create a client configuration RPM'''
    RHUIManagerCLI.client_rpm(connection, "/tmp/atomic_and_my.key", "/tmp/atomic_and_my.crt", "1.0", "atomic_and_my", "/tmp", [custom_repo_name])

def test_22_cleanup():
    '''Cleanup: Delete all repositories from RHUI (interactively; not currently supported by the CLI), remove certs and other files'''
    RHUIManagerRepo.delete_all_repos(connection)
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])
    RHUIManager.remove_rh_certs(connection)
    Expect.ping_pong(connection, "rm -rf /tmp/atomic_and_my* ; ls /tmp/atomic_and_my* 2>&1", "No such file or directory")

def test_23_upload_entitlement_certificate():
    '''Bonus: Check expired certificate handling'''
    # currently, an error occurs
    RHUIManagerCLI.cert_upload(connection, "/tmp/extra_rhui_files/rhcert_expired.pem", "An unexpected error has occurred during the last operation")
    # a relevant traceback is logged, though; check it
    Expect.ping_pong(connection, "tail -1 /root/.rhui/rhui.log", "InvalidOrExpiredCertificate")

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)
