"""Connection Manager for RHUI Test Cases"""

import re
import logging

from stitches.connection import Connection
from stitches.expect import Expect

SHORT_HOSTNAMES = {"RHUA": "rhua",
                   "CDS_LB": "cds",
                   "CDS": "cds",
                   "HAProxy": "hap",
                   "client": "cli",
                   "Atomic_client": "atomiccli"}
DOMAIN = "example.com"

USER_NAME = "root"
USER_KEY = "/root/.ssh/id_rsa_test"
SUDO_USER_NAME = "ec2-user"
SUDO_USER_KEY = "/root/.ssh/id_rsa_rhua"

def _list_hostnames(nodes, fake=False):
    """return a list of hostnames of the given node type"""
    # if "fake" is on and no hostnames are found, a hostname is made up and returned as
    # a single list item
    host_pattern = r"%s[0-9]+\.%s" % (nodes, re.escape(DOMAIN))
    with open("/etc/hosts") as hostsfile:
        all_hosts = hostsfile.read()
    matched_hosts = re.findall(host_pattern, all_hosts)
    if matched_hosts or not fake:
        return matched_hosts
    logging.warning("No hosts found. Using a fake hostname. Proceed with caution.")
    return ["%s01.%s" % (nodes, DOMAIN)]

class ConMgr():
    """simplify connections to RHUI nodes & clients by providing handy constants and methods"""
    @staticmethod
    def get_rhua_hostname():
        """return the hostname of the RHUA node"""
        return "%s.%s" % (SHORT_HOSTNAMES["RHUA"], DOMAIN)

    @staticmethod
    def get_cds_lb_hostname():
        """return the hostname of the CDS Load Balancer node"""
        return "%s.%s" % (SHORT_HOSTNAMES["CDS_LB"], DOMAIN)

    @staticmethod
    def get_cds_hostnames(fake=True):
        """return a list of CDS hostnames"""
        return _list_hostnames(SHORT_HOSTNAMES["CDS"], fake)

    @staticmethod
    def get_haproxy_hostnames(fake=True):
        """return a list of HAProxy hostnames; there's usually only a single HAProxy node in RHUI"""
        return _list_hostnames(SHORT_HOSTNAMES["HAProxy"], fake)

    @staticmethod
    def get_cli_hostnames(fake=True):
        """return a list of client hostnames"""
        return _list_hostnames(SHORT_HOSTNAMES["client"], fake)

    @staticmethod
    def get_atomic_cli_hostname():
        """return the hostname of the Atomic client"""
        return "%s.%s" % (SHORT_HOSTNAMES["Atomic_client"], DOMAIN)

    @staticmethod
    def connect(hostname="", username=USER_NAME, sshkey=USER_KEY):
        """create a connection to the specified host"""
        return Connection(hostname or ConMgr.get_rhua_hostname(), username, sshkey)

    @staticmethod
    def add_ssh_keys(connection, hostnames, keytype="rsa"):
        """gather SSH keys for the given hosts"""
        Expect.expect_retval(connection,
                             "ssh-keyscan -t %s %s >> ~/.ssh/known_hosts" % (keytype,
                                                                             " ".join(hostnames)))

    @staticmethod
    def remove_ssh_keys(connection, hostnames=""):
        """remove SSH keys that belong to the given (or all CDS & HAProxy) hosts"""
        key_file_exists = connection.recv_exit_status("test -f ~/.ssh/known_hosts") == 0
        if key_file_exists:
            if not hostnames:
                hostnames = ConMgr.get_cds_hostnames() + ConMgr.get_haproxy_hostnames()
            for host in hostnames:
                Expect.expect_retval(connection, "ssh-keygen -R %s" % host)
