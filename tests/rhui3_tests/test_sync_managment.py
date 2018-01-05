'''Repo syncing and scheduling tests'''

import nose, stitches, yaml, time

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanager_sync import *
from rhui3_tests_lib.rhuimanager_entitlement import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

with open('/tmp/rhui3-tests/tests/rhui3_tests/tested_repos.yaml', 'r') as file:
    doc = yaml.load(file)

yum_repo_name = doc['yum_repo1']['name']
yum_repo_version = doc['yum_repo1']['version']

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_setup():
    '''do rhui-manager login, upload RH cert, add a repo to sync '''
    RHUIManager.initial_run(connection)
    list = RHUIManagerEntitlements.upload_rh_certificate(connection)
    nose.tools.assert_not_equal(len(list), 0)
    RHUIManagerRepo.add_rh_repo_by_repo(connection, [yum_repo_name + yum_repo_version + " \(Yum\)"])

def test_02_sync_repo():
    '''sync a RH repo '''
    RHUIManagerSync.sync_repo(connection, [yum_repo_name + yum_repo_version])

def test_03_check_sync_started():
    '''ensure that sync started'''
    RHUIManagerSync.check_sync_started(connection, [yum_repo_name + yum_repo_version])

def test_04_wait_till_repo_synced():
    '''wait until repo is synced'''
    RHUIManagerSync.wait_till_repo_synced(connection, [yum_repo_name + yum_repo_version])

def test_99_cleanup():
    '''remove the RH repo and cert'''
    RHUIManagerRepo.delete_repo(connection, [yum_repo_name + ".*"])
    RHUIManager.remove_rh_certs(connection)

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)
