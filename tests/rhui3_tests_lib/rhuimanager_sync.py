""" RHUIManager Sync functions """

import re

from stitches.expect import Expect
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.util import Util


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
        RHUIManager.proceed_with_check(connection, "The following repositories will be scheduled for synchronization:", repolist)
        RHUIManager.quit(connection)

    @staticmethod
    def get_repo_status(connection, reponame):
        '''
        display repo sync summary
        '''
        RHUIManager.screen(connection, "sync")
        Expect.enter(connection, "dr")
        reponame_quoted = reponame.replace(".", "\.")
        res = Expect.match(connection, re.compile(".*" + reponame_quoted + "\s*\r\n([^\n]*)\r\n.*", re.DOTALL), [1], 60)[0]
        connection.cli.exec_command("killall -s SIGINT rhui-manager")
        res = Util.uncolorify(res)
        ret_list = res.split("             ")
        for i in range(len(ret_list)):
            ret_list[i] = ret_list[i].strip()

        Expect.enter(connection, '\x03')
        Expect.enter(connection, 'q') 
        return ret_list
