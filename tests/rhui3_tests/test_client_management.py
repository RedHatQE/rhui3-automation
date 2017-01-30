import nose, unittest, stitches, logging, yaml, time

from rhui3_tests_lib.rhuimanager_cli import *
from rhui3_tests_lib.rhuimanager_entitlement import *
from rhui3_tests_lib.rhuimanager_repo import *
from rhui3_tests_lib.rhuimanager_sync import *
from rhui3_tests_lib.rhuimanager_cds import *
from rhui3_tests_lib.cds import *
from rhui3_tests_lib.rhuimanager_hap import *
from rhui3_tests_lib.hap import *
from rhui3_tests_lib.util import Util

from os.path import basename

# The parts related to Atomic are applicable to RHEL 7+ only.
import platform
atomic_unsupported = float(platform.linux_distribution()[1]) < 7

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
cli=stitches.connection.Connection("cli01.example.com", "root", "/root/.ssh/id_rsa_test")

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_repo_setup():
    '''do initial rhui-manager run'''
    RHUIManager.initial_run(connection)

def test_02_upload_rh_certificate():
    '''
       upload a new or updated Red Hat content certificate
    '''
    list = RHUIManagerEntitlements.upload_rh_certificate(connection)
    nose.tools.assert_not_equal(len(list), 0)

def test_03_add_cds():
    '''
        add a CDS
    '''
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    cds_list = RHUIManagerCds.list(connection)
    nose.tools.assert_equal(cds_list, [])
    cds = Cds()
    RHUIManagerCds.add_cds(connection, cds)

def test_04_add_hap():
    '''
        add an HAProxy Load-balancer
    '''
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    hap_list = RHUIManagerHap.list(connection)
    nose.tools.assert_equal(hap_list, [])
    hap = Hap()
    RHUIManagerHap.add_hap(connection, hap)

def test_05_add_repos_upload_rpm_sync():
    '''
       add a custom and RH content repos to protect by a cli entitlement cert, upload rpm, sync
    '''
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    RHUIManagerRepo.add_custom_repo(connection, "custom-i386-x86_64", "", "custom/i386/x86_64", "1", "y")
    RHUIManagerRepo.upload_content(connection, ["custom-i386-x86_64"], "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")
    RHUIManagerRepo.add_rh_repo_by_repo(connection, ["Red Hat Update Infrastructure 2.0 \(RPMs\) \(6Server-x86_64\) \(Yum\)", "RHEL RHUI Server 7 Rhgs-server-nfs 3.1 OS \(7Server-x86_64\) \(Yum\)"])
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    RHUIManagerSync.sync_repo(connection, ["Red Hat Update Infrastructure 2.0 \(RPMs\) \(6Server-x86_64\)", "RHEL RHUI Server 7 Rhgs-server-nfs 3.1 OS \(7Server-x86_64\)"])

def test_06_generate_ent_cert():
    '''
       generate an entitlement certificate
    '''
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    if atomic_unsupported:
       RHUIManagerClient.generate_ent_cert(connection, ["custom-i386-x86_64", "Red Hat Update Infrastructure 2.0 \(RPMs\)"], "test_ent_cli", "/root/")
    else:
       RHUIManagerClient.generate_ent_cert(connection, ["custom-i386-x86_64", "RHEL RHUI Server 7 Rhgs-server-nfs 3.1 OS"], "test_ent_cli", "/root/")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_ent_cli.crt && echo SUCCESS", "[^ ]SUCCESS")
    Expect.ping_pong(connection, "test -f /root/test_ent_cli.key && echo SUCCESS", "[^ ]SUCCESS")

def test_07_create_cli_rpm():
    '''
       create a client configuration RPM from an entitlement certificate
    '''
    RHUIManager.initial_run(connection)
    RHUIManagerClient.create_conf_rpm(connection, "/root", "/root/test_ent_cli.crt", "/root/test_ent_cli.key", "test_cli_rpm", "3.0")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_cli_rpm-3.0/build/RPMS/noarch/test_cli_rpm-3.0-1.noarch.rpm && echo SUCCESS", "[^ ]SUCCESS")

def test_08_remove_amazon_rhui_conf_rpm():
    '''
       remove amazon rhui configuration rpm from client
    '''
    Util.remove_amazon_rhui_conf_rpm(cli)

def test_09_install_conf_rpm():
    '''
       install configuration rpm to client
    '''
    Util.install_rpm_from_rhua(connection, cli, "/root/test_cli_rpm-3.0/build/RPMS/noarch/test_cli_rpm-3.0-1.noarch.rpm")

def test_10_check_cli_conf_rpm_version():
    '''
       check client configuration rpm version
    '''
    Expect.ping_pong(cli, "[ `rpm -q --queryformat \"%{VERSION}\" test_cli_rpm` = '3.0' ] && echo SUCCESS", "[^ ]SUCCESS")

def test_11_check_repo_sync_status():
    '''
       check if RH repos were synced to install rpm
    '''
    RHUIManager.initial_run(connection)
    reposync = ["", "", "Running"]
    while reposync[2] == "Running" or reposync[2] == "Never":
        time.sleep(10)
        if atomic_unsupported:
            reposync = RHUIManagerSync.get_repo_status(connection, "Red Hat Update Infrastructure 2.0 \(RPMs\) \(6Server-x86_64\)")
        else:
            reposync = RHUIManagerSync.get_repo_status(connection, "RHEL RHUI Server 7 Rhgs-server-nfs 3.1 OS \(7Server-x86_64\)")

    nose.tools.assert_equal(reposync[2], "Success")
    Expect.enter(connection, 'q')

def test_12_install_rpm_from_custom_repo():
    '''
       install rpm from a custom repo
    '''
    Expect.ping_pong(cli, "yum install -y rhui-rpm-upload-test --nogpgcheck && echo SUCCESS", "[^ ]SUCCESS", 60)

def test_13_install_rpm_from_rh_repo():
    '''
       install rpm from a RH repo
    '''
    if atomic_unsupported:
       Expect.ping_pong(cli, "yum install -y js && echo SUCCESS", "[^ ]SUCCESS", 60)
    else:
       Expect.ping_pong(cli, "yum install -y libntirpc && echo SUCCESS", "[^ ]SUCCESS", 60)

def test_14_create_docker_cli_rpm():
    '''
       create a docker client configuration RPM
    '''
    RHUIManager.initial_run(connection)
    RHUIManagerClient.create_docker_conf_rpm(connection, "/root", "test_docker_cli_rpm", "4.0")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_docker_cli_rpm-4.0/build/RPMS/noarch/test_docker_cli_rpm-4.0-1.noarch.rpm && echo SUCCESS", "[^ ]SUCCESS")

def test_15_install_docker_rpm():
    '''
       install a docker client configuration RPM to client (RHEL 7+ CLI only)
    '''
    if atomic_unsupported:
        return    
    Util.install_rpm_from_rhua(connection, cli, "/root/test_docker_cli_rpm-4.0/build/RPMS/noarch/test_docker_cli_rpm-4.0-1.noarch.rpm")

def test_16_check_docker_rpm_version():
    '''
       check docker rpm version (RHEL 7+ CLI only)
    '''
    if atomic_unsupported:
        return  
    Expect.ping_pong(cli, "[ `rpm -q --queryformat \"%{VERSION}\" test_docker_cli_rpm` = '4.0' ] && echo SUCCESS", "[^ ]SUCCESS")

def test_17_add_atomic_repo():
    '''
       add the RHEL RHUI Atomic 7 Ostree Repo (RHEL 7+ only)
    '''
    if atomic_unsupported:
        return
    RHUIManager.initial_run(connection)
    RHUIManagerRepo.add_rh_repo_by_product(connection, ["RHEL RHUI Atomic 7 Ostree Repo"])

def test_18_generate_atomic_ent_cert():
    '''
       generate an entitlement certificate for the Atomic repo (RHEL 7+ only)
    '''
    if atomic_unsupported:
        return
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    RHUIManagerClient.generate_ent_cert(connection, ["RHEL RHUI Atomic 7 Ostree Repo"], "test_atomic_ent_cli", "/root/")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_atomic_ent_cli.crt && echo SUCCESS", "[^ ]SUCCESS")
    Expect.ping_pong(connection, "test -f /root/test_atomic_ent_cli.key && echo SUCCESS", "[^ ]SUCCESS")

def test_19_create_atomic_pkg():
    '''
       create an Atomic client configuration package (RHEL 7+ only)
    '''
    if atomic_unsupported:
        return
    RHUIManager.initial_run(connection)
    RHUIManagerClient.create_atomic_conf_pkg(connection, "/root", "test_atomic_pkg", "/root/test_atomic_ent_cli.crt", "/root/test_atomic_ent_cli.key")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_atomic_pkg.tar.gz && echo SUCCESS", "[^ ]SUCCESS")

def test_99_cleanup():
    '''
       remove created repos, entitlements and custom cli rpms (and tar on RHEL 7+), remove rpms from cli, uninstall cds, hap
    '''
    RHUIManager.initial_run(connection)
    RHUIManagerRepo.delete_all_repos(connection)
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    hap = Hap()
    RHUIManagerHap.delete_haps(connection, hap)
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    cds = Cds()
    RHUIManagerCds.delete_cdses(connection, cds)
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "rm -f /root/test_ent_cli* && echo SUCCESS", "[^ ]SUCCESS")
    Expect.ping_pong(connection, "rm -rf /root/test_cli_rpm-3.0/ && echo SUCCESS", "[^ ]SUCCESS")
    Expect.ping_pong(connection, "rm -rf /root/test_docker_cli_rpm-4.0/ && echo SUCCESS", "[^ ]SUCCESS")
    if not atomic_unsupported:
        Expect.ping_pong(connection, "rm -f /root/test_atomic_ent_cli* && echo SUCCESS", "[^ ]SUCCESS")
        Expect.ping_pong(connection, "rm -f /root/test_atomic_pkg.tar.gz && echo SUCCESS", "[^ ]SUCCESS")
        Util.remove_rpm(cli, ["libntirpc", "test_docker_cli_rpm"])
    else:
        Util.remove_rpm(cli, ["js"])
    Util.remove_rpm(cli, ["test_cli_rpm", "rhui-rpm-upload-test"])

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)

