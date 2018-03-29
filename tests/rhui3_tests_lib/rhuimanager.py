import re
import logging

from stitches.expect import Expect, ExpectFailed
from rhui3_tests_lib.util import Util

SELECT_PATTERN = re.compile('^  (x|-)  (\d+) :')
PROCEED_PATTERN = re.compile('.*Proceed\? \(y/n\).*', re.DOTALL)
CONFIRM_PATTERN_STRING = "Enter value \([\d]+-[\d]+\) to toggle selection, 'c' to confirm selections, or '\?' for more commands: "

class NotSelectLine(ValueError):
    """
    to be raised when the line isn't actually a selection line
    """

class RHUIManager(object):
    '''
    Basic functions to manage rhui-manager.
    '''

    @staticmethod
    def selected_line(line):
        """
        return True/False, item list index
        """
        match = SELECT_PATTERN.match(line)
        if match is None:
            raise NotSelectLine(line)
        return match.groups()[0] == 'x', int(match.groups()[1])

    @staticmethod
    def list_lines(connection, prompt='', enter_l=True):
        '''
        list items on screen returning a list of lines seen
        eats prompt!!!
        '''
        if enter_l:
            Expect.enter(connection, "l")
        match = Expect.match(connection, re.compile("(.*)" + prompt, re.DOTALL))
        return match[0].split('\r\n')

    @staticmethod
    def select(connection, value_list):
        '''
        Select list of items (multiple choice)
        '''
        for value in value_list:
            match = Expect.match(connection, re.compile(".*-\s+([0-9]+)\s*:[^\n]*\s+" + value + "\s*\n.*for more commands:.*", re.DOTALL))
            Expect.enter(connection, match[0])
            match = Expect.match(connection, re.compile(".*x\s+([0-9]+)\s*:[^\n]*\s+" + value + "\s*\n.*for more commands:.*", re.DOTALL))
            Expect.enter(connection, "l")
        Expect.enter(connection, "c")

    @staticmethod
    def select_items(connection, itemslist):
        '''
        Select list of items (multiple choice)
        '''
        lines = RHUIManager.list_lines(connection, prompt=CONFIRM_PATTERN_STRING, enter_l=False)
        for item in itemslist:
            for line in lines:
                if item in line:
                     index = list(filter(str.isdigit, str(lines[lines.index(line)-1])))[0]
                     Expect.enter(connection, index)
                     break
        Expect.enter(connection, "c")

    @staticmethod
    def select_one(connection, item):
        '''
        Select one item (single choice)
        '''
        match = Expect.match(connection, re.compile(".*([0-9]+)\s+-\s+" + item + "\s*\n.*to abort:.*", re.DOTALL))
        Expect.enter(connection, match[0])

    @staticmethod
    def select_all(connection):
        '''
        Select all items
        '''
        Expect.expect(connection, "Enter value .*:")
        Expect.enter(connection, "a")
        Expect.expect(connection, "Enter value .*:")
        Expect.enter(connection, "c")

    @staticmethod
    def quit(connection, prefix="", timeout=10):
        '''
        Quit from rhui-manager

        Use @param prefix to specify something to expect before exiting
        Use @param timeout to specify the timeout
        '''
        Expect.expect(connection, prefix + ".*rhui \(.*\) =>", timeout)
        Expect.enter(connection, "q")

    @staticmethod
    def logout(connection, prefix=""):
        '''
        Logout from rhui-manager

        Use @param prefix to specify something to expect before exiting
        '''
        Expect.expect(connection, prefix + ".*rhui \(.*\) =>")
        Expect.enter(connection, "logout")

    @staticmethod
    def proceed_without_check(connection):
        '''
        Proceed without check (avoid this function when possible!)
        '''
        Expect.expect(connection, "Proceed\? \(y/n\)")
        Expect.enter(connection, "y")

    @staticmethod
    def proceed_with_check(connection, caption, value_list, skip_list=[]):
        '''
        Proceed with prior checking the list of values

        Use @param skip_list to skip meaningless 2nd-level headers
        '''
        selected = Expect.match(connection, re.compile(".*" + caption + "\r\n(.*)\r\nProceed\? \(y/n\).*", re.DOTALL))[0].split("\r\n")
        selected_clean = []
        for val in selected:
            val = val.strip()
            val = val.replace("\t", " ")
            val = ' '.join(val.split())
            val = val.replace("(", "\(")
            val = val.replace(")", "\)")
            if val != "" and not val in skip_list:
                selected_clean.append(val)
        if sorted(selected_clean) != sorted(value_list):
            logging.debug("Selected: " + str(selected_clean))
            logging.debug("Expected: " + str(value_list))
            raise ExpectFailed()
        Expect.enter(connection, "y")

    @staticmethod
    def screen(connection, screen_name):
        '''
        Open specified rhui-manager screen
        '''
        Expect.enter(connection, "rhui-manager")
        Expect.expect(connection, "rhui \(home\) =>")
        if screen_name in ["repo", "cds", "loadbalancers", "sync", "identity", "users"]:
            key = screen_name[:1]
        elif screen_name == "client":
            key = "e"
        elif screen_name == "entitlements":
            key = "n"
        Expect.enter(connection, key)
        Expect.expect(connection, "rhui \(" + screen_name + "\) =>")

    @staticmethod
    def initial_run(connection, username="admin", password="admin"):
        '''
        Do rhui-manager initial run
        '''
        Expect.enter(connection, "rhui-manager")
        state = Expect.expect_list(connection, [(re.compile(".*RHUI Username:.*", re.DOTALL),1),
                                                (re.compile(".*rhui \(home\) =>.*", re.DOTALL), 2)])
        if state == 1:
            Expect.enter(connection, username)
            Expect.expect(connection, "RHUI Password:")
            Expect.enter(connection, password)
            password_state = Expect.expect_list(connection, [(re.compile(".*Invalid login.*", re.DOTALL),1),
                                                (re.compile(".*rhui \(home\) =>.*", re.DOTALL), 2)])
            if password_state == 1:
                initial_password = Util.get_initial_password(connection)
                Expect.enter(connection, "rhui-manager")
                Expect.expect(connection, ".*RHUI Username:")
                Expect.enter(connection, username)
                Expect.expect(connection, "RHUI Password:")
                Expect.enter(connection, initial_password)
                Expect.expect(connection, "rhui \(home\) =>")
            else:
                pass
        else:
            # initial step was already performed by someone
            pass

    @staticmethod
    def change_user_password(connection, password='admin'):
        '''
        Change the password of rhui-manager user
        '''
        Expect.enter(connection, "p")
        Expect.expect(connection, "Username:")
        Expect.enter(connection, 'admin')
        Expect.expect(connection, "New Password:")
        Expect.enter(connection, password)
        Expect.expect(connection, "Re-enter Password:")
        Expect.enter(connection, password)

    @staticmethod
    def remove_rh_certs(connection):
        '''
        Remove all RH certificates from RHUI
        '''
        Expect.enter(connection, "find /etc/pki/rhui/redhat/ -name '*.pem' -delete")
        Expect.expect(connection, "root@")
