#! /usr/bin/python -tt

import nose, stitches, logging

from rhui3_tests_lib.rhui_testcase import *
from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_cds import RHUIManagerCds


class test_0_simple_log_test(RHUITestcase):
    def _test(self):
        """ just testing the logging capabilities """
        logging.debug('This message from ' + str(__name__) + ' should go to the log file')
        logging.info('So should this')
        logging.warning('And this one as well')
        assert True == True