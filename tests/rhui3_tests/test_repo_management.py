#! /usr/bin/python -tt
''' Repository management tests '''

from os.path import basename

import logging
import nose
import stitches
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements
from rhui3_tests_lib.rhuimanager_repo import AlreadyExistsError, RHUIManagerRepo
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
        self.yum_repo_path = doc['yum_repo1']['path']
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
        '''log in to RHUI'''
        RHUIManager.initial_run(CONNECTION)
        entlist = RHUIManagerEntitlements.upload_rh_certificate(CONNECTION)
        nose.tools.assert_not_equal(len(entlist), 0)

    @staticmethod
    def test_02_check_empty_repo_list():
        '''check if the repolist is empty'''
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_03_create_3_custom_repos():
        '''create 3 custom repos (protected, unprotected, no RH GPG check) '''
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
        '''check if the repolist contains the 3 custom repos'''
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION),
                                ['custom-i386-i386', 'custom-i386-x86_64', 'custom-x86_64-x86_64'])

    @staticmethod
    def test_05_repo_id_uniqueness():
        '''verify that rhui-manager refuses to create a custom repo whose name already exists'''
        nose.tools.assert_raises(AlreadyExistsError,
                                 RHUIManagerRepo.add_custom_repo,
                                 CONNECTION,
                                 "custom-i386-x86_64")

    @staticmethod
    def test_06_upload_to_custom_repo():
        '''upload content to the custom repo'''
        RHUIManagerRepo.upload_content(CONNECTION,
                                       ["custom-i386-x86_64"],
                                       "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")

    @staticmethod
    def test_07_upload_several_rpms():
        '''upload several rpms to the custom repo from a directory'''
        RHUIManagerRepo.upload_content(CONNECTION,
                                       ["custom-i386-x86_64"],
                                       "/tmp/extra_rhui_files/")

    @staticmethod
    def test_08_check_for_package():
        '''check package lists'''
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
    def test_09_display_custom_repos():
        '''check detailed information on the custom repos'''
        RHUIManagerRepo.check_detailed_information(CONNECTION,
                                                   ["custom-i386-x86_64", "custom/i386/x86_64"],
                                                   [True, True],
                                                   [True, None, True],
                                                   2)
        RHUIManagerRepo.check_detailed_information(CONNECTION,
                                                   ["custom-x86_64-x86_64", "custom/x86_64/x86_64"],
                                                   [True, False],
                                                   [True, None, True],
                                                   0)
        RHUIManagerRepo.check_detailed_information(CONNECTION,
                                                   ["custom-i386-i386", "custom/i386/i386"],
                                                   [True, True],
                                                   [False],
                                                   0)

    @staticmethod
    def test_10_remove_3_custom_repos():
        '''remove the 3 custom repos'''
        RHUIManagerRepo.delete_repo(CONNECTION,
                                    ["custom-i386-x86_64",
                                     "custom-x86_64-x86_64",
                                     "custom-i386-i386"])
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_11_add_rh_repo_by_repo(self):
        '''add a RH repo by repository'''
        RHUIManagerRepo.add_rh_repo_by_repo(CONNECTION, [Util.format_repo(self.yum_repo_name,
                                                                          self.yum_repo_version,
                                                                          self.yum_repo_kind)])
        nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_12_display_rh_repo(self):
        '''check detailed information on the RH repo'''
        RHUIManagerRepo.check_detailed_information(CONNECTION,
                                                   [Util.format_repo(self.yum_repo_name,
                                                                     self.yum_repo_version),
                                                    self.yum_repo_path],
                                                   [False],
                                                   [True, None, True],
                                                   0)

    def test_13_delete_one_repo(self):
        '''remove the RH repo'''
        RHUIManagerRepo.delete_repo(CONNECTION, [self.yum_repo_name + ".*"])
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_14_add_rh_repo_by_product(self):
        '''add a RH repo by product'''
        RHUIManagerRepo.add_rh_repo_by_product(CONNECTION, [self.yum_repo_name])
        #nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_15_delete_repo():
        '''remove the RH repo'''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_16_add_all_rh_repos():
        '''add all RH repos'''
        RHUIManagerRepo.add_rh_repo_all(CONNECTION)
        #nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_17_delete_all_repos():
        '''delete all the repos'''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_18_add_docker_container(self):
        '''add a Docker container'''
        RHUIManagerRepo.add_docker_container(CONNECTION,
                                             self.docker_container_name,
                                             "",
                                             self.docker_container_displayname)
        nose.tools.assert_not_equal(RHUIManagerRepo.list(CONNECTION), [])

    def test_19_display_docker_cont(self):
        '''check detailed information on the Docker container'''
        RHUIManagerRepo.check_detailed_information(CONNECTION,
                                                   [self.docker_container_displayname,
                                                    "https://cds.example.com/pulp/docker/%s/" % \
                                                    self.docker_container_name.replace("/", "_")],
                                                   [False],
                                                   [True, None, True],
                                                   0)

    @staticmethod
    def test_20_delete_docker_container():
        '''delete the Docker container'''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])

    @staticmethod
    def test_99_delete_rh_cert():
        '''delete the RH cert'''
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
