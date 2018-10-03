'''Client management tests'''

from os.path import basename

import logging
import nose
import requests
import stitches
from stitches.expect import Expect
import urllib3
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.rhuimanager_sync import RHUIManagerSync
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
CLI = stitches.Connection("cli01.example.com", "root", "/root/.ssh/id_rsa_test")

TEST_PACKAGE = "vm-dump-metrics"

class TestClient(object):
    '''
       class for client tests
    '''

    def __init__(self):
        self.rhua_os_version = Util.get_rhel_version(CONNECTION)["major"]

        with open('/usr/share/rhui3_tests_lib/config/tested_repos.yaml', 'r') as configfile:
            doc = yaml.load(configfile)

        self.yum_repo1_name = doc['yum_repo1']['name']
        self.yum_repo1_version = doc['yum_repo1']['version']
        self.yum_repo1_kind = doc['yum_repo1']['kind']
        self.yum_repo1_path = doc['yum_repo1']['path']
        self.yum_repo2_name = doc['yum_repo2']['name']
        self.yum_repo2_version = doc['yum_repo2']['version']
        self.yum_repo2_kind = doc['yum_repo2']['kind']
        self.yum_repo2_path = doc['yum_repo2']['path']

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

    @staticmethod
    def test_02_upload_rh_certificate():
        '''
           upload a new or updated Red Hat content certificate
        '''
        entlist = RHUIManagerEntitlements.upload_rh_certificate(CONNECTION)
        nose.tools.assert_not_equal(len(entlist), 0)

    @staticmethod
    def test_03_add_cds():
        '''
            add a CDS
        '''
        cds_list = RHUIManagerInstance.list(CONNECTION, "cds")
        nose.tools.assert_equal(cds_list, [])
        RHUIManagerInstance.add_instance(CONNECTION, "cds", "cds01.example.com")

    @staticmethod
    def test_04_add_hap():
        '''
            add an HAProxy Load-balancer
        '''
        hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
        nose.tools.assert_equal(hap_list, [])
        RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", "hap01.example.com")

    def test_05_add_upload_sync_stuff(self):
        '''
           add a custom and RH content repos to protect by a cli entitlement cert, upload rpm, sync
        '''
        RHUIManagerRepo.add_custom_repo(CONNECTION,
                                        "custom-i386-x86_64",
                                        "",
                                        "custom/i386/x86_64",
                                        "1",
                                        "y")
        RHUIManagerRepo.upload_content(CONNECTION,
                                       ["custom-i386-x86_64"],
                                       "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")
        RHUIManagerRepo.add_rh_repo_by_repo(CONNECTION,
                                            [Util.format_repo(self.yum_repo1_name,
                                                              self.yum_repo1_version,
                                                              self.yum_repo1_kind),
                                             Util.format_repo(self.yum_repo2_name,
                                                              self.yum_repo2_version,
                                                              self.yum_repo1_kind)])
        RHUIManagerSync.sync_repo(CONNECTION,
                                  [Util.format_repo(self.yum_repo1_name, self.yum_repo1_version),
                                   Util.format_repo(self.yum_repo2_name, self.yum_repo2_version)])

    def test_06_generate_ent_cert(self):
        '''
           generate an entitlement certificate
        '''
        if self.rhua_os_version < 7:
            RHUIManagerClient.generate_ent_cert(CONNECTION,
                                                ["custom-i386-x86_64", self.yum_repo1_name],
                                                "test_ent_cli",
                                                "/root/")
        else:
            RHUIManagerClient.generate_ent_cert(CONNECTION,
                                                ["custom-i386-x86_64", self.yum_repo2_name],
                                                "test_ent_cli",
                                                "/root/")
        Expect.expect_retval(CONNECTION, "test -f /root/test_ent_cli.crt")
        Expect.expect_retval(CONNECTION, "test -f /root/test_ent_cli.key")

    @staticmethod
    def test_07_create_cli_rpm():
        '''
           create a client configuration RPM from the entitlement certificate
        '''
        RHUIManagerClient.create_conf_rpm(CONNECTION,
                                          "/root",
                                          "/root/test_ent_cli.crt",
                                          "/root/test_ent_cli.key",
                                          "test_cli_rpm",
                                          "3.0")
        Expect.expect_retval(CONNECTION,
                             "test -f /root/test_cli_rpm-3.0/build/RPMS/noarch/" +
                             "test_cli_rpm-3.0-1.noarch.rpm")

    @staticmethod
    def test_08_ensure_gpgcheck_conf():
        '''
           ensure that GPG checking is enabled in the client configuration
        '''
        Expect.expect_retval(CONNECTION,
                             r"grep -q '^gpgcheck\s*=\s*1$' " +
                             "/root/test_cli_rpm-3.0/build/BUILD/test_cli_rpm-3.0/rh-cloud.repo")

    @staticmethod
    def test_09_rm_amazon_rhui_cf_rpm():
        '''
           remove Amazon RHUI configuration from the client
        '''
        Util.remove_amazon_rhui_conf_rpm(CLI)

    @staticmethod
    def test_10_install_conf_rpm():
        '''
           install the client configuration RPM
        '''
        Util.install_pkg_from_rhua(CONNECTION,
                                   CLI,
                                   "/root/test_cli_rpm-3.0/build/RPMS/noarch/" +
                                   "test_cli_rpm-3.0-1.noarch.rpm")

    @staticmethod
    def test_11_check_cli_cf_rpm_ver():
        '''
           check the client configuration RPM version
        '''
        Expect.expect_retval(CLI, "[ `rpm -q --queryformat \"%{VERSION}\" test_cli_rpm` = '3.0' ]")

    def test_12_check_repo_sync_status(self):
        '''
           check if RH repos have been synced so RPMs can be installed from them
        '''
        if self.rhua_os_version < 7:
            RHUIManagerSync.wait_till_repo_synced(CONNECTION,
                                                  [Util.format_repo(self.yum_repo1_name,
                                                                    self.yum_repo1_version)])
        else:
            RHUIManagerSync.wait_till_repo_synced(CONNECTION,
                                                  [Util.format_repo(self.yum_repo2_name,
                                                                    self.yum_repo2_version)])

    @staticmethod
    def test_13_inst_rpm_custom_repo():
        '''
           install an RPM from the custom repo
        '''
        Expect.expect_retval(CLI, "yum install -y rhui-rpm-upload-test --nogpgcheck", timeout=20)

    @staticmethod
    def test_14_inst_rpm_rh_repo():
        '''
           install an RPM from the RH repo
        '''
        Expect.expect_retval(CLI, "yum install -y " + TEST_PACKAGE, timeout=20)

    def test_15_unauthorized_access(self):
        '''
           verify that RHUI repo content cannot be fetched without an entitlement certificate
        '''
        # re-use the already added repos
        repo_paths = [self.yum_repo1_path, self.yum_repo2_path]
        # try HEADing the repodata file for each repo
        # the HTTP request must not complete (not even with HTTP 403);
        # it is supposed to raise an SSLError instead
        for repo_path in repo_paths:
            nose.tools.assert_raises(requests.exceptions.SSLError, requests.head,
                                     "https://cds.example.com/pulp/repos/" +
                                     repo_path + "/repodata/repomd.xml",
                                     verify=False)
        # also check the protected custom repo
        nose.tools.assert_raises(requests.exceptions.SSLError, requests.head,
                                 "https://cds.example.com/pulp/repos/" +
                                 "protected/custom-i386-x86_64/repodata/repomd.xml",
                                 verify=False)

    @staticmethod
    def test_16_check_cli_plugins():
        '''
           check if irrelevant Yum plug-ins are not enabled on the client with the config RPM
        '''
        # for RHBZ#1415681
        Expect.expect_retval(CLI,
                             "yum repolist enabled 2> /dev/null | " +
                             "egrep '^Loaded plugins.*(rhnplugin|subscription-manager)'", 1)

    @staticmethod
    def test_17_release_handling():
        '''
           check EUS release handling (working with /etc/yum/vars/releasever on the client)
        '''
        # for RHBZ#1504229
        Expect.expect_retval(CLI, "rhui-set-release --set 7.5")
        Expect.expect_retval(CLI, "[[ $(</etc/yum/vars/releasever) == 7.5 ]]")
        Expect.expect_retval(CLI, "[[ $(rhui-set-release) == 7.5 ]]")
        Expect.expect_retval(CLI, "rhui-set-release -s 6.5")
        Expect.expect_retval(CLI, "[[ $(</etc/yum/vars/releasever) == 6.5 ]]")
        Expect.expect_retval(CLI, "[[ $(rhui-set-release) == 6.5 ]]")
        Expect.expect_retval(CLI, "rhui-set-release -u")
        Expect.expect_retval(CLI, "test -f /etc/yum/vars/releasever", 1)
        Expect.expect_retval(CLI, "rhui-set-release -s 7.1")
        Expect.expect_retval(CLI, "[[ $(</etc/yum/vars/releasever) == 7.1 ]]")
        Expect.expect_retval(CLI, "[[ $(rhui-set-release) == 7.1 ]]")
        Expect.expect_retval(CLI, "rhui-set-release --unset")
        Expect.expect_retval(CLI, "test -f /etc/yum/vars/releasever", 1)
        Expect.expect_retval(CLI, "rhui-set-release foo", 1)
        Expect.ping_pong(CLI, "rhui-set-release --help", "Usage:")
        Expect.ping_pong(CLI, "rhui-set-release -h", "Usage:")

    @staticmethod
    def test_99_cleanup():
        '''
           remove repos, certs, cli rpms; remove rpms from cli, uninstall cds, hap
        '''
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])
        RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(CONNECTION, "cds", ["cds01.example.com"])
        Expect.expect_retval(CONNECTION, "rm -f /root/test_ent_cli*")
        Expect.expect_retval(CONNECTION, "rm -rf /root/test_cli_rpm-3.0/")
        Util.remove_rpm(CLI, [TEST_PACKAGE, "test_cli_rpm", "rhui-rpm-upload-test"])
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
