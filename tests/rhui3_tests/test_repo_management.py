#! /usr/bin/python -tt
''' Repository management tests '''

from os.path import basename

import logging
import nose
import stitches
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

class TestRepo(object):
    '''
       class for repository manipulation tests
    '''

    def __init__(self):
        with open('/usr/share/rhui3_tests_lib/config/tested_repos.yaml', 'r') as configfile:
            doc = yaml.load(configfile)

        self.yum_repo_name = doc['yum_repo1']['name']
        self.yum_repo_version = doc['yum_repo1']['version']
        self.yum_repo_kind = doc['yum_repo1']['kind']
        self.docker_container_name = doc['docker_container1']['name']
        self.docker_container_displayname = doc['docker_container1']['displayname']

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_repo_setup():
        '''Do initial rhui-manager run, upload RH cert'''
        RHUIManager.initial_run(CONNECTION)
        entlist = RHUIManagerEntitlements.upload_rh_certificate(CONNECTION)
        nose.tools.assert_not_equal(len(entlist), 0)

    @staticmethod
    def test_02_check_empty_repo_list():
        '''Check if the repolist is empty'''
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_03_create_3_custom_repos():
        '''Create 3 custom repos (protected, unprotected, no RH GPG check) '''
        RHUIManagerRepo.add_custom_repo(CONNECTION,
                                        "custom-i386-x86_64",
                                        "",
                                        "custom/i386/x86_64",
                                        "1",
                                        "y")
        RHUIManagerRepo.add_custom_repo(CONNECTION,
                                        "custom-x86_64-x86_64",
                                        "",
                                        "custom/x86_64/x86_64",
                                        "1",
                                        "n")
        RHUIManagerRepo.add_custom_repo(CONNECTION,
                                        "custom-i386-i386",
                                        "",
                                        "custom/i386/i386",
                                        "1",
                                        "y",
                                        "",
                                        "n")

    @staticmethod
    def test_04_check_custom_repo_list():
        '''Check if the repolist contains 3 custom repos'''
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION),
                                ['custom-i386-i386', 'custom-i386-x86_64', 'custom-x86_64-x86_64'])

    @staticmethod
    def test_05_repo_id_uniqness():
        '''Check that repo id is unique'''
        RHUIManagerRepo.add_custom_repo(CONNECTION,
                                        "custom-i386-x86_64",
                                        "",
                                        "custom/i386/x86_64",
                                        "1",
                                        "y")

    @staticmethod
    def test_06_upload_to_custom_repo():
        '''Upload content to the custom repo'''
        RHUIManagerRepo.upload_content(CONNECTION,
                                       ["custom-i386-x86_64"],
                                       "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")

    @staticmethod
    def test_06_01_upload_several_rpms():
        '''Upload several rpms to the custom repo from a directory'''
        RHUIManagerRepo.upload_content(CONNECTION,
                                       ["custom-i386-x86_64"],
                                       "/tmp/extra_rhui_files/")

    @staticmethod
    def test_06_02_check_for_package():
        '''Check the packages list'''
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(CONNECTION,
                                                                  "custom-i386-x86_64",
                                                                  ""),
                                ["rhui-rpm-upload-test-1-1.noarch.rpm",
                                 "rhui-rpm-upload-trial-1-1.noarch.rpm"])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(CONNECTION,
                                                                  "custom-i386-x86_64",
                                                                  "rhui-rpm-upload-test"),
                                ["rhui-rpm-upload-test-1-1.noarch.rpm"])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(CONNECTION,
                                                                  "custom-i386-x86_64",
                                                                  "test"),
                                [])
        nose.tools.assert_equal(RHUIManagerRepo.check_for_package(CONNECTION,
                                                                  "custom-x86_64-x86_64",
                                                                  ""),
                                [])

    @staticmethod
    def test_07_remove_3_custom_repos():
        '''Remove 3 custom repos'''
        RHUIManagerRepo.delete_repo(CONNECTION,
                                    ["custom-i386-x86_64",
                                     "custom-x86_64-x86_64",
                                     "custom-i386-i386"])
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_08_add_rh_repo_by_repo(self):
        '''Add a RH repo by repository'''
        RHUIManagerRepo.add_rh_repo_by_repo(CONNECTION, [Util.format_repo(self.yum_repo_name,
                                                                          self.yum_repo_version,
                                                                          self.yum_repo_kind)])
        nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_09_delete_one_repo(self):
        '''Remove a RH repo'''
        RHUIManagerRepo.delete_repo(CONNECTION, [self.yum_repo_name + ".*"])
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_10_add_rh_repo_by_product(self):
        '''Add a RH repo by product'''
        RHUIManagerRepo.add_rh_repo_by_product(CONNECTION, [self.yum_repo_name])
        #nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_11_delete_repo():
        '''Remove a RH repo'''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_12_add_all_rh_repos():
        '''Add all RH repos'''
        RHUIManagerRepo.add_rh_repo_all(CONNECTION)
        #nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_13_delete_all_repos():
        '''Delete all repositories from RHUI'''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_14_add_docker_container(self):
        '''Add a RH docker container'''
        RHUIManagerRepo.add_docker_container(CONNECTION,
                                             self.docker_container_name,
                                             "",
                                             self.docker_container_displayname)
        nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_15_delete_docker_container():
        '''Delete a docker container'''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_16_delete_rh_cert():
        '''Delete the RH cert'''
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
