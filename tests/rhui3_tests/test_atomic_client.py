'''Atomic client tests (RHEL 7 only)'''

from __future__ import print_function

from os.path import basename
import socket

import logging
import nose
import pytoml
from stitches.expect import Expect
import yaml

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.rhuimanager_sync import RHUIManagerSync
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

AH = ConMgr.get_atomic_cli_hostname()
try:
    socket.gethostbyname(AH)
    AH_EXISTS = True
    ATOMIC_CLI = ConMgr.connect(AH)
except socket.error:
    AH_EXISTS = False
RHUA = ConMgr.connect()

class TestClient():
    '''
       class for Atomic client tests
    '''

    def __init__(self):
        with open("/etc/rhui3_tests/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)

        self.atomic_repo_name = doc["atomic_repo"]["name"]
        self.atomic_repo_remote = doc["atomic_repo"]["remote"]
        self.atomic_repo_ref = doc["atomic_repo"]["ref"]

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
    def test_02_add_cds():
        '''
           add a CDS
        '''
        cds_list = RHUIManagerInstance.list(RHUA, "cds")
        nose.tools.assert_equal(cds_list, [])
        RHUIManagerInstance.add_instance(RHUA, "cds")

    @staticmethod
    def test_03_add_hap():
        '''
           add an HAProxy Load-balancer
        '''
        hap_list = RHUIManagerInstance.list(RHUA, "loadbalancers")
        nose.tools.assert_equal(hap_list, [])
        RHUIManagerInstance.add_instance(RHUA, "loadbalancers")

    @staticmethod
    def test_04_upload_atomic_cert():
        '''
           upload the Atomic cert
        '''
        entlist = RHUIManagerEntitlements.upload_rh_certificate(RHUA,
                                                                "/tmp/extra_rhui_files/" +
                                                                "rhcert_atomic.pem")
        nose.tools.assert_not_equal(len(entlist), 0)

    def test_05_add_atomic_repo(self):
        '''
           add the RHEL Atomic Host (Trees) from RHUI repo
        '''
        RHUIManagerRepo.add_rh_repo_by_product(RHUA, [self.atomic_repo_name])

    def test_06_start_atomic_repo_sync(self):
        '''
           start syncing the repo
        '''
        atomic_repo_version = RHUIManagerRepo.get_repo_version(RHUA, self.atomic_repo_name)
        RHUIManagerSync.sync_repo(RHUA,
                                  [Util.format_repo(self.atomic_repo_name, atomic_repo_version)])

    def test_07_generate_atomic_cert(self):
        '''
           generate an entitlement certificate for the repo
        '''
        RHUIManagerClient.generate_ent_cert(RHUA,
                                            [self.atomic_repo_name],
                                            "test_atomic_ent_cli",
                                            "/root/")
        Expect.expect_retval(RHUA, "test -f /root/test_atomic_ent_cli.crt")
        Expect.expect_retval(RHUA, "test -f /root/test_atomic_ent_cli.key")

    @staticmethod
    def test_08_create_atomic_pkg():
        '''
           create an Atomic client configuration package
        '''
        RHUIManagerClient.create_atomic_conf_pkg(RHUA,
                                                 "/root",
                                                 "test_atomic_pkg",
                                                 "/root/test_atomic_ent_cli.crt",
                                                 "/root/test_atomic_ent_cli.key")
        Expect.expect_retval(RHUA, "test -f /root/test_atomic_pkg.tar.gz")

    def test_09_wait_for_sync(self):
        '''
           wait until the repo is synced (takes a while)
        '''
        atomic_repo_version = RHUIManagerRepo.get_repo_version(RHUA, self.atomic_repo_name)
        RHUIManagerSync.wait_till_repo_synced(RHUA,
                                              [Util.format_repo(self.atomic_repo_name,
                                                                atomic_repo_version)])

    @staticmethod
    def test_10_install_atomic_pkg():
        '''
           install the Atomic client configuration package on the Atomic host
        '''
        if AH_EXISTS:
            Util.install_pkg_from_rhua(RHUA, ATOMIC_CLI, "/root/test_atomic_pkg.tar.gz")
        else:
            raise nose.exc.SkipTest("No known Atomic host")

    def test_11_sync_again(self):
        '''
           sync the repo again (workaround for RHBZ#1427190)
        '''
        atomic_repo_version = RHUIManagerRepo.get_repo_version(RHUA, self.atomic_repo_name)
        RHUIManagerSync.sync_repo(RHUA,
                                  [Util.format_repo(self.atomic_repo_name, atomic_repo_version)])
        RHUIManagerSync.wait_till_repo_synced(RHUA,
                                              [Util.format_repo(self.atomic_repo_name,
                                                                atomic_repo_version)])

    @staticmethod
    def test_12_wait_for_pulp_tasks():
        '''
            wait until the repo publish task is complete (takes extra time)
        '''
        RHUIManagerSync.wait_till_pulp_tasks_finish(RHUA)

    def test_13_pull_atomic_content(self):
        '''
           pull Atomic content
        '''
        if AH_EXISTS:
            Expect.expect_retval(ATOMIC_CLI,
                                 "ostree pull {0}:{1}".format(self.atomic_repo_remote,
                                                              self.atomic_repo_ref),
                                 timeout=200)
        else:
            raise nose.exc.SkipTest("No known Atomic host")

    def test_14_check_fetched_file(self):
        '''
           check if the repo data was fetched on the client
        '''
        if AH_EXISTS:
            Expect.expect_retval(ATOMIC_CLI,
                                 "test -f /sysroot/ostree/repo/refs/remotes/" +
                                 "{0}/{1}".format(self.atomic_repo_remote,
                                                  self.atomic_repo_ref))
        else:
            raise nose.exc.SkipTest("No known Atomic host")

    @staticmethod
    def test_15_check_registry_config():
        '''
           check if container registry configuration was modified
        '''
        if AH_EXISTS:
            _, stdout, _ = ATOMIC_CLI.exec_command("cat /etc/containers/registries.conf")
            cfg = pytoml.load(stdout)
            nose.tools.ok_("%s:5000" % ConMgr.get_cds_lb_hostname() in \
                           cfg["registries"]["search"]["registries"],
                           msg="unexpected configuration: %s" % cfg)
        else:
            raise nose.exc.SkipTest("No known Atomic host")

    def test_99_cleanup(self):
        '''
           remove the repo and RH cert, uninstall CDS and HAProxy, delete the ostree configuration
        '''
        RHUIManagerRepo.delete_all_repos(RHUA)
        nose.tools.assert_equal(RHUIManagerRepo.list(RHUA), [])
        RHUIManagerInstance.delete_all(RHUA, "loadbalancers")
        RHUIManagerInstance.delete_all(RHUA, "cds")
        Expect.expect_retval(RHUA, "rm -f /root/test_atomic_ent_cli*")
        Expect.expect_retval(RHUA, "rm -f /root/test_atomic_pkg.tar.gz")
        RHUIManager.remove_rh_certs(RHUA)
        if AH_EXISTS:
            Expect.expect_retval(ATOMIC_CLI, "ostree remote delete %s" % self.atomic_repo_remote)
            Expect.expect_retval(ATOMIC_CLI, "mv -f /etc/containers/registries.conf{.backup,}")

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
