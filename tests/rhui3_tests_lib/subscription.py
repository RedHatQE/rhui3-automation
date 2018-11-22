""" RHSM integration in RHUI """

from stitches.expect import Expect
from rhui3_tests_lib.util import Util

class RHSMRHUI(object):
    '''
        Subscription management for RHUI
    '''
    @staticmethod
    def register_system(connection):
        '''
            register with RHSM
        '''
        rhaccount_file = "/tmp/extra_rhui_files/rhaccount.sh"
        if connection.recv_exit_status("test -f " + rhaccount_file) != 0:
            raise OSError(rhaccount_file + " does not exist")
        # on RHEL 7.5, update subscription-manager first (due to RHBZ#1554482)
        rhel_version = Util.get_rhel_version(connection)
        if rhel_version["major"] == 7 and rhel_version["minor"] == 5:
            Expect.expect_retval(connection, "yum -y update subscription-manager", timeout=30)
        Expect.expect_retval(connection, "source " + rhaccount_file + " && " +
                             "subscription-manager register --type=rhui " +
                             "--username=$SM_USERNAME --password=$SM_PASSWORD",
                             timeout=40)

    @staticmethod
    def attach_rhui_sku(connection):
        '''
            check if the RHUI SKU is available and attach it if so
        '''
        Expect.expect_retval(connection, "subscription-manager list --available " +
                             "--matches=RC1116415 --pool-only > /tmp/rhuipool.txt && " +
                             "test -s /tmp/rhuipool.txt && " +
                             "[[ \"$(cat /tmp/rhuipool.txt)\" =~ ^[0-9a-f]+$ ]] && " +
                             "subscription-manager attach --pool=$(< /tmp/rhuipool.txt)",
                             timeout=60)

    @staticmethod
    def enable_rhui_3_repo(connection):
        '''
            enable the RHUI 3 repo
        '''
        rhel_version = Util.get_rhel_version(connection)["major"]
        # the RHUI 3 for RHEL 6 repo tends to be unavailable with the test account :/ try using beta
        if rhel_version == 6:
            Expect.expect_retval(connection, "subscription-manager repos " +
                                 "--enable=rhel-6-server-rhui-3-rpms || " +
                                 "subscription-manager repos " +
                                 "--enable=rhel-6-server-rhui-3-beta-rpms",
                                 timeout=60)
        else:
            Expect.expect_retval(connection, "subscription-manager repos --enable=rhel-" +
                                 str(rhel_version) + "-server-rhui-3-rpms",
                                 timeout=30)

    @staticmethod
    def unregister_system(connection):
        '''
            unregister from RHSM
        '''
        Expect.expect_retval(connection, "rm -f /tmp/rhuipool.txt")
        Expect.expect_retval(connection, "subscription-manager unregister", timeout=20)
