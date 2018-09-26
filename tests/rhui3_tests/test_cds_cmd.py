'''CDS management tests for the CLI'''

from os.path import basename
import random
import re

import logging
import nose
import stitches

from rhui3_tests_lib.rhui_cmd import RHUICLI
from rhui3_tests_lib.rhuimanager import RHUIManager

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

CDS_PATTERN = r"cds[0-9]+\.example\.com"
with open("/etc/hosts") as hostsfile:
    ALL_HOSTS = hostsfile.read()
CDS_HOSTNAMES = re.findall(CDS_PATTERN, ALL_HOSTS)

def setup():
    '''
    announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_init():
    '''
    log in to RHUI
    '''
    RHUIManager.initial_run(CONNECTION)

def test_02_list_cds():
    '''
    check if there are no CDSs
    '''
    cds_list = RHUICLI.list(CONNECTION, "cds")
    nose.tools.eq_(cds_list, [])

def test_03_add_cds():
    '''
    add all known CDSs
    '''
    for cds in CDS_HOSTNAMES:
        status = RHUICLI.add(CONNECTION, "cds", cds, unsafe=True)
        nose.tools.ok_(status, msg="unexpected %s installation status: %s" % (cds, status))

def test_04_list_cds():
    '''
    check if the CDSes have been added
    '''
    cds_list = RHUICLI.list(CONNECTION, "cds")
    nose.tools.eq_(cds_list, CDS_HOSTNAMES)

def test_05_reinstall_cds():
    '''
    add one of the CDSs again by reinstalling it
    '''
    # choose a random CDS hostname from the list
    cds = random.choice(CDS_HOSTNAMES)
    status = RHUICLI.reinstall(CONNECTION, "cds", cds)
    nose.tools.ok_(status, msg="unexpected %s reinstallation status: %s" % (cds, status))

def test_06_list_cds():
    '''
    check if the CDSs are still tracked, and nothing extra has appeared
    '''
    cds_list = RHUICLI.list(CONNECTION, "cds")
    # the reinstalled CDS is now the last one in the list; the list may not be the same, sort it!
    cds_list.sort()
    nose.tools.eq_(cds_list, CDS_HOSTNAMES)

def test_07_readd_cds_noforce():
    '''
    check if rhui refuses to add a CDS again if no extra parameter is used
    '''
    # again choose a random CDS hostname from the list
    cds = random.choice(CDS_HOSTNAMES)
    status = RHUICLI.add(CONNECTION, "cds", cds, unsafe=True)
    nose.tools.ok_(not status, msg="unexpected %s readdition status: %s" % (cds, status))

def test_08_list_cds():
    '''
    check if nothing extra has been added
    '''
    cds_list = RHUICLI.list(CONNECTION, "cds")
    # the readded CDS is now the last one in the list; the list may not be the same, sort it!
    cds_list.sort()
    nose.tools.eq_(cds_list, CDS_HOSTNAMES)

def test_09_readd_cds():
    '''
    add one of the CDSs again by using force
    '''
    # again choose a random CDS hostname from the list
    cds = random.choice(CDS_HOSTNAMES)
    status = RHUICLI.add(CONNECTION, "cds", cds, force=True, unsafe=True)
    nose.tools.ok_(status, msg="unexpected %s readdition status: %s" % (cds, status))

def test_10_list_cds():
    '''
    check if the CDSs are still tracked, and nothing extra has appeared
    '''
    cds_list = RHUICLI.list(CONNECTION, "cds")
    # the readded CDS is now the last one in the list; the list may not be the same, sort it!
    cds_list.sort()
    nose.tools.eq_(cds_list, CDS_HOSTNAMES)

def test_11_delete_cds_noforce():
    '''
    check if rhui refuses to delete the node when it's the only/last one and force isn't used
    '''
    # delete all but the first node (if there are more nodes to begin with)
    if len(CDS_HOSTNAMES) > 1:
        RHUICLI.delete(CONNECTION, "cds", CDS_HOSTNAMES[1:])
    status = RHUICLI.delete(CONNECTION, "cds", [CDS_HOSTNAMES[0]])
    nose.tools.ok_(not status, msg="unexpected deletion status: %s" % status)

def test_12_list_cds():
    '''
    check if the last CDS really hasn't been deleted
    '''
    cds_list = RHUICLI.list(CONNECTION, "cds")
    nose.tools.eq_(cds_list, [CDS_HOSTNAMES[0]])


def test_13_delete_cds_force():
    '''
    delete the last CDS forcibly
    '''
    status = RHUICLI.delete(CONNECTION, "cds", [CDS_HOSTNAMES[0]], force=True)
    nose.tools.ok_(status, msg="unexpected deletion status: %s" % status)

def test_14_list_cds():
    '''
    check if the last CDS has been deleted
    '''
    cds_list = RHUICLI.list(CONNECTION, "cds")
    nose.tools.eq_(cds_list, [])

def test_15_add_bad_cds():
    '''
    try adding an incorrect CDS hostname, expect trouble and nothing added
    '''
    status = RHUICLI.add(CONNECTION, "cds", "foo" + CDS_HOSTNAMES[0])
    nose.tools.ok_(not status, msg="unexpected addition status: %s" % status)
    cds_list = RHUICLI.list(CONNECTION, "cds")
    nose.tools.eq_(cds_list, [])

# currently broken, see RHBZ#1409697
# def test_16_delete_bad_cds():
#     '''
#     try deleting a non-existing CDS hostname, expect trouble
#     '''
#     status = RHUICLI.delete(CONNECTION, "cds", ["bar" + CDS_HOSTNAMES[0]], force=True)
#     nose.tools.ok_(not status, msg="unexpected deletion status: %s" % status)

def teardown():
    '''
    announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
