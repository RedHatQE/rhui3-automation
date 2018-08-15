'''Atomic client tests (RHEL 7+ only)'''

from os.path import basename

import logging
import nose
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

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
ATOMIC_CLI = stitches.Connection("atomiccli.example.com", "root", "/root/.ssh/id_rsa_test")


class TestClient(object):
    '''
       class for Atomic client tests
    '''

    def __init__(self):
        self.rhua_os_version = Util.get_rhua_version(CONNECTION)["major"]
        if self.rhua_os_version < 7:
            raise nose.exc.SkipTest('Not supported on RHEL ' + str(self.rhua_os_version))

        with open('/usr/share/rhui3_tests_lib/config/tested_repos.yaml', 'r') as configfile:
            doc = yaml.load(configfile)

        self.atomic_repo_name = doc['atomic_repo']['name']
        self.atomic_repo_remote = doc['atomic_repo']['remote']
        self.atomic_repo_ref = doc['atomic_repo']['ref']

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_initial_run():
        '''do initial rhui-manager run'''
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

    @staticmethod
    def test_10_install_atomic_pkg():
        '''
           install the Atomic client configuration package on the Atomic host
        '''
        Util.install_pkg_from_rhua(CONNECTION, ATOMIC_CLI, "/root/test_atomic_pkg.tar.gz")

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
        Expect.expect_retval(ATOMIC_CLI,
                             "ostree pull {0}:{1}".format(self.atomic_repo_remote,
                                                          self.atomic_repo_ref),
                             timeout=200)

    def test_14_check_fetched_file(self):
        '''
           check if the repo data was fetched on the client
        '''
        Expect.expect_retval(ATOMIC_CLI,
                             "test -f /sysroot/ostree/repo/refs/remotes/" +
                             "{0}/{1}".format(self.atomic_repo_remote,
                                              self.atomic_repo_ref))

    def test_99_cleanup(self):
        '''
           remove the repo, uninstall CDS and HAProxy, delete the configuration package and RH cert
        '''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])
        RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(CONNECTION, "cds", ["cds01.example.com"])
        Expect.expect_retval(CONNECTION, "rm -f /root/test_atomic_ent_cli*")
        Expect.expect_retval(CONNECTION, "rm -f /root/test_atomic_pkg.tar.gz")
        Expect.expect_retval(ATOMIC_CLI,
                             "ostree remote delete " + self.atomic_repo_remote)
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
