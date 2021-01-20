"""Helper Functions for RHUI Test Cases"""

from os.path import basename, join

try:
    from configparser import ConfigParser # Python 3+
except ImportError:
    from ConfigParser import ConfigParser # Python 2

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
        cfg = stdout.read().decode()
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

    @staticmethod
    def get_credentials(connection, site="rh"):
        '''
        get the user name and password for the given site from the RHUA
        '''
        path = "/tmp/extra_rhui_files/credentials.conf"
        creds_cfg = ConfigParser()
        _, stdout, _ = connection.exec_command("cat %s" % path)
        creds_cfg.readfp(stdout)
        if not creds_cfg.has_section(site):
            raise RuntimeError("section %s does not exist in %s" % (site, path))
        if not creds_cfg.has_option(site, "username"):
            raise RuntimeError("username does not exist inside %s in %s" % (site, path))
        if not creds_cfg.has_option(site, "password"):
            raise RuntimeError("password does not exist inside %s in %s" % (site, path))
        credentials = [creds_cfg.get(site, "username"), creds_cfg.get(site, "password")]
        return credentials

    @staticmethod
    def get_registry_url(site, connection=""):
        """get the URL for the given container registry or for the saved one (use "default" then)"""
        if site == "default":
            cfg_file = "/etc/rhui/rhui-tools.conf"
            rhuicfg = ConfigParser()
            _, stdout, _ = connection.exec_command("cat %s" % cfg_file)
            rhuicfg.readfp(stdout)
            if not rhuicfg.has_option("docker", "docker_url"):
                return None
            return rhuicfg.get("docker", "docker_url")
        urls = {"rh": "https://registry.redhat.io",
                "quay": "https://quay.io",
                "gitlab": "https://registry.gitlab.com",
                "docker": "https://registry-1.docker.io"}
        if site in urls:
            return urls[site]
        return None

    @staticmethod
    def set_registry_credentials(connection, site="rh", data="", backup=True):
        """put container registry credentials into the RHUI configuration file"""
        # if "site" isn't in credentials.conf, then "data" is supposed to be:
        # [username, password, url], or just [url] if no authentication is to be used for "site";
        # first get the RHUI config file
        cfg_file = "/etc/rhui/rhui-tools.conf"
        rhuicfg = ConfigParser()
        _, stdout, _ = connection.exec_command("cat %s" % cfg_file)
        rhuicfg.readfp(stdout)
        # add the relevant config section if it's not there yet
        if not rhuicfg.has_section("docker"):
            rhuicfg.add_section("docker")
        # then get the credentials
        try:
            credentials = Helpers.get_credentials(connection, site)
            url = Helpers.get_registry_url(site)
            rhuicfg.set("docker", "docker_url", url)
            rhuicfg.set("docker", "docker_auth", "True")
        except RuntimeError:
            # the site isn't defined in the credentials file -> use the data passed to this method
            if len(data) == 3:
                rhuicfg.set("docker", "docker_url", data[2])
                rhuicfg.set("docker", "docker_auth", "True")
                credentials = data[:-1]
            elif len(data) == 1:
                rhuicfg.set("docker", "docker_url", data[0])
                rhuicfg.set("docker", "docker_auth", "False")
                credentials = False
            else:
                raise ValueError("the passed data is invalid")
        # if credentials are known, add them into the configuration
        if credentials:
            rhuicfg.set("docker", "docker_username", credentials[0])
            rhuicfg.set("docker", "docker_password", credentials[1])
        # otherwise, make sure the options don't exists in the configuration
        else:
            rhuicfg.remove_option("docker", "docker_username")
            rhuicfg.remove_option("docker", "docker_password")
        # back up the original config file (unless prevented)
        if backup:
            Expect.expect_retval(connection, "cp -f %s %s.bak" % (cfg_file, cfg_file))
        # save (rewrite) the configuration file with the newly added credentials
        stdin, _, _ = connection.exec_command("cat > %s" % cfg_file)
        rhuicfg.write(stdin)

    @staticmethod
    def restore_rhui_tools_conf(connection):
        """restore the backup copy of the RHUI tools configuration file"""
        cfg_file = "/etc/rhui/rhui-tools.conf"
        Expect.expect_retval(connection, "mv -f %s.bak %s" % (cfg_file, cfg_file))

    @staticmethod
    def is_iso_installation(connection):
        """return True if the remote uses a local (ISO based) yum repository, or False otherwise"""
        yum_repo_file_from_iso = "/etc/yum.repos.d/rhui-local.repo"
        return connection.recv_exit_status("test -f %s" % yum_repo_file_from_iso) == 0

    @staticmethod
    def is_registered(connection):
        """return True if the remote host is registered with RHSM, or False otherwise"""
        return connection.recv_exit_status("subscription-manager identity") == 0
