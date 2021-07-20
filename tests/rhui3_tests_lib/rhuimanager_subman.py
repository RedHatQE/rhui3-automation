""" Red Hat subscription registration in RHUI """

import re

from stitches.expect import Expect, ExpectFailed
from rhui3_tests_lib.rhuimanager import RHUIManager

PROMPT = r"rhui \(subscriptions\) => "

class RHUIManagerSubMan():
    """Represents -= Subscriptions Manager =- RHUI screen"""
    @staticmethod
    def subscriptions_list(connection, what):
        """list registered or available subscriptions"""
        if what == "registered":
            key = "l"
        elif what == "available":
            key = "a"
        else:
            raise ValueError("Unsupported list: %s. Use 'registered' or 'available'." % what)

        RHUIManager.screen(connection, "subscriptions")
        Expect.enter(connection, key)
        lines = Expect.match(connection, re.compile("(.*)" + PROMPT, re.DOTALL))[0]
        # subscription names are on lines that start with two spaces
        sub_list = [line.strip() for line in lines.splitlines() if line.startswith("  ")]
        Expect.enter(connection, "q")
        return sub_list

    @staticmethod
    def subscriptions_register(connection, names):
        """register one or more Red Hat subscriptions in RHUI"""
        RHUIManager.screen(connection, "subscriptions")
        Expect.enter(connection, "r")
        try:
            RHUIManager.select(connection, names)
        except ExpectFailed:
            Expect.enter(connection, "q")
            raise RuntimeError("subscription(s) not available: %s" % names) from None
        RHUIManager.proceed_with_check(connection,
                                       "The following subscriptions will be registered:",
                                       names)
        RHUIManager.quit(connection)

    @staticmethod
    def subscriptions_unregister(connection, names):
        """unregister one or more Red Hat subscriptions from RHUI"""
        RHUIManager.screen(connection, "subscriptions")
        Expect.enter(connection, "d")
        try:
            RHUIManager.select(connection, names)
        except ExpectFailed:
            Expect.enter(connection, "q")
            raise RuntimeError("subscription(s) not registered: %s" % names) from None
        RHUIManager.proceed_with_check(connection,
                                       "The following subscriptions will be unregistered:",
                                       names)
        RHUIManager.quit(connection)
