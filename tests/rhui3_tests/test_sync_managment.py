import nose, stitches, yaml, time

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanager_sync import *
from rhui3_tests_lib.rhuimanager_entitlement import *

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_setup():
    '''do rhui-manager login, upload RH cert, add a repo to sync '''
    RHUIManager.initial_run(connection)
    RHUIManagerEntitlements.upload_rh_certificate(connection)
    RHUIManagerRepo.add_rh_repo_by_repo(connection, ["Red Hat Update Infrastructure 2.0 \(RPMs\) \(6Server-x86_64\) \(Yum\)"])

def test_02_sync_repo():
    '''sync a RH repo '''
    RHUIManagerSync.sync_repo(connection, ["Red Hat Update Infrastructure 2.0 \(RPMs\) \(6Server-x86_64\)"])

def test_03_check_sync_status():
    '''check sync status of the repo'''
    Expect.ping_pong(connection, "rhui-manager status | grep \"Red Hat Update Infrastructure 2.0 (RPMs) (6Server-x86_64)\" | grep \"SUCCESS\|SYNCING\" && echo SUCCESS", "[^ ]SUCCESS", 120)

def test_04_cleanup():
    '''Wait until repo is synced and remove it then'''
    RHUIManagerSync.wait_till_repo_synced(connection, ["Red Hat Update Infrastructure 2.0 \(RPMs\) \(6Server-x86_64\)"])

    '''remove the RH repo '''
    RHUIManagerRepo.delete_repo(connection, ["Red Hat Update Infrastructure 2.0 \(RPMs\).*"])

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)
