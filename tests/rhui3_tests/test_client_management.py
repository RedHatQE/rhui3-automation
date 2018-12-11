'''Client management tests'''

from os.path import basename
import re

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

CUSTOM_REPO = "custom-i386-x86_64"
CUSTOM_PATH = CUSTOM_REPO.replace("-", "/")
CUSTOM_RPMS_DIR = "/tmp/extra_rhui_files"

class TestClient(object):
    '''
       class for client tests
    '''

    def __init__(self):
        try:
            self.custom_rpm = Util.get_rpms_in_dir(CONNECTION, CUSTOM_RPMS_DIR)[0]
        except IndexError:
            raise RuntimeError("No custom RPMs to test in %s" % CUSTOM_RPMS_DIR)
        self.cli_version = Util.get_rhel_version(CLI)["major"]
        arch = Util.get_arch(CLI)
        if arch == "arm64":
            repos = "ARM_repos"
        else:
            repos = "yum_repos"
        with open("/usr/share/rhui3_tests_lib/config/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)
            try:
                self.yum_repo_name = doc[repos][self.cli_version]["name"]
                self.yum_repo_version = doc[repos][self.cli_version]["version"]
                self.yum_repo_kind = doc[repos][self.cli_version]["kind"]
                self.yum_repo_path = doc[repos][self.cli_version]["path"]
                self.test_package = doc[repos][self.cli_version]["test_package"]
            except KeyError as version:
                raise nose.SkipTest("No test repo defined for RHEL %s on %s" % (version, arch))

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
                                        CUSTOM_REPO,
                                        "",
                                        CUSTOM_PATH,
                                        "1",
                                        "y")
        RHUIManagerRepo.upload_content(CONNECTION,
                                       [CUSTOM_REPO],
                                       "%s/%s" % (CUSTOM_RPMS_DIR, self.custom_rpm))
        RHUIManagerRepo.add_rh_repo_by_repo(CONNECTION,
                                            [Util.format_repo(self.yum_repo_name,
                                                              self.yum_repo_version,
                                                              self.yum_repo_kind)])
        RHUIManagerSync.sync_repo(CONNECTION,
                                  [Util.format_repo(self.yum_repo_name, self.yum_repo_version)])

    def test_06_generate_ent_cert(self):
        '''
           generate an entitlement certificate
        '''
        RHUIManagerClient.generate_ent_cert(CONNECTION,
                                            [CUSTOM_REPO, self.yum_repo_name],
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
    def test_09_check_cli_crt_sig():
        '''check if SHA-256 is used in the client certificate signature'''
        # for RHBZ#1628957
        sigs_expected = ["sha256", "sha256"]
        _, stdout, _ = CONNECTION.exec_command("openssl x509 -noout -text -in " +
                                               "/root/test_ent_cli.crt")
        with stdout as output:
            cert_details = output.read().decode()
        sigs_actual = re.findall("sha[0-9]+", cert_details)
        nose.tools.eq_(sigs_expected, sigs_actual)

    @staticmethod
    def test_10_rm_amazon_rhui_cf_rpm():
        '''
           remove Amazon RHUI configuration from the client
        '''
        Util.remove_amazon_rhui_conf_rpm(CLI)

    @staticmethod
    def test_11_install_conf_rpm():
        '''
           install the client configuration RPM
        '''
        Util.install_pkg_from_rhua(CONNECTION,
                                   CLI,
                                   "/root/test_cli_rpm-3.0/build/RPMS/noarch/" +
                                   "test_cli_rpm-3.0-1.noarch.rpm")

        # verify the installation by checking the client configuration RPM version
        Expect.expect_retval(CLI, "[ `rpm -q --queryformat \"%{VERSION}\" test_cli_rpm` = '3.0' ]")

    def test_12_check_repo_sync_status(self):
        '''
           check if RH repos have been synced so RPMs can be installed from them
        '''
        RHUIManagerSync.wait_till_repo_synced(CONNECTION,
                                              [Util.format_repo(self.yum_repo_name,
                                                                self.yum_repo_version)])
        # also wait for the publish Pulp task to complete (takes time in the case of large repos)
        RHUIManagerSync.wait_till_pulp_tasks_finish(CONNECTION)

    def test_13_inst_rpm_custom_repo(self):
        '''
           install an RPM from the custom repo
        '''
        test_rpm_name = self.custom_rpm.rsplit('-', 2)[0]
        Expect.expect_retval(CLI, "yum install -y %s --nogpgcheck" % test_rpm_name, timeout=20)

    def test_14_inst_rpm_rh_repo(self):
        '''
           install an RPM from the RH repo
        '''
        Expect.expect_retval(CLI, "yum install -y %s" % self.test_package, timeout=20)

    def test_15_unauthorized_access(self):
        '''
           verify that RHUI repo content cannot be fetched without an entitlement certificate
        '''
        # try HEADing the repodata file for the already added repo
        # the HTTP request must not complete (not even with HTTP 403);
        # it is supposed to raise an SSLError instead
        nose.tools.assert_raises(requests.exceptions.SSLError, requests.head,
                                 "https://cds.example.com/pulp/repos/" +
                                 self.yum_repo_path + "/repodata/repomd.xml",
                                 verify=False)
        # also check the protected custom repo
        nose.tools.assert_raises(requests.exceptions.SSLError, requests.head,
                                 "https://cds.example.com/pulp/repos/" +
                                 "protected/%s/repodata/repomd.xml" % CUSTOM_PATH,
                                 verify=False)

    def test_16_check_cli_plugins(self):
        '''
           check if irrelevant Yum plug-ins are not enabled on the client with the config RPM
        '''
        # for RHBZ#1415681
        if self.cli_version <= 7:
            cmd = "yum"
        else:
            cmd = "dnf -v"
        Expect.expect_retval(CLI,
                             "%s repolist enabled 2> /dev/null | " % cmd +
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

    def test_99_cleanup(self):
        '''
           remove repos, certs, cli rpms; remove rpms from cli, uninstall cds, hap
        '''
        test_rpm_name = self.custom_rpm.rsplit('-', 2)[0]
        RHUIManagerRepo.delete_all_repos(CONNECTION)
        nose.tools.assert_equal(RHUIManagerRepo.list(CONNECTION), [])
        RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(CONNECTION, "cds", ["cds01.example.com"])
        Expect.expect_retval(CONNECTION, "rm -f /root/test_ent_cli*")
        Expect.expect_retval(CONNECTION, "rm -rf /root/test_cli_rpm-3.0/")
        Util.remove_rpm(CLI, [self.test_package, "test_cli_rpm", test_rpm_name])
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
