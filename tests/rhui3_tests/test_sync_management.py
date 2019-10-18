'''Repo syncing and scheduling tests'''

from __future__ import print_function

from os.path import basename

import logging
import nose
import stitches
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.rhuimanager_sync import RHUIManagerSync
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

class TestSync(object):
    '''
       class for repository synchronization tests
    '''

    def __init__(self):
        # Test the RHEL-7 ARM-64 repo for a change
        version = 7
        arch = "aarch64"
        with open("/etc/rhui3_tests/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)
            try:
                self.yum_repo_name = doc["yum_repos"][version][arch]["name"]
                self.yum_repo_version = doc["yum_repos"][version][arch]["version"]
                self.yum_repo_kind = doc["yum_repos"][version][arch]["kind"]
            except KeyError as version:
                raise nose.SkipTest("No test repo defined for RHEL %s on %s" % (version, arch))

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    def test_01_setup(self):
        '''log in to rhui-manager, upload RH cert, add a repo to sync '''
        RHUIManager.initial_run(CONNECTION)
        entlist = RHUIManagerEntitlements.upload_rh_certificate(CONNECTION)
        nose.tools.assert_not_equal(len(entlist), 0)
        RHUIManagerRepo.add_rh_repo_by_repo(CONNECTION, [Util.format_repo(self.yum_repo_name,
                                                                          self.yum_repo_version,
                                                                          self.yum_repo_kind)])

    def test_02_sync_repo(self):
        '''sync a RH repo '''
        RHUIManagerSync.sync_repo(CONNECTION, [Util.format_repo(self.yum_repo_name,
                                                                self.yum_repo_version)])

    def test_03_check_sync_started(self):
        '''ensure that the sync started'''
        RHUIManagerSync.check_sync_started(CONNECTION, [Util.format_repo(self.yum_repo_name,
                                                                         self.yum_repo_version)])

    def test_04_wait_till_repo_synced(self):
        '''wait until the repo is synced'''
        RHUIManagerSync.wait_till_repo_synced(CONNECTION, [Util.format_repo(self.yum_repo_name,
                                                                            self.yum_repo_version)])

    def test_99_cleanup(self):
        '''remove the RH repo and cert'''
        RHUIManagerRepo.delete_repo(CONNECTION, [self.yum_repo_name + ".*"])
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
