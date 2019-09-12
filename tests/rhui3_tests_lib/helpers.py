"""Helper Functions for RHUI Test Cases"""

from os.path import basename, join

from stitches.expect import Expect

class Helpers(object):
    """actions that may be repeated in specific test cases and do not belong in general utils"""
    @staticmethod
    def break_hostname(connection, hostname):
        """override DNS by setting a fake IP address in /etc/hosts and stopping bind"""
        tweak_hosts_cmd = r"sed -i.bak 's/^[^ ]*\(.*%s\)$/256.0.0.0\1/' /etc/hosts" % hostname
        Expect.expect_retval(connection, tweak_hosts_cmd)
        Expect.expect_retval(connection, "service named stop")

    @staticmethod
    def unbreak_hostname(connection):
        """undo the changes made by break_hostname"""
        Expect.expect_retval(connection, "mv -f /etc/hosts.bak /etc/hosts")
        Expect.expect_retval(connection, "service named start")

    @staticmethod
    def cds_in_haproxy_cfg(connection, cds):
        """check if the CDS is present in the HAProxy configuration"""
        _, stdout, _ = connection.exec_command("cat /etc/haproxy/haproxy.cfg")
        with stdout as output:
            cfg = output.read().decode()
            return "server %s %s:5000 check" % (cds, cds) in cfg and \
                   "server %s %s:443 check" % (cds, cds) in cfg

    @staticmethod
    def check_service(connection, service):
        """check if the given service is running"""
        return connection.recv_exit_status("systemctl is-active %s" % service) == 0

    @staticmethod
    def check_mountpoint(connection, mountpoint):
        """check if something is mounted in the given directory"""
        return connection.recv_exit_status("mountpoint %s" % mountpoint) == 0

    @staticmethod
    def encode_sos_command(command):
        """replace special characters with safe ones as per rhui-debug, prepend /commands/"""
        # spaces become underscores
        # slashes become dots
        # special case: " /" becomes just "_", not "_.", so let's get rid of the slash first
        command = command.replace(" /", " ")
        command = command.replace(" ", "_")
        command = command.replace("/", ".")
        # the actual file is in the /commands directory in the archive
        return "/commands/%s" % command

    @staticmethod
    def add_legacy_ca(connection, local_ca_file):
        """configure a CDS to accept a legacy CA"""
        # this method takes the path to the local CA file and configures that CA on a CDS
        ca_dir = "/etc/pki/rhui/legacy-ca"
        ca_file = join(ca_dir, basename(local_ca_file))
        connection.sftp.put(local_ca_file, ca_file)
        Expect.expect_retval(connection,
                             "hash=`openssl x509 -hash -noout -in %s` && " % ca_file +
                             "ln -sf %s /etc/pki/tls/certs/$hash.0" % ca_file)

    @staticmethod
    def del_legacy_ca(connection, ca_file_name):
        """unconfigure a legacy CA"""
        # this method takes just the base file name (something.crt) in the legacy CA dir on a CDS
        # and unconfigures that CA
        ca_dir = "/etc/pki/rhui/legacy-ca"
        ca_file = join(ca_dir, ca_file_name)
        Expect.expect_retval(connection,
                             "hash=`openssl x509 -hash -noout -in %s` && " % ca_file +
                             "rm -f %s /etc/pki/tls/certs/$hash.0" % ca_file)
        Expect.expect_retval(connection, "systemctl restart httpd")
