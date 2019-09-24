""" RHSM integration in RHUI """

import re

from stitches.expect import Expect

class RHSMRHUI(object):
    """Subscription management for RHUI"""
    @staticmethod
    def register_system(connection, alt_rhaccount_file=""):
        """register with RHSM"""
        rhaccount_file = alt_rhaccount_file or "/tmp/extra_rhui_files/rhaccount.sh"
        if connection.recv_exit_status("test -f %s" % rhaccount_file):
            raise OSError("%s does not exist" % rhaccount_file)
        Expect.expect_retval(connection,
                             "source %s && " % rhaccount_file +
                             "subscription-manager register --type=rhui " +
                             "--username=$SM_USERNAME --password=$SM_PASSWORD",
                             timeout=40)

    @staticmethod
    def attach_subscription(connection, sub):
        """attach a supported subscription"""
        # 'sub' can be anything that sub-man can search by,
        # but typically it's the subscription name or the SKU
        # (or a substring with one or more wildcards)
        _, stdout, _ = connection.exec_command("subscription-manager list --available " +
                                               "--matches '%s' --pool-only 2>&1" % sub)
        with stdout as output:
            pool = output.read().decode().strip()
        if not re.match(r"^[0-9a-f]+$", pool):
            raise RuntimeError("Unable to fetch the pool ID for '%s'. Got: '%s'." % (sub, pool))
        # attach the pool
        Expect.expect_retval(connection, "subscription-manager attach --pool %s" % pool, timeout=60)

    @staticmethod
    def enable_rhui_repo(connection, base_rhel=True, gluster=False):
        """enable the RHUI 3 repo and by default also the base RHEL repo, disable everything else"""
        # the Gluster 3 repo can also be enabled if needed
        cmd = "subscription-manager repos --disable=* --enable=rhel-7-server-rhui-3-rpms"
        if base_rhel:
            cmd += " --enable=rhel-7-server-rhui-rpms"
        if gluster:
            cmd += " --enable=rh-gluster-3-for-rhel-7-server-rhui-rpms"
        Expect.expect_retval(connection, cmd, timeout=60)

    @staticmethod
    def unregister_system(connection):
        """unregister from RHSM"""
        Expect.expect_retval(connection, "subscription-manager unregister", timeout=20)
