""" Utility functions """

import os
import random
import re
import string
import tempfile
import time
import yaml

from stitches.expect import Expect, ExpectFailed


class Util(object):
    '''
    Utility functions for instances
    '''
    @staticmethod
    def uncolorify(instr):
        """ Remove colorification """
        res = instr.replace("\x1b", "")
        res = res.replace("[91m", "")
        res = res.replace("[92m", "")
        res = res.replace("[93m", "")
        res = res.replace("[0m", "")
        return res

    @staticmethod
    def generate_gpg_key(connection,
                         keytype="DSA",
                         keysize="1024",
                         keyvalid="0",
                         realname="Key Owner",
                         email="kowner@example.com",
                         comment="comment"):
        '''
        Generate GPG keypair

        WARNING!!!
        It takes too long to wait for this operation to complete... use pre-created keys instead!
        '''
        Expect.enter(connection, "cat > /tmp/gpgkey << EOF")
        Expect.enter(connection, "Key-Type: " + keytype)
        Expect.enter(connection, "Key-Length: " + keysize)
        Expect.enter(connection, "Subkey-Type: ELG-E")
        Expect.enter(connection, "Subkey-Length: " + keysize)
        Expect.enter(connection, "Name-Real: " + realname)
        Expect.enter(connection, "Name-Comment: " + comment)
        Expect.enter(connection, "Name-Email: " + email)
        Expect.enter(connection, "Expire-Date: " + keyvalid)
        Expect.enter(connection, "%commit")
        Expect.enter(connection, "%echo done")
        Expect.enter(connection, "EOF")
        Expect.expect(connection, "root@")

        Expect.enter(connection, "gpg --gen-key --no-random-seed-file --batch /tmp/gpgkey")
        for _ in range(1, 200):
            Expect.enter(connection,
                         ''.join(random.choice(string.ascii_lowercase) for x in range(200)))
            time.sleep(1)
            try:
                Expect.expect(connection, "gpg: done")
                break
            except ExpectFailed:
                continue

    @staticmethod
    def remove_amazon_rhui_conf_rpm(connection):
        '''
        Remove Amazon RHUI config rpm (owning /usr/sbin/choose_repo.py) from instance
        downlad the rpm first, though, so the configuration can be restored if needed
        (but don't fail if the download is unsuccessful, just try your luck)
        note that more than one rpm can actually own the file, typically on beta AMIs
        the rpm(s) is/are saved in /root
        '''
        Expect.expect_retval(connection,
                             "file=/usr/sbin/choose_repo.py; " +
                             "if [ -f $file ]; then" +
                             "  package=`rpm -qf --queryformat '%{NAME} ' $file`;" +
                             "  yumdownloader $package;" +
                             "  rpm -e $package;" +
                             "fi",
                             timeout=60)

    @staticmethod
    def remove_rpm(connection, rpmlist):
        '''
        Remove installed rpms from cli
        '''
        Expect.expect_retval(connection, "rpm -e " + ' '.join(rpmlist))

    @staticmethod
    def install_pkg_from_rhua(rhua_connection, connection, pkgpath):
        '''
        Transfer package from RHUA host to the instance and install it
        @param pkgpath: path to package on RHUA node
        '''
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.close()
        rhua_connection.sftp.get(pkgpath, tfile.name)
        file_extension = os.path.splitext(pkgpath)[1]
        if file_extension == '.rpm':
            connection.sftp.put(tfile.name, tfile.name + file_extension)
            os.unlink(tfile.name)
            Expect.expect_retval(connection, "rpm -i " + tfile.name + file_extension)
        else:
            connection.sftp.put(tfile.name, tfile.name + '.tar.gz')
            os.unlink(tfile.name)
            Expect.expect_retval(connection, "tar -xzf" + tfile.name + ".tar.gz && ./install.sh")

    @staticmethod
    def get_initial_password(connection, pwdfile="/etc/rhui-installer/answers.yaml"):
        '''
        Read login password from file
        @param pwdfile: file with the password (defaults to /etc/rhui-installer/answers.yaml)
        '''
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.close()
        connection.sftp.get(pwdfile, tfile.name)
        with open(tfile.name, 'r') as filed:
            doc = yaml.load(filed)
            password = doc["rhua"]["rhui_manager_password"]
        if password[-1:] == '\n':
            password = password[:-1]
        return password

    @staticmethod
    def get_rpm_details(rpmpath):
        '''
        Get (name-version-release, name) pair for local rpm file
        '''
        if rpmpath:
            rpmnvr = os.popen("basename " + rpmpath).read()[:-1]
            rpmname = os.popen("rpm -qp --queryformat '%{NAME}\n' " +
                               rpmpath +
                               " 2>/dev/null").read()[:-1]
            return (rpmnvr, rpmname)
        return (None, None)

    @staticmethod
    def get_rhel_version(connection):
        '''
        get RHEL X.Y version (dict with two integers representing the major and minor version)
        '''
        _, stdout, _ = connection.exec_command(r"egrep -o '[0-9]+\.[0-9]+' /etc/redhat-release")
        with stdout as output:
            version = output.read().decode().strip().split(".")
        try:
            version_dict = {"major": int(version[0]), "minor": int(version[1])}
            return version_dict
        except ValueError:
            return None

    @staticmethod
    def wildcard(hostname):
        """ Hostname wildcard """
        hostname_particles = hostname.split('.')
        hostname_particles[0] = "*"
        return ".".join(hostname_particles)

    @staticmethod
    def esc_parentheses(name):
        '''
        helper method to escape parentheses so they can be safely used inside
        regular expressions in Expect methods
        '''
        return name.replace("(", r"\(").replace(")", r"\)")

    @staticmethod
    def format_repo(name, version="", kind=""):
        '''
        helper method to put together a repo name, version, and kind
        the way RHUI repos are called in rhui-manager
        '''
        repo = name
        if version:
            repo += " (%s)" % version
        if kind:
            repo += " (%s)" % kind
        return repo

    @staticmethod
    def get_cds_hostnames():
        '''
        read CDS hostnames from /etc/hosts and return a list of them
        '''
        cds_pattern = r"cds[0-9]+\.example\.com"
        with open("/etc/hosts") as hostsfile:
            all_hosts = hostsfile.read()
        return re.findall(cds_pattern, all_hosts)

    @staticmethod
    def get_rpms_in_dir(connection, directory):
        '''
        return a list of RPM files in the directory
        '''
        _, stdout, _ = connection.exec_command("cd %s && ls -w1 *.rpm" % directory)
        with stdout as output:
            rpms = output.read().decode().splitlines()
            return rpms
