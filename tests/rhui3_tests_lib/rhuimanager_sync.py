""" RHUIManager Sync functions """

import re
import time

import nose

from stitches.expect import Expect, CTRL_C

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.util import Util

def _get_repo_status(connection, reponame):
    '''
    display repo sync summary
    '''
    RHUIManager.screen(connection, "sync")
    Expect.enter(connection, "dr")
    res = Expect.match(connection,
                       re.compile(r".*%s\s*\r\n([^\n]*)\r\n.*" % re.escape(reponame),
                                  re.DOTALL), [1], 60)[0]
    connection.cli.exec_command("killall -s SIGINT rhui-manager")
    res = Util.uncolorify(res)
    ret_list = res.split("             ")
    for i, _ in enumerate(ret_list):
        ret_list[i] = ret_list[i].strip()

    Expect.enter(connection, CTRL_C)
    Expect.enter(connection, "q")
    return ret_list

class RHUIManagerSync(object):
    '''
    Represents -= Synchronization Status =- RHUI screen
    '''
    @staticmethod
    def sync_repo(connection, repolist):
        '''
        sync an individual repository immediately
        '''
        RHUIManager.screen(connection, "sync")
        Expect.enter(connection, "sr")
        Expect.expect(connection, "Select one or more repositories.*for more commands:", 60)
        Expect.enter(connection, "l")
        RHUIManager.select(connection, repolist)
        RHUIManager.proceed_with_check(connection,
                                       "The following repositories will be scheduled " +
                                       "for synchronization:",
                                       repolist)
        RHUIManager.quit(connection)

    @staticmethod
    def check_sync_started(connection, repolist):
        '''ensure that sync started'''
        for repo in repolist:
            reposync = ["", "", "Never"]
            while reposync[2] in ["Never", "Unknown"]:
                time.sleep(10)
                reposync = _get_repo_status(connection, repo)
            if reposync[2] in ["Running", "Success"]:
                pass
            else:
                raise TypeError("Something went wrong")

    @staticmethod
    def wait_till_repo_synced(connection, repolist):
        '''
        wait until repo is synced
        '''
        for repo in repolist:
            reposync = ["", "", "Running"]
            while reposync[2] in ["Running", "Never", "Unknown"]:
                time.sleep(10)
                reposync = _get_repo_status(connection, repo)
            if reposync[2] == "Error":
                raise TypeError("The repo sync returned Error")
            nose.tools.assert_equal(reposync[2], "Success")

    @staticmethod
    def wait_till_pulp_tasks_finish(connection):
        '''
        wait until there are no running Pulp tasks
        '''
        # will be using pulp-admin, which requires you to log in to it
        # if the Pulp user cert has expired, delete it first of all;
        # if the Pulp user cert doesn't exist, use the one from rhui-manager
        # but create the .pulp directory (with the right perms) if it doesn't exist
        try:
            if Util.cert_expired(connection, "~/.pulp/user-cert.pem"):
                Expect.expect_retval(connection, "rm -f ~/.pulp/user-cert.pem")
        except OSError:
            pass
        rhua = ConMgr.get_rhua_hostname()
        Expect.expect_retval(connection,
                             "if ! [ -e ~/.pulp/user-cert.pem ]; then " +
                             "mkdir -p -m 700 ~/.pulp; " +
                             "ln -s ~/.rhui/%s/user.crt ~/.pulp/user-cert.pem; " % rhua +
                             "touch /tmp/pulploginhack; " +
                             "fi")
        while connection.recv_exit_status("pulp-admin tasks list | grep -q '^No tasks found'"):
            time.sleep(15)
        Expect.expect_retval(connection,
                             "if [ -f /tmp/pulploginhack ]; then " +
                             "rm -f ~/.pulp/user-cert.pem /tmp/pulploginhack; " +
                             "fi")
