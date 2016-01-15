#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhui_testcase import *
from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_cds import RHUIManagerCds

logging.basicConfig(level=logging.DEBUG)

def test_01_dummy():
    ''' dummy test to pass'''
    pass

def test_02_dummy():
    ''' dummy test to fail'''
    assert True == False
