'''Client management tests'''

import nose, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager_client import *
from rhui3_tests_lib.rhuimanager_entitlement import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanager_sync import *
from rhui3_tests_lib.rhuimanager_instance import *
from rhui3_tests_lib.instance import *
from rhui3_tests_lib.util import Util

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
cli=stitches.connection.Connection("cli01.example.com", "root", "/root/.ssh/id_rsa_test")
atomic_cli=stitches.connection.Connection("atomiccli.example.com", "root", "/root/.ssh/id_rsa_test")

with open('/tmp/rhui3-tests/tests/rhui3_tests/tested_repos.yaml', 'r') as file:
    doc = yaml.load(file)

yum_repo1_name = doc['yum_repo1']['name']
yum_repo1_version = doc['yum_repo1']['version']
yum_repo2_name = doc['yum_repo2']['name']
yum_repo2_version = doc['yum_repo2']['version']
atomic_repo_name = doc['atomic_repo']['name']

def setUp():
    print "*** Running %s: *** " % basename(__file__)

class TestClient:

    @classmethod
    def setUpClass(cls):
        cls.rhua_os_version = Util.get_rhua_version(connection)

    def test_01_repo_setup(self):
        '''do initial rhui-manager run'''
        RHUIManager.initial_run(connection)

    def test_02_upload_rh_certificate(self):
        '''
           upload a new or updated Red Hat content certificate
        '''
        list = RHUIManagerEntitlements.upload_rh_certificate(connection)
        nose.tools.assert_not_equal(len(list), 0)

    def test_03_add_cds(self):
        '''
            add a CDS
        '''
        cds_list = RHUIManagerInstance.list(connection, "cds")
        nose.tools.assert_equal(cds_list, [])
        RHUIManagerInstance.add_instance(connection, "cds", "cds01.example.com")

    def test_04_add_hap(self):
        '''
            add an HAProxy Load-balancer
        '''
        hap_list = RHUIManagerInstance.list(connection, "loadbalancers")
        nose.tools.assert_equal(hap_list, [])
        RHUIManagerInstance.add_instance(connection, "loadbalancers", "hap01.example.com")

    def test_05_add_repos_upload_rpm_sync(self):
        '''
           add a custom and RH content repos to protect by a cli entitlement cert, upload rpm, sync
        '''
        RHUIManagerRepo.add_custom_repo(connection, "custom-i386-x86_64", "", "custom/i386/x86_64", "1", "y")
        RHUIManagerRepo.upload_content(connection, ["custom-i386-x86_64"], "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")
        RHUIManagerRepo.add_rh_repo_by_repo(connection, [yum_repo1_name + yum_repo1_version + " \(Yum\)", yum_repo2_name + yum_repo2_version + " \(Yum\)"])
        RHUIManagerSync.sync_repo(connection, [yum_repo1_name + yum_repo1_version, yum_repo2_name + yum_repo2_version])

    def test_06_generate_ent_cert(self):
        '''
           generate an entitlement certificate
        '''
        if self.rhua_os_version < 7:
           RHUIManagerClient.generate_ent_cert(connection, ["custom-i386-x86_64", yum_repo1_name], "test_ent_cli", "/root/")
        else:
           RHUIManagerClient.generate_ent_cert(connection, ["custom-i386-x86_64", yum_repo2_name], "test_ent_cli", "/root/")
        Expect.ping_pong(connection, "test -f /root/test_ent_cli.crt && echo SUCCESS", "[^ ]SUCCESS")
        Expect.ping_pong(connection, "test -f /root/test_ent_cli.key && echo SUCCESS", "[^ ]SUCCESS")

    def test_07_create_cli_rpm(self):
        '''
           create a client configuration RPM from an entitlement certificate
        '''
        RHUIManager.initial_run(connection)
        RHUIManagerClient.create_conf_rpm(connection, "/root", "/root/test_ent_cli.crt", "/root/test_ent_cli.key", "test_cli_rpm", "3.0")
        Expect.ping_pong(connection, "test -f /root/test_cli_rpm-3.0/build/RPMS/noarch/test_cli_rpm-3.0-1.noarch.rpm && echo SUCCESS", "[^ ]SUCCESS")

    def test_08_ensure_gpgcheck_in_cli_conf_(self):
        '''
           ensure that GPG checking is enabled in the client configuration
        '''
        Expect.expect_retval(connection, "grep -q '^gpgcheck\s*=\s*1$' /root/test_cli_rpm-3.0/build/BUILD/test_cli_rpm-3.0/rh-cloud.repo")

    def test_09_remove_amazon_rhui_conf_rpm(self):
        '''
           remove amazon rhui configuration rpm from client
        '''
        Util.remove_amazon_rhui_conf_rpm(cli)

    def test_10_install_conf_rpm(self):
        '''
           install configuration rpm to client
        '''
        Util.install_pkg_from_rhua(connection, cli, "/root/test_cli_rpm-3.0/build/RPMS/noarch/test_cli_rpm-3.0-1.noarch.rpm")

    def test_11_check_cli_conf_rpm_version(self):
        '''
           check client configuration rpm version
        '''
        Expect.ping_pong(cli, "[ `rpm -q --queryformat \"%{VERSION}\" test_cli_rpm` = '3.0' ] && echo SUCCESS", "[^ ]SUCCESS")

    def test_12_check_repo_sync_status(self):
        '''
           check if RH repos were synced to install rpm
        '''
        RHUIManager.initial_run(connection)
        if self.rhua_os_version < 7:
            RHUIManagerSync.wait_till_repo_synced(connection, [yum_repo1_name + yum_repo1_version])
        else:
            RHUIManagerSync.wait_till_repo_synced(connection, [yum_repo2_name + yum_repo2_version])

    def test_13_install_rpm_from_custom_repo(self):
        '''
           install rpm from a custom repo
        '''
        Expect.ping_pong(cli, "yum install -y rhui-rpm-upload-test --nogpgcheck && echo SUCCESS", "[^ ]SUCCESS", 60)

    def test_14_install_rpm_from_rh_repo(self):
        '''
           install rpm from a RH repo
        '''
        if self.rhua_os_version < 7:
           Expect.ping_pong(cli, "yum install -y js && echo SUCCESS", "[^ ]SUCCESS", 60)
        else:
           Expect.ping_pong(cli, "yum install -y vm-dump-metrics && echo SUCCESS", "[^ ]SUCCESS", 60)

    def test_15_create_docker_cli_rpm(self):
        '''
           create a docker client configuration RPM
        '''
        RHUIManager.initial_run(connection)
        RHUIManagerClient.create_docker_conf_rpm(connection, "/root", "test_docker_cli_rpm", "4.0")
        Expect.ping_pong(connection, "test -f /root/test_docker_cli_rpm-4.0/build/RPMS/noarch/test_docker_cli_rpm-4.0-1.noarch.rpm && echo SUCCESS", "[^ ]SUCCESS")

    def test_16_install_docker_rpm(self):
        '''
           install a docker client configuration RPM to client
        '''
        if self.rhua_os_version < 7:
            raise nose.exc.SkipTest('Not supported on RHEL6')
        Util.install_pkg_from_rhua(connection, cli, "/root/test_docker_cli_rpm-4.0/build/RPMS/noarch/test_docker_cli_rpm-4.0-1.noarch.rpm")

    def test_17_check_docker_rpm_version(self):
        '''
           check docker rpm version
        '''
        if self.rhua_os_version < 7:
            raise nose.exc.SkipTest('Not supported on RHEL6')
        Expect.ping_pong(cli, "[ `rpm -q --queryformat \"%{VERSION}\" test_docker_cli_rpm` = '4.0' ] && echo SUCCESS", "[^ ]SUCCESS")

    def test_99_cleanup(self):
        '''
           remove created repos, entitlements and custom cli rpms (and tar on RHEL 7+), remove rpms from cli, uninstall cds, hap, delete the RH cert
        '''
        RHUIManager.initial_run(connection)
        RHUIManagerRepo.delete_all_repos(connection)
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])
        RHUIManagerInstance.delete(connection, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(connection, "cds", ["cds01.example.com"])
        Expect.ping_pong(connection, "rm -f /root/test_ent_cli* && echo SUCCESS", "[^ ]SUCCESS")
        Expect.ping_pong(connection, "rm -rf /root/test_cli_rpm-3.0/ && echo SUCCESS", "[^ ]SUCCESS")
        Expect.ping_pong(connection, "rm -rf /root/test_docker_cli_rpm-4.0/ && echo SUCCESS", "[^ ]SUCCESS")
        if self.rhua_os_version >=7:
            Util.remove_rpm(cli, ["vm-dump-metrics", "test_docker_cli_rpm"])
        else:
            Util.remove_rpm(cli, ["js"])
        Util.remove_rpm(cli, ["test_cli_rpm", "rhui-rpm-upload-test"])
        RHUIManager.remove_rh_certs(connection)

    @classmethod
    def tearDownClass(cls):
        print "*** Finished running %s. *** " % basename(__file__)
