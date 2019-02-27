"""Helper Functions for RHUI Test Cases"""

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
