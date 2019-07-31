""" RHSM integration in RHUI """

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
    def attach_rhui_sku(connection):
        """check if the RHUI SKU is available and attach it if so"""
        Expect.expect_retval(connection,
                             "subscription-manager list --available " +
                             "--matches=RC1116415 --pool-only > /tmp/rhuipool.txt && " +
                             "test -s /tmp/rhuipool.txt && " +
                             "[[ \"$(cat /tmp/rhuipool.txt)\" =~ ^[0-9a-f]+$ ]] && " +
                             "subscription-manager attach --pool=$(< /tmp/rhuipool.txt)",
                             timeout=60)

    @staticmethod
    def enable_rhui_3_repo(connection):
        """enable the RHUI 3 repo"""
        Expect.expect_retval(connection,
                             "subscription-manager repos --enable=rhel-7-server-rhui-3-rpms",
                             timeout=30)

    @staticmethod
    def unregister_system(connection):
        """unregister from RHSM"""
        Expect.expect_retval(connection, "rm -f /tmp/rhuipool.txt")
        Expect.expect_retval(connection, "subscription-manager unregister", timeout=20)
