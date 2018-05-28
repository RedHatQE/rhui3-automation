""" Red Hat subscription registration in RHUI """

import re

from stitches.expect import Expect
from rhui3_tests_lib.rhuimanager import RHUIManager

class RHUIManagerSubMan(object):
    '''
    Represents -= Subscriptions Manager =- RHUI screen
    '''
    prompt = r'rhui \(subscriptions\) => '

    @staticmethod
    def subscriptions_list(connection, what):
        '''
        list registered or available subscriptions
        '''
        if what == "registered":
            key = "l"
        elif what == "available":
            key = "a"
        else:
            raise ValueError("Unsupported list: " + what)

        RHUIManager.screen(connection, "subscriptions")
        Expect.enter(connection, key)
        lines = Expect.match(connection, re.compile("(.*)" + RHUIManagerSubMan.prompt,
                                                    re.DOTALL))[0]
        sub_list = []
        for line in lines.splitlines():
            # subscription names are on lines that start with two spaces
            if line[:2] == "  ":
                sub_list.append(line.strip())
        Expect.enter(connection, 'q')
        return sub_list

    @staticmethod
    def subscriptions_register(connection, names):
        '''
        register a Red Hat subscription in RHUI
        '''
        RHUIManager.screen(connection, "subscriptions")
        Expect.enter(connection, "r")
        RHUIManager.select(connection, names)
        RHUIManager.proceed_with_check(connection,
                                       "The following subscriptions will be registered:",
                                       names)
        RHUIManager.quit(connection)

    @staticmethod
    def subscriptions_unregister(connection, names):
        '''
        unregister a Red Hat subscription from RHUI
        '''
        RHUIManager.screen(connection, "subscriptions")
        Expect.enter(connection, "d")
        RHUIManager.select(connection, names)
        RHUIManager.proceed_with_check(connection,
                                       "The following subscriptions will be unregistered:",
                                       names)
        RHUIManager.quit(connection)
