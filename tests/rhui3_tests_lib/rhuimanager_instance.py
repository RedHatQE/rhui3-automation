""" RHUIManager CDS functions """

import re

from stitches.expect import Expect, ExpectFailed, CTRL_C
from rhui3_tests_lib.rhuimanager import RHUIManager, PROCEED_PATTERN
from rhui3_tests_lib.instance import Instance

class InstanceAlreadyExistsError(ExpectFailed):
    """
    To be raised when trying to add an already tracked Cds or HAProxy
    """

class NoSuchInstance(ExpectFailed):
    """
    To be raised e.g. when trying to select a non-existing Cds or HAProxy
    """

class InvalidSshKeyPath(ExpectFailed):
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
                     hostname, user_name="ec2-user", ssh_key_path="/root/.ssh/id_rsa_rhua",
                     update=False):
        '''
        Register (add) a new CDS or HAProxy instance
        @param hostname instance
        @param update: Bool; update the cds or hap if it is already tracked or raise ExpectFailed
        '''

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
                # but we don't wish to update its config: raise
                raise ExpectFailed("%s already tracked but update wasn't required" % hostname)
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
            (PROCEED_PATTERN, 2)
        ])
        if state == 1:
            # don't know how to continue with invalid path: raise
            Expect.enter(connection, CTRL_C)
            Expect.enter(connection, "q")
            raise InvalidSshKeyPath(ssh_key_path)
        # all OK, confirm
        Expect.enter(connection, "y")
        # some installation and configuration through Puppet happens here, let it take its time
        RHUIManager.quit(connection, "The .*was successfully configured.", 180)


    @staticmethod
    def delete(connection, screen, instances):
        '''
        unregister (delete) CDS instance from the RHUI
        '''
        RHUIManager.screen(connection, screen)
        Expect.enter(connection, "d")
        RHUIManager.select_items(connection, instances)
        Expect.enter(connection, "y")
        RHUIManager.quit(connection, "Unregistered", 180)

    @staticmethod
    def list(connection, screen):
        '''
        return the list of currently managed CDSes
        '''
        RHUIManager.screen(connection, screen)
        # eating prompt!!
        lines = RHUIManager.list_lines(connection, r"rhui \(" + screen + r"\) => ")
        ret = Instance.parse(lines)
        Expect.enter(connection, 'q')
        return [cds for _, cds in ret]
