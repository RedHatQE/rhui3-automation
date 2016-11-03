#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhui_testcase import *
from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_cds import RHUIManagerCds

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_dummy():
    ''' dummy test to pass'''
    pass

def test_02_dummy():
    ''' dummy test to fail'''
    assert True == False

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)
