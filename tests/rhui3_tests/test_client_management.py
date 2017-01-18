import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager_cli import *
from rhui3_tests_lib.rhuimanager_repo import *

from os.path import basename

# The parts related to Atomic are applicable to RHEL 7+ only.
import platform
atomic_unsupported = float(platform.linux_distribution()[1]) < 7

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_repo_setup():
    '''do initial rhui-manager run'''
    RHUIManager.initial_run(connection)

def test_02_add_repos():
    '''
       add a custom and RH content repos to protect by a client entitlement certificate
    '''
    RHUIManagerRepo.add_custom_repo(connection, "custom-i386-x86_64", "", "custom/i386/x86_64", "1", "y")
    RHUIManagerRepo.add_rh_repo_by_repo(connection, ["Red Hat Update Infrastructure 2.0 \(RPMs\) \(6Server-x86_64\) \(Yum\)"])

def test_02_generate_ent_cert():
    '''
       generate an entitlement certificate
    '''
    Expect.enter(connection, "home")
    Expect.expect(connection, ".*rhui \(" + "home" + "\) =>")
    RHUIManagerClient.generate_ent_cert(connection, ["custom-i386-x86_64", "Red Hat Update Infrastructure 2.0 \(RPMs\)"], "test_ent_cli", "/root/")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_ent_cli.crt && echo SUCCESS", "[^ ]SUCCESS")
    Expect.ping_pong(connection, "test -f /root/test_ent_cli.key && echo SUCCESS", "[^ ]SUCCESS")

def test_02_create_cli_rpm():
    '''
       create a client configuration RPM from an entitlement certificate
    '''
    RHUIManager.initial_run(connection)
    RHUIManagerClient.create_conf_rpm(connection, "/root", "/root/test_ent_cli.crt", "/root/test_ent_cli.key", "test_cli_rpm", "3.0")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_cli_rpm-3.0/build/RPMS/noarch/test_cli_rpm-3.0-1.noarch.rpm && echo SUCCESS", "[^ ]SUCCESS")

def test_03_create_docker_cli_rpm():
    '''
       create a docker client configuration RPM
    '''
    RHUIManager.initial_run(connection)
    RHUIManagerClient.create_docker_conf_rpm(connection, "/root", "test_docker_cli_rpm", "4.0")
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "test -f /root/test_docker_cli_rpm-4.0/build/RPMS/noarch/test_docker_cli_rpm-4.0-1.noarch.rpm && echo SUCCESS", "[^ ]SUCCESS")

def test_04_add_atomic_repo():
    '''
       add the RHEL RHUI Atomic 7 Ostree Repo (RHEL 7+ only)
    '''
    if atomic_unsupported:
        return
    RHUIManager.initial_run(connection)
    RHUIManagerRepo.add_rh_repo_by_product(connection, ["RHEL RHUI Atomic 7 Ostree Repo"])

def test_05_generate_atomic_ent_cert():
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

def test_06_create_atomic_pkg():
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
       remove created repos, entitlements and custom cli rpms (and tar on RHEL 7+)
    '''
    RHUIManager.initial_run(connection)
    RHUIManagerRepo.delete_all_repos(connection)
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])
    Expect.enter(connection, 'q')
    Expect.ping_pong(connection, "rm -f /root/test_ent_cli* && echo SUCCESS", "[^ ]SUCCESS")
    Expect.ping_pong(connection, "rm -rf /root/test_cli_rpm-3.0/ && echo SUCCESS", "[^ ]SUCCESS")
    Expect.ping_pong(connection, "rm -rf /root/test_docker_cli_rpm-4.0/ && echo SUCCESS", "[^ ]SUCCESS")
    if not atomic_unsupported:
        Expect.ping_pong(connection, "rm -f /root/test_atomic_ent_cli* && echo SUCCESS", "[^ ]SUCCESS")
        Expect.ping_pong(connection, "rm -f /root/test_atomic_pkg.tar.gz && echo SUCCESS", "[^ ]SUCCESS")
    RHUIManager.initial_run(connection)

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)

