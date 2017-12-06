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
atomic_cli=stitches.connection.Connection("atomiccli.example.com", "root", "/root/.ssh/id_rsa_test")

with open('/tmp/rhui3-tests/tests/rhui3_tests/tested_repos.yaml', 'r') as file:
    doc = yaml.load(file)

atomic_repo_name = doc['atomic_repo']['name']

class TestClient:

    @classmethod
    def setUpClass(cls):
        cls.rhua_os_version = Util.get_rhua_version(connection)
        print "*** Running %s: *** " % basename(__file__)
        if cls.rhua_os_version < 7:
            raise nose.exc.SkipTest('Not supported on RHEL6\n*** Finished running %s. *** ' % basename(__file__))

    def test_01_repo_setup(self):
        '''do initial rhui-manager run'''
        RHUIManager.initial_run(connection)

    def test_02_add_cds(self):
        '''
            add a CDS
        '''
        cds_list = RHUIManagerInstance.list(connection, "cds")
        nose.tools.assert_equal(cds_list, [])
        RHUIManagerInstance.add_instance(connection, "cds", "cds01.example.com")

    def test_03_add_hap(self):
        '''
            add an HAProxy Load-balancer
        '''
        hap_list = RHUIManagerInstance.list(connection, "loadbalancers")
        nose.tools.assert_equal(hap_list, [])
        RHUIManagerInstance.add_instance(connection, "loadbalancers", "hap01.example.com")

    def test_04_upload_atomic_cert(self):
        '''
            upload atomic cert
        '''
        list = RHUIManagerEntitlements.upload_rh_certificate(connection, "/tmp/extra_rhui_files/rhcert_atomic.pem")
        nose.tools.assert_not_equal(len(list), 0)

    def test_05_add_atomic_repo(self):
        '''
           add the RHEL RHUI Atomic 7 Ostree Repo
        '''
        RHUIManagerRepo.add_rh_repo_by_product(connection, [atomic_repo_name])

    #def test_06_sync_atomic_repo(self):
    #    '''
    #       sync the RHEL RHUI Atomic 7 Ostree Repo (RHEL 7+ only)
    #    '''
    #    atomic_repo_version = RHUIManagerRepo.get_repo_version(connection, atomic_repo_name)
    #    RHUIManagerSync.sync_repo(connection, [atomic_repo_name + atomic_repo_version])

    def test_07_generate_atomic_ent_cert(self):
        '''
           generate an entitlement certificate for the Atomic repo (RHEL 7+ only)
        '''
        RHUIManagerClient.generate_ent_cert(connection, [atomic_repo_name], "test_atomic_ent_cli", "/root/")
        Expect.ping_pong(connection, "test -f /root/test_atomic_ent_cli.crt && echo SUCCESS", "[^ ]SUCCESS")
        Expect.ping_pong(connection, "test -f /root/test_atomic_ent_cli.key && echo SUCCESS", "[^ ]SUCCESS")

    def test_08_create_atomic_pkg(self):
        '''
           create an Atomic client configuration package (RHEL 7+ only)
        '''
        RHUIManager.initial_run(connection)
        RHUIManagerClient.create_atomic_conf_pkg(connection, "/root", "test_atomic_pkg", "/root/test_atomic_ent_cli.crt", "/root/test_atomic_ent_cli.key")
        Expect.ping_pong(connection, "test -f /root/test_atomic_pkg.tar.gz && echo SUCCESS", "[^ ]SUCCESS")

    #def test_09_check_sync_status_of_atomic_repo(self):
    #    '''
    #       check if Atomic repo was synced to pull the content (RHEL 7+ only)
    #    '''
    #    RHUIManager.initial_run(connection)
    #    atomic_repo_version = RHUIManagerRepo.get_repo_version(connection, atomic_repo_name)
    #    RHUIManagerSync.wait_till_repo_synced(connection, atomic_repo_name + atomic_repo_version)

    def test_10_install_atomic_pkg(self):
        '''
           install atomic pkg on atomic host
        '''
        Util.install_pkg_from_rhua(connection, atomic_cli, "/root/test_atomic_pkg.tar.gz")

    #def test_11_pull_atomic_content(self):
    #    '''
    #       pull atomic content
    #    '''
    #    Expect.ping_pong(atomic_cli, "sudo ostree pull rhui-rhel-rhui-atomic-7-ostree-repo:rhel-atomic-host/7/x86_64/standard && echo SUCCESS", "[^ ]SUCCESS")

    def test_99_cleanup(self):
        '''
           remove created repos, entitlements and custom cli rpms (and tar on RHEL 7+), remove rpms from cli, uninstall cds, hap, delete the RH cert
        '''
        RHUIManager.initial_run(connection)
        RHUIManagerRepo.delete_all_repos(connection)
        nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])
        RHUIManagerInstance.delete(connection, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(connection, "cds", ["cds01.example.com"])
        Expect.ping_pong(connection, "rm -f /root/test_atomic_ent_cli* && echo SUCCESS", "[^ ]SUCCESS")
        Expect.ping_pong(connection, "rm -f /root/test_atomic_pkg.tar.gz && echo SUCCESS", "[^ ]SUCCESS")
     #   Expect.ping_pong(atomic_cli, "sudo ostree remote delete rhui-rhel-rhui-atomic-7-ostree-repo \
     #                                    && echo SUCCESS", "[^ ]SUCCESS")
        RHUIManager.remove_rh_certs(connection)

    @classmethod
    def tearDownClass(cls):
        print "*** Finished running %s. *** " % basename(__file__)
