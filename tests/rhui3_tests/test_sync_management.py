'''Repo syncing and scheduling tests'''

import nose, stitches, yaml, time, logging

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanager_sync import *
from rhui3_tests_lib.rhuimanager_entitlement import *
from rhui3_tests_lib.util import Util

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

class TestSync(object):
    '''
       class for repository synchronization tests
    '''

    def __init__(self):
        with open('/tmp/rhui3-tests/tests/rhui3_tests/tested_repos.yaml', 'r') as file:
            doc = yaml.load(file)

        self.yum_repo_name = doc['yum_repo1']['name']
        self.yum_repo_version = doc['yum_repo1']['version']
        self.yum_repo_kind = doc['yum_repo1']['kind']

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    def test_01_setup(self):
        '''do rhui-manager login, upload RH cert, add a repo to sync '''
        RHUIManager.initial_run(connection)
        list = RHUIManagerEntitlements.upload_rh_certificate(connection)
        nose.tools.assert_not_equal(len(list), 0)
        RHUIManagerRepo.add_rh_repo_by_repo(connection, [Util.format_repo(self.yum_repo_name,
                                                                          self.yum_repo_version,
                                                                          self.yum_repo_kind)])

    def test_02_sync_repo(self):
        '''sync a RH repo '''
        RHUIManagerSync.sync_repo(connection, [Util.format_repo(self.yum_repo_name,
                                                                self.yum_repo_version)])

    def test_03_check_sync_started(self):
        '''ensure that sync started'''
        RHUIManagerSync.check_sync_started(connection, [Util.format_repo(self.yum_repo_name,
                                                                         self.yum_repo_version)])

    def test_04_wait_till_repo_synced(self):
        '''wait until repo is synced'''
        RHUIManagerSync.wait_till_repo_synced(connection, [Util.format_repo(self.yum_repo_name,
                                                                            self.yum_repo_version)])

    def test_99_cleanup(self):
        '''remove the RH repo and cert'''
        RHUIManagerRepo.delete_repo(connection, [self.yum_repo_name + ".*"])
        RHUIManager.remove_rh_certs(connection)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
