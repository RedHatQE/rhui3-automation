'''Miscellaneous Tests That Do Not Fit Elsewhere'''

import json
from os.path import basename

import nose
import stitches
from stitches.expect import Expect

RHUA = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

RHUI_SERVICE_PIDFILES = ["/var/run/httpd/httpd.pid",
                         "/var/run/pulp/celerybeat.pid",
                         "/var/run/pulp/reserved_resource_worker-0.pid",
                         "/var/run/pulp/reserved_resource_worker-1.pid",
                         "/var/run/pulp/reserved_resource_worker-2.pid",
                         "/var/run/pulp/resource_manager.pid"]

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_sha1():
    '''
        check if SHA-1 is not used in internal certificates, and if SHA-256 is used instead
    '''
    # for RHBZ#1411451
    Expect.expect_retval(RHUA,
                         "grep 'Signature Algorithm: sha1' " +
                         "/etc/pki/katello-certs-tools/certs/*.crt " +
                         "/etc/puppet/rhui-secrets/cds-cert.crt",
                         1)
    Expect.expect_retval(RHUA,
                         "grep 'Signature Algorithm: sha256' " +
                         "/etc/pki/katello-certs-tools/certs/*.crt " +
                         "/etc/puppet/rhui-secrets/cds-cert.crt")

def test_02_repo_remove_missing():
    '''
        check if Pulp repos are globally configured to remove packages missing upstream
    '''
    # for RHBZ#1489113
    _, stdout, _ = RHUA.exec_command("cat /etc/pulp/server/plugins.conf.d/yum_importer.json")
    with stdout as cfgfile:
        cfg = json.load(cfgfile)
    nose.tools.ok_("remove_missing" in cfg, msg="'remove_missing' is not in the configuration")
    nose.tools.ok_(cfg["remove_missing"], msg="'remove_missing' is not enabled")

def test_03_restart_services_script():
    '''
        try the rhui-services-restart script
    '''
    # for RHBZ#1539105
    Expect.ping_pong(RHUA, "rhui-services-restart --help", "Usage:")
    # fetch current service PIDs
    # use 0 if a PID file doesn't exist (the service isn't running)
    _, stdout, _ = RHUA.exec_command("for pidfile in %s; do cat $pidfile || echo 0; done" % \
                                     " ".join(RHUI_SERVICE_PIDFILES))
    with stdout as output:
        old_pids = list(map(int, output.read().decode().splitlines()))
    # restart
    Expect.expect_retval(RHUA, "rhui-services-restart", timeout=30)
    # fetch new service PIDs
    _, stdout, _ = RHUA.exec_command("for pidfile in %s; do cat $pidfile || echo 0; done" % \
                                     " ".join(RHUI_SERVICE_PIDFILES))
    with stdout as output:
        new_pids = list(map(int, output.read().decode().splitlines()))
    # the new PIDs must differ and mustn't be 0, which would mean the pidfile couldn't be read
    # (which would mean the service didn't (re)start)
    for i in range(len(RHUI_SERVICE_PIDFILES)):
        nose.tools.ok_(new_pids[i] != old_pids[i], msg="not all the RHUI services restarted")
        nose.tools.ok_(new_pids[i] > 0, msg="not all the RHUI services started")

def test_04_fabric_crypto_req():
    '''
        check if the fabric package requires python-crypto
    '''
    # for RHBZ#1615907
    Expect.expect_retval(RHUA, "rpm -qR fabric | grep python-crypto")

def test_05_celery_selinux():
    '''
        verify that no SELinux denial related to celery was logged
    '''
    # for RHBZ#1608166 - anyway, only non-fatal denials are expected if everything else works
    Expect.ping_pong(RHUA, "grep celery /var/log/audit/audit.log | audit2allow", "Nothing to do")

def test_06_pulp_server_rpm_v():
    '''
        verify that /etc/pki/pulp/rsa_pub.key is installed correctly
    '''
    # for RHBZ#1578266
    Expect.expect_retval(RHUA, "rpm -V pulp-server | grep /etc/pki/pulp/rsa_pub.key", 1)

def test_07_check_migrate_py():
    '''
        check if the migration script in the RHUI ISO is up to date
    '''
    # for RHBZ#1278954
    Expect.expect_retval(RHUA,
                         "mount /tmp/iso && " +
                         "grep DEFAULT_ENTITLEMENT /tmp/iso/migrate/migrate.py")
    Expect.expect_retval(RHUA, "umount /tmp/iso")

def test_08_qpid_linearstore():
    '''
        check if the qpid-cpp-server-linearstore package is available
    '''
    # for RHBZ#1702254
    Expect.expect_retval(RHUA, "yum list qpid-cpp-server-linearstore", timeout=30)

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
