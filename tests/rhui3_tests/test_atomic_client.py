'''Atomic client tests (RHEL 7+ only)'''

from __future__ import print_function

from os.path import basename
import socket

import logging
import nose
import pytoml
import stitches
from stitches.expect import Expect
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.rhuimanager_sync import RHUIManagerSync
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

AH = "atomiccli.example.com"
CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
ATOMIC_CLI = stitches.Connection(AH, "root", "/root/.ssh/id_rsa_test")


class TestClient(object):
    '''
       class for Atomic client tests
    '''

    def __init__(self):
        try:
            socket.gethostbyname(AH)
            self.ah_exists = True
        except socket.error:
            self.ah_exists = False

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
        RHUIManager.initial_run(CONNECTION)

    @staticmethod
    def test_02_add_cds():
        '''
           add a CDS
        '''
        cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
        nose.tools.assert_equal(cds_list, [])
        RHUIManagerInstance.add_instance(CONNECTION, "cds", "cds01.example.com")

    @staticmethod
    def test_03_add_hap():
        '''
           add an HAProxy Load-balancer
        '''
        hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
        nose.tools.assert_equal(hap_list, [])
        RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", "hap01.example.com")

    @staticmethod
    def test_04_upload_atomic_cert():
        '''
           upload the Atomic cert
        '''
        entlist = RHUIManagerEntitlements.upload_rh_certificate(CONNECTION,
                                                                "/tmp/extra_rhui_files/" +
                                                                "rhcert_atomic.pem")
        nose.tools.assert_not_equal(len(entlist), 0)

    def test_05_add_atomic_repo(self):
        '''
           add the RHEL Atomic Host (Trees) from RHUI repo
        '''
        RHUIManagerRepo.add_rh_repo_by_product(CONNECTION, [self.atomic_repo_name])

    def test_06_start_atomic_repo_sync(self):
        '''
           start syncing the repo
        '''
        atomic_repo_version = RHUIManagerRepo.get_repo_version(CONNECTION, self.atomic_repo_name)
        RHUIManagerSync.sync_repo(CONNECTION,
                                  [Util.format_repo(self.atomic_repo_name, atomic_repo_version)])

    def test_07_generate_atomic_cert(self):
        '''
           generate an entitlement certificate for the repo
        '''
        RHUIManagerClient.generate_ent_cert(CONNECTION,
                                            [self.atomic_repo_name],
                                            "test_atomic_ent_cli",
                                            "/root/")
        Expect.expect_retval(CONNECTION, "test -f /root/test_atomic_ent_cli.crt")
        Expect.expect_retval(CONNECTION, "test -f /root/test_atomic_ent_cli.key")

    @staticmethod
    def test_08_create_atomic_pkg():
        '''
           create an Atomic client configuration package
        '''
        RHUIManagerClient.create_atomic_conf_pkg(CONNECTION,
                                                 "/root",
                                                 "test_atomic_pkg",
                                                 "/root/test_atomic_ent_cli.crt",
                                                 "/root/test_atomic_ent_cli.key")
        Expect.expect_retval(CONNECTION, "test -f /root/test_atomic_pkg.tar.gz")

    def test_09_wait_for_sync(self):
        '''
           wait until the repo is synced (takes a while)
        '''
        atomic_repo_version = RHUIManagerRepo.get_repo_version(CONNECTION, self.atomic_repo_name)
        RHUIManagerSync.wait_till_repo_synced(CONNECTION,
                                              [Util.format_repo(self.atomic_repo_name,
                                                                atomic_repo_version)])

    def test_10_install_atomic_pkg(self):
        '''
           install the Atomic client configuration package on the Atomic host
        '''
        if self.ah_exists:
            Util.install_pkg_from_rhua(CONNECTION, ATOMIC_CLI, "/root/test_atomic_pkg.tar.gz")
        else:
            raise nose.exc.SkipTest("No known Atomic host")

    def test_11_sync_again(self):
        '''
           sync the repo again (workaround for RHBZ#1427190)
        '''
        atomic_repo_version = RHUIManagerRepo.get_repo_version(CONNECTION, self.atomic_repo_name)
        RHUIManagerSync.sync_repo(CONNECTION,
                                  [Util.format_repo(self.atomic_repo_name, atomic_repo_version)])
        RHUIManagerSync.wait_till_repo_synced(CONNECTION,
                                              [Util.format_repo(self.atomic_repo_name,
                                                                atomic_repo_version)])

    @staticmethod
    def test_12_wait_for_pulp_tasks():
        '''
            wait until the repo publish task is complete (takes extra time)
        '''
        RHUIManagerSync.wait_till_pulp_tasks_finish(CONNECTION)

    def test_13_pull_atomic_content(self):
        '''
           pull Atomic content
        '''
        if self.ah_exists:
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
        if self.ah_exists:
            Expect.expect_retval(ATOMIC_CLI,
                                 "test -f /sysroot/ostree/repo/refs/remotes/" +
                                 "{0}/{1}".format(self.atomic_repo_remote,
                                                  self.atomic_repo_ref))
        else:
            raise nose.exc.SkipTest("No known Atomic host")

    def test_15_check_registry_config(self):
        '''
           check if container registry configuration was modified
        '''
        if self.ah_exists:
            _, stdout, _ = ATOMIC_CLI.exec_command("cat /etc/containers/registries.conf")
            cfg = pytoml.load(stdout)
            nose.tools.ok_("cds.example.com:5000" in cfg["registries"]["search"]["registries"],
                           msg="unexpected configuration: %s" % cfg)

        else:
            raise nose.exc.SkipTest("No known Atomic host")

    def test_99_cleanup(self):
        '''
           remove the repo and RH cert, uninstall CDS and HAProxy, delete the ostree configuration
        '''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])
        RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(CONNECTION, "cds", ["cds01.example.com"])
        Expect.expect_retval(CONNECTION, "rm -f /root/test_atomic_ent_cli*")
        Expect.expect_retval(CONNECTION, "rm -f /root/test_atomic_pkg.tar.gz")
        RHUIManager.remove_rh_certs(CONNECTION)
        if self.ah_exists:
            Expect.expect_retval(ATOMIC_CLI, "ostree remote delete %s" % self.atomic_repo_remote)
            Expect.expect_retval(ATOMIC_CLI, "mv -f /etc/containers/registries.conf{.backup,}")

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
