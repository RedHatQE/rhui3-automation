""" RHUIManager HAP functions """

import re

from stitches.expect import Expect, ExpectFailed, CTRL_C
from rhui3_tests_lib.rhuimanager import RHUIManager, PROCEED_PATTERN
from rhui3_tests_lib.hap import Hap

class HapAlreadyExistsError(ExpectFailed):
    """
    To be raised when trying to add an already tracked Hap
    """

class NoSuchHap(ExpectFailed):
    """
    To be raised e.g. when trying to select a non-existing Hap
    """

class InvalidSshKeyPath(ExpectFailed):
    """
    To be raised if rhui-manager wasn't able to locate the provided SSH key path
    """

class RHUIManagerHap(object):
    '''
    Represents -= Load-balancer (HAProxy) Management =- RHUI screen
    '''
    prompt = 'rhui \(loadbalancers\) => '

    @staticmethod
    def add_hap(connection, hap=Hap(), update=False):
        '''
        Register (add) a new HAP instance
        @param hap: rhuilib.hap.Hap instance
        @param update: Bool; update the hap if it is already tracked or raise ExpectFailed
        '''
        
        RHUIManager.screen(connection, "loadbalancers")
        Expect.enter(connection, "a")
        Expect.expect(connection, ".*Hostname of the HAProxy Load-balancer instance to register:")
        Expect.enter(connection, hap.host_name)
        state = Expect.expect_list(connection, [ \
            (re.compile(".*Username with SSH access to %s and sudo privileges:.*" % hap.host_name, re.DOTALL), 1),
            (re.compile(".*A HAProxy Load-balancer instance with that hostname exists.*Continue\?\s+\(y/n\): ", re.DOTALL), 2)
        ])
        if state == 2:
            # hap of the same hostname is already being tracked
            if not update:
                # but we don't wish to update its config: raise
                raise ExpectFailed("%s already tracked but update wasn't required" % hap.host_name)
            else:
                # we wish to update, send 'y' answer
                Expect.enter(connection, "y")
                # the question about user name comes now
                Expect.expect(connection, "Username with SSH access to %s and sudo privileges:" % hap.host_name)
        # if the execution reaches here, uesername question was already asked
        Expect.enter(connection, hap.user_name)
        Expect.expect(connection, "Absolute path to an SSH private key to log into %s as %s:" % (hap.host_name, hap.user_name))
        Expect.enter(connection, hap.ssh_key_path)
        state = Expect.expect_list(connection, [
            (re.compile(".*Cannot find file, please enter a valid path.*", re.DOTALL), 1),
            (PROCEED_PATTERN, 2)
        ])
        if state == 1:
            # don't know how to continue with invalid path: raise
            Expect.enter(connection, CTRL_C)
            Expect.enter(connection, "q")
            raise InvalidSshKeyPath(hap.ssh_key_path)
        # all OK, confirm
        Expect.enter(connection, "y")
        # some installation and configuration through Puppet happens here, let it take its time
        Expect.expect(connection, "The HAProxy Load-balancer was successfully configured." + ".*rhui \(.*\) =>", 180)


    @staticmethod
    def delete_haps(connection, *hapes):
        '''
        unregister (delete) HAP instance from the RHUI
        '''
        RHUIManager.screen(connection, "loadbalancers")
        Expect.enter(connection, "d")
        RHUIManager.select_items(connection, *hapes)
        Expect.enter(connection, "y")
        Expect.expect(connection, "Unregistered" + ".*rhui \(.*\) =>", 180)

    @staticmethod
    def list(connection):
        '''
        return the list of currently managed HAPs
        '''
        RHUIManager.screen(connection, "loadbalancers")
        # eating prompt!!
        lines = RHUIManager.list_lines(connection, prompt=RHUIManagerHap.prompt)
        ret = Hap.parse(lines)
        return [hap for _, hap in ret]


