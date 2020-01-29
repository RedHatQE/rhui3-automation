""" RHUIManager CDS functions """

import re

from stitches.expect import Expect, CTRL_C

from rhui3_tests_lib.conmgr import ConMgr, SUDO_USER_NAME, SUDO_USER_KEY
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.instance import Instance

class InstanceAlreadyExistsError(Exception):
    """
    To be raised when trying to add an already tracked Cds or HAProxy
    """

class NoSuchInstance(Exception):
    """
    To be raised e.g. when trying to select a non-existing Cds or HAProxy
    """

class InvalidSshKeyPath(Exception):
    """
    To be raised if rhui-manager wasn't able to locate the provided SSH key path
    """

class RHUIManagerInstance(object):
    '''
    Represents -= Content Delivery Server (CDS) Management =- RHUI screen
    '''
    prompt_cds = r'rhui \(cds\) => '
    prompt_hap = r'rhui \(loadbalancers\) => '

    @staticmethod
    def add_instance(connection, screen,
                     hostname="", user_name=SUDO_USER_NAME, ssh_key_path=SUDO_USER_KEY,
                     update=False):
        '''
        Register (add) a new CDS or HAProxy instance
        @param hostname instance, or the default value for the screen type as ConMgr knows it
        @param update: Bool; update the cds or hap if it is already tracked or raise an exception
        '''
        if not hostname:
            if screen == "cds":
                hostname = ConMgr.get_cds_hostnames()[0]
            elif screen == "loadbalancers":
                hostname = ConMgr.get_haproxy_hostnames()[0]
            else:
                raise ValueError("hostname not given and screen invalid")
        # first check if the RHUA knows the host's SSH key, because if so, rhui-manager
        # won't ask you to confirm the key
        key_check_cmd = "ssh-keygen -F %s" % hostname
        # check if the host is known
        known_host = connection.recv_exit_status(key_check_cmd) == 0
        # run rhui-manager and add the instance
        RHUIManager.screen(connection, screen)
        Expect.enter(connection, "a")
        Expect.expect(connection, ".*Hostname of the .*instance to register:")
        Expect.enter(connection, hostname)
        state = Expect.expect_list(connection, [ \
            (re.compile(".*Username with SSH access to %s and sudo privileges:.*" % hostname,
                        re.DOTALL), 1),
            (re.compile(r".*instance with that hostname exists.*Continue\?\s+\(y/n\): ",
                        re.DOTALL), 2)
                                               ])
        if state == 2:
            # cds or haproxy of the same hostname is already being tracked
            if not update:
                # but we don't wish to update its config: say no, quit rhui-manager, and raise
                # an exception
                Expect.enter(connection, "n")
                RHUIManager.quit(connection)
                raise InstanceAlreadyExistsError("%s already tracked but update wasn't required" % \
                                                 hostname)
            else:
                # we wish to update, send 'y' answer
                Expect.enter(connection, "y")
                # the question about user name comes now
                Expect.expect(connection,
                              "Username with SSH access to %s and sudo privileges:" % hostname)
        # if the execution reaches here, uesername question was already asked
        Expect.enter(connection, user_name)
        Expect.expect(connection,
                      "Absolute path to an SSH private key to log into %s as ec2-user:" % hostname)
        Expect.enter(connection, ssh_key_path)
        state = Expect.expect_list(connection, [
            (re.compile(".*Cannot find file, please enter a valid path.*", re.DOTALL), 1),
            (re.compile(".*Checking that instance ports are reachable.*", re.DOTALL), 2)
        ])
        if state == 1:
            # don't know how to continue with invalid path: raise an exception
            Expect.enter(connection, CTRL_C)
            Expect.enter(connection, "q")
            raise InvalidSshKeyPath(ssh_key_path)
        # all OK
        # if the SSH key is unknown, rhui-manager now asks you to confirm it; say yes
        if not known_host:
            Expect.enter(connection, "y")
        # some installation and configuration through Puppet happens here, let it take its time
        RHUIManager.quit(connection, "The .*was successfully configured.", 180)


    @staticmethod
    def delete(connection, screen, instances):
        '''
        unregister (delete) one or more CDS or HAProxy instances from the RHUI
        '''
        # first check if the instances are really tracked
        tracked_instances = RHUIManagerInstance.list(connection, screen)
        hostnames = [instance.host_name for instance in tracked_instances]
        bad_instances = [i for i in instances if i not in hostnames]
        if bad_instances:
            raise NoSuchInstance(bad_instances)
        RHUIManager.screen(connection, screen)
        Expect.enter(connection, "d")
        RHUIManager.select_items(connection, instances)
        Expect.enter(connection, "y")
        RHUIManager.quit(connection, "Unregistered", 180)

    @staticmethod
    def delete_all(connection, screen):
        '''
        unregister (delete) all CDS or HAProxy instances from the RHUI
        '''
        RHUIManager.screen(connection, screen)
        Expect.enter(connection, "d")
        Expect.expect(connection, "Enter value .*:")
        Expect.enter(connection, "a")
        Expect.expect(connection, "Enter value .*:")
        Expect.enter(connection, "c")
        Expect.expect(connection, "Are you sure .*:")
        Expect.enter(connection, "y")
        RHUIManager.quit(connection, "Unregistered")

    @staticmethod
    def list(connection, screen):
        '''
        return the list of currently managed CDS or HAProxy instances
        '''
        RHUIManager.screen(connection, screen)
        # eating prompt!!
        lines = RHUIManager.list_lines(connection, r"rhui \(" + screen + r"\) => ")
        ret = Instance.parse(lines)
        Expect.enter(connection, 'q')
        return [cds for _, cds in ret]
