""" Red Hat entitlement certificates """

import re

from stitches.expect import CTRL_C, Expect
from rhui3_tests_lib.rhuimanager import RHUIManager

PROMPT = r"rhui \(entitlements\) => "

class MissingCertificate(Exception):
    """
    Raised when the certificate file does not exist
    """

class BadCertificate(Exception):
    """
    Raised when a certificate is expired or invalid
    """

class IncompatibleCertificate(Exception):
    """
    Raised when a certificate is incompatible with RHUI
    """

class RHUIManagerEntitlements(object):
    '''
    Represents -= Entitlements Manager =- RHUI screen
    '''
    @staticmethod
    def list(connection):
        '''
        return the list of entitlements
        '''
        RHUIManager.screen(connection, "entitlements")
        lines = RHUIManager.list_lines(connection, prompt=PROMPT)
        Expect.enter(connection, 'q')
        return lines

    @staticmethod
    def list_rh_entitlements(connection):
        '''
        list Red Hat entitlements
        '''

        RHUIManager.screen(connection, "entitlements")
        Expect.enter(connection, "l")
        match = Expect.match(connection,
                             re.compile("(.*)" + PROMPT, re.DOTALL))

        matched_string = match[0].replace('l\r\n\r\nRed Hat Entitlements\r\n\r\n  ' +
                                          '\x1b[92mValid\x1b[0m\r\n    ', '', 1)

        entitlements_list = []
        pattern = re.compile('(.*?\r\n.*?pem)', re.DOTALL)
        for entitlement in pattern.findall(matched_string):
            entitlements_list.append(entitlement.strip())
        Expect.enter(connection, 'q')
        return entitlements_list


    @staticmethod
    def list_custom_entitlements(connection):
        '''
        list custom entitlements
        '''

        RHUIManager.screen(connection, "entitlements")
        Expect.enter(connection, "c")
        match = Expect.match(connection,
                             re.compile("c\r\n\r\nCustom Repository Entitlements\r\n\r\n(.*)" +
                                        PROMPT, re.DOTALL))[0]

        repo_list = []

        for line in match.splitlines():
            if "Name:" in line:
                repo_list.append(line.replace("Name:", "").strip())
        Expect.enter(connection, 'q')
        return sorted(repo_list)

    @staticmethod
    def upload_rh_certificate(connection, certificate_file="/tmp/extra_rhui_files/rhcert.pem"):
        '''
        upload a new or updated Red Hat content certificate
        '''
        bad_cert_msg = "The provided certificate is expired or invalid"
        incompatible_cert_msg = "does not contain any entitlements"

        RHUIManager.screen(connection, "entitlements")
        Expect.enter(connection, "u")
        Expect.expect(connection, "Full path to the new content certificate:")
        Expect.enter(connection, certificate_file)
        state = Expect.expect_list(connection,
                                   [(re.compile(".*The RHUI will be updated.*", re.DOTALL), 1),
                                    (re.compile(".*Cannot find file.*", re.DOTALL), 2)])
        if state == 2:
            Expect.enter(connection, CTRL_C)
            RHUIManager.quit(connection)
            raise MissingCertificate("No such certificate file: %s" % certificate_file)
        Expect.enter(connection, "y")
        match = Expect.match(connection,
                             re.compile("(.*)" + PROMPT, re.DOTALL))
        matched_string = match[0].replace('l\r\n\r\nRed Hat Entitlements\r\n\r\n  ' +
                                          '\x1b[92mValid\x1b[0m\r\n    ', '', 1)
        if bad_cert_msg in matched_string:
            Expect.enter(connection, 'q')
            raise BadCertificate()
        if incompatible_cert_msg in matched_string:
            Expect.enter(connection, 'q')
            raise IncompatibleCertificate()
        entitlements_list = []
        pattern = re.compile('(.*?\r\n.*?pem)', re.DOTALL)
        for entitlement in pattern.findall(matched_string):
            entitlements_list.append(entitlement.strip())
        Expect.enter(connection, 'q')
        return entitlements_list
