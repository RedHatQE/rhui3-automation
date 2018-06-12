#! /usr/bin/python -tt
''' Repository management tests '''

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanager_entitlement import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

class TestRepo(object):
    '''
       class for repository manipulation tests
    '''

    def __init__(self):
        with open('/tmp/rhui3-tests/tests/rhui3_tests/tested_repos.yaml', 'r') as file:
            doc = yaml.load(file)

        self.yum_repo_name = doc['yum_repo1']['name']
        self.yum_repo_version = doc['yum_repo1']['version']

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_repo_setup():
        '''Do initial rhui-manager run, upload RH cert'''
        RHUIManager.initial_run(connection)
        list = RHUIManagerEntitlements.upload_rh_certificate(connection)
        nose.tools.assert_not_equal(len(list), 0)

    @staticmethod
    def test_02_check_empty_repo_list():
        '''Check if the repolist is empty'''
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_03_create_3_custom_repos():
        '''Create 3 custom repos (protected, unprotected, no RH GPG check) '''
        RHUIManagerRepo.add_custom_repo(connection, "custom-i386-x86_64", "", "custom/i386/x86_64", "1", "y")
        RHUIManagerRepo.add_custom_repo(connection, "custom-x86_64-x86_64", "", "custom/x86_64/x86_64", "1", "n")
        RHUIManagerRepo.add_custom_repo(connection, "custom-i386-i386", "", "custom/i386/i386", "1", "y", "", "n" )

    @staticmethod
    def test_04_check_custom_repo_list():
        '''Check if the repolist contains 3 custom repos'''
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), ['custom-i386-i386', 'custom-i386-x86_64', 'custom-x86_64-x86_64'])

    @staticmethod
    def test_05_repo_id_uniqness():
        '''Check that repo id is unique'''
        RHUIManagerRepo.add_custom_repo(connection, "custom-i386-x86_64", "", "custom/i386/x86_64", "1", "y")

    @staticmethod
    def test_06_upload_rpm_to_custom_repo():
        '''Upload content to the custom repo'''
        RHUIManagerRepo.upload_content(connection, ["custom-i386-x86_64"], "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")

    @staticmethod
    def test_06_01_upload_several_rpms_to_custom_repo():
        '''Upload several rpms to the custom repo from a directory'''
        RHUIManagerRepo.upload_content(connection, ["custom-i386-x86_64"], "/tmp/extra_rhui_files/")

    @staticmethod
    def test_06_02_check_for_package():
        '''Check the packages list'''
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(connection, "custom-i386-x86_64", ""), ["rhui-rpm-upload-test-1-1.noarch.rpm", "rhui-rpm-upload-trial-1-1.noarch.rpm"])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(connection, "custom-i386-x86_64", "rhui-rpm-upload-test"), ["rhui-rpm-upload-test-1-1.noarch.rpm"])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(connection, "custom-i386-x86_64", "test"), [])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(connection, "custom-x86_64-x86_64", ""), [])

    @staticmethod
    def test_07_remove_3_custom_repos():
        '''Remove 3 custom repos'''
        RHUIManagerRepo.delete_repo(connection, ["custom-i386-x86_64", "custom-x86_64-x86_64", "custom-i386-i386"])
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    def test_08_add_rh_repo_by_repository(self):
        '''Add a RH repo by repository'''
        RHUIManagerRepo.add_rh_repo_by_repo(connection,
                                            [self.yum_repo_name +
                                             " (" + self.yum_repo_version + ") (Yum)"])
        nose.tools.assert_not_equal(RHUIManagerRepo.list(connection), [])

    def test_09_delete_one_repo(self):
        '''Remove a RH repo'''
        RHUIManagerRepo.delete_repo(connection, [self.yum_repo_name + ".*"])
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    def test_10_add_rh_repo_by_product(self):
        '''Add a RH repo by product'''
        RHUIManagerRepo.add_rh_repo_by_product(connection, [self.yum_repo_name])
        #nose.tools.assert_not_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_11_delete_repo():
        '''Remove a RH repo'''
        RHUIManagerRepo.delete_all_repos(connection)
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_12_add_all_rh_repos():
         '''Add all RH repos'''
         RHUIManagerRepo.add_rh_repo_all(connection)
         #nose.tools.assert_not_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_13_delete_all_repos():
        '''Delete all repositories from RHUI'''
        RHUIManagerRepo.delete_all_repos(connection)
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_14_add_docker_container():
        '''Add a RH docker container'''
        RHUIManagerRepo.add_docker_container(connection, "rhcertification/redhat-certification", "", "RH Certification Docker")
        nose.tools.assert_not_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_15_delete_docker_container():
        '''Delete a docker container'''
        RHUIManagerRepo.delete_all_repos(connection)
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

    @staticmethod
    def test_16_delete_rh_cert():
        '''Delete the RH cert'''
        RHUIManager.remove_rh_certs(connection)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
