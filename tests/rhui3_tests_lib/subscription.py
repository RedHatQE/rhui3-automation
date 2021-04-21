""" RHSM integration in RHUI """

import re

from stitches.expect import Expect

from rhui3_tests_lib.helpers import Helpers

class RHSMRHUI(object):
    """Subscription management for RHUI"""
    @staticmethod
    def register_system(connection, username="", password="", fail_if_registered=False):
        """register with RHSM"""
        # if username or password isn't specified, it will be obtained using
        # the get_credentials method on the remote host -- only usable with the RHUA
        # if the system is already registered, it will be unregistered first,
        # unless fail_if_registered == True
        if fail_if_registered and Helpers.is_registered(connection):
            raise RuntimeError("The system is already registered.")
        if not username or not password:
            username, password = Helpers.get_credentials(connection)
        Expect.expect_retval(connection,
                             "subscription-manager register --force --type rhui " +
                             "--username %s --password %s" % (username, password),
                             timeout=60)

    @staticmethod
    def attach_subscription(connection, sub):
        """attach a supported subscription"""
        # 'sub' can be anything that sub-man can search by,
        # but typically it's the subscription name or the SKU
        # (or a substring with one or more wildcards)
        _, stdout, _ = connection.exec_command("subscription-manager list --available " +
                                               "--matches '%s' --pool-only 2>&1" % sub)
        pools = stdout.read().decode().splitlines()
        if not pools:
            raise RuntimeError("There are no available pools.")
        if not all(re.match(r"^[0-9a-f]+$", pool) for pool in pools):
            raise RuntimeError("This doesn't look like a list of pools: '%s'." % pools)
        pool_opts = " ".join(["--pool %s" % pool for pool in pools])
        # attach the pool(s)
        Expect.expect_retval(connection, "subscription-manager attach %s" % pool_opts, timeout=60)

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

    @staticmethod
    def sca_setup(connection):
        """set the RHUA up for Simple Content Access (SCA) testing"""
        Expect.expect_retval(connection, "cp /tmp/extra_rhui_files/SCA/* /etc/pki/entitlement/")

    @staticmethod
    def sca_cleanup(connection):
        """clean up the (SCA) cert and key"""
        Expect.expect_retval(connection, "rm -f /etc/pki/entitlement/*")
