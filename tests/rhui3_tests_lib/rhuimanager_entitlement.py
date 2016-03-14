""" Red Hat entitlement certificates """

import re

from stitches.expect import Expect, ExpectFailed, CTRL_C
from rhui3_tests_lib.rhuimanager import RHUIManager, PROCEED_PATTERN
# from sepolgen import matching

class InvalidCertificatePath(ExpectFailed):
    """
    To be risen in case rhui-manager wasn't able to locate provided certificate path
    """

class RHUIManagerEntitlements(object):
    '''
    Represents -= Entitlements Manager =- RHUI screen
    '''
    prompt = 'rhui \(entitlements\) => '
 
    @staticmethod
    def list(connection):
        '''
        return the list of entitlements
        '''
        RHUIManager.screen(connection, "entitlements")
        lines = RHUIManager.list_lines(connection, prompt=RHUIManagerEntitlements.prompt)
        return lines
    
    @staticmethod
    def list_rh_entitlements(connection):
        '''
        list Red Hat entitlements
        '''
        
        RHUIManager.screen(connection, "entitlements")
        Expect.enter(connection, "l")
        match = Expect.match(connection, re.compile("(.*)" + RHUIManagerEntitlements.prompt, re.DOTALL))
        
        matched_string = match[0].replace('l\r\n\r\nRed Hat Entitlements\r\n\r\n  \x1b[92mValid\x1b[0m\r\n    ', '', 1)
        
        entitlements_list = []
        pattern = re.compile('(.*?\r\n.*?pem)', re.DOTALL)
        for entitlement in pattern.findall(matched_string):
            entitlements_list.append(entitlement.strip())
        return entitlements_list


    @staticmethod
    def list_custom_entitlements(connection):
        '''
        list custom entitlements
        '''
         
        RHUIManager.screen(connection, "entitlements")
        Expect.enter(connection, "c")
        match = Expect.match(connection, re.compile("c\r\n\r\nCustom Repository Entitlements\r\n\r\n(.*)" + RHUIManagerEntitlements.prompt, re.DOTALL))
        
        repo_list = []
        
        if match[0].find('No custom repositories exist in the RHUI') != -1:
            return repo_list

    @staticmethod
    def upload_rh_certificate(connection):
        '''
        upload a new or updated Red Hat content certificate
        '''
         
        RHUIManager.screen(connection, "entitlements")
        Expect.enter(connection, "u")
        Expect.expect(connection, "Full path to the new content certificate:")
        Expect.enter(connection, "/tmp/extra_files/rest-team/rest-team.pem")
        Expect.expect(connection, "The RHUI will be updated with the following certificate:")
        Expect.enter(connection, "y")
        match = Expect.match(connection, re.compile("(.*)" + RHUIManagerEntitlements.prompt, re.DOTALL))
        matched_string = match[0].replace('l\r\n\r\nRed Hat Entitlements\r\n\r\n  \x1b[92mValid\x1b[0m\r\n    ', '', 1)
        entitlements_list = []
        pattern = re.compile('(.*?\r\n.*?pem)', re.DOTALL)
        for entitlement in pattern.findall(matched_string):
            entitlements_list.append(entitlement.strip())
        return entitlements_list

