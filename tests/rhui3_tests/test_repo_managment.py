#! /usr/bin/python -tt

import nose, unittest, stitches, logging, yaml

from rhui3_tests_lib.rhuimanager import *
from rhui3_tests_lib.rhuimanager_repo import *

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

with open('/tmp/rhui3-tests/tests/rhui3_tests/rhui_manager.yaml', 'r') as file:
    doc = yaml.load(file)

rhui_login = doc['rhui_login']
rhui_pass = doc['rhui_pass']
new_rhui_pass = 'new_pass'
rhui_iso_date = doc['rhui_iso_date']

def test_01_repo_setup():
    '''Do initial rhui-manager run'''
    RHUIManager.initial_run(connection, username = rhui_login, password = rhui_pass)

def test_02_check_empty_repo_list():
    '''Check the repolist is empty'''
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])

def test_03_create_repo():
    '''Create custom repos '''
    RHUIManagerRepo.add_custom_repo(connection, "custom-i386-x86_64", "", "custom/i386/x86_64", "1", "y")
    RHUIManagerRepo.add_custom_repo(connection, "custom-x86_64-x86_64", "", "custom/x86_64/x86_64", "1", "y")
    RHUIManagerRepo.add_custom_repo(connection, "custom-i386-i386", "", "custom/i386/i386", "1", "y")

def test_04_check_custom_repo_list():
    '''Check the repolist contains 3 custom repos'''
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), ['custom-i386-i386', 'custom-i386-x86_64', 'custom-x86_64-x86_64'])

def test_05_repo_id_uniqness():
    '''Check that repo id should be unique'''
    RHUIManagerRepo.add_custom_repo(connection, "custom-i386-x86_64", "", "custom/i386/x86_64", "1", "y")

def test_06_upload_rpm_to_custom_repo():
    '''Upload content to custom repo'''
    RHUIManagerRepo.upload_content(connection, ["custom-i386-x86_64"], "/tmp/extra_rhui_files")

def test_cleanup():
    '''Remove 3 custom repos'''
    RHUIManagerRepo.delete_repo(connection, ["custom-i386-x86_64", "custom-x86_64-x86_64", "custom-i386-i386"])
    nose.tools.assert_equal(RHUIManagerRepo.list(connection), [])
