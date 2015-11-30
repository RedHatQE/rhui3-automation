#! /usr/bin/python -tt

import nose, stitches, logging

from rhui3_tests_lib.rhui_testcase import *
from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_cds import RHUIManagerCds

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_master")


def test_1():
    ''' dummy test to pass'''
    pass

def test_2():
    ''' dummy test to fail'''
    assert True != False

def test_3():
    cds_list=RHUIManagerCds.list(connection)
    assert []==cds_list
