'''HAProxy management tests for the CLI'''

from os.path import basename

import logging
import nose
import stitches
from stitches.expect import Expect

from rhui3_tests_lib.helpers import Helpers
from rhui3_tests_lib.rhui_cmd import RHUICLI
from rhui3_tests_lib.rhuimanager import RHUIManager

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

HA_HOSTNAME = "hap01.example.com"

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

def test_02_list_hap():
    '''
    check if there are no HAProxy Load-balancers
    '''
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [])

def test_03_add_hap():
    '''
    add an HAProxy Load-balancer
    '''
    status = RHUICLI.add(CONNECTION, "haproxy", HA_HOSTNAME, unsafe=True)
    nose.tools.ok_(status, msg="unexpected installation status: %s" % status)

def test_04_list_hap():
    '''
    check if the HAProxy Load-balancer has been added
    '''
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [HA_HOSTNAME])

def test_05_reinstall_hap():
    '''
    add the HAProxy Load-balancer again by reinstalling it
    '''
    status = RHUICLI.reinstall(CONNECTION, "haproxy", HA_HOSTNAME)
    nose.tools.ok_(status, msg="unexpected reinstallation status: %s" % status)

def test_06_list_hap():
    '''
    check if the HAProxy Load-balancer is still tracked, and only once
    '''
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [HA_HOSTNAME])

def test_07_readd_hap_noforce():
    '''
    check if rhui refuses to add the HAProxy Load-balancer again if no extra parameter is used
    '''
    status = RHUICLI.add(CONNECTION, "haproxy", HA_HOSTNAME, unsafe=True)
    nose.tools.ok_(not status, msg="unexpected readdition status: %s" % status)

def test_08_list_hap():
    '''
    check if nothing extra has been added
    '''
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [HA_HOSTNAME])

def test_09_readd_hap():
    '''
    add the HAProxy Load-balancer again by using force
    '''
    status = RHUICLI.add(CONNECTION, "haproxy", HA_HOSTNAME, force=True, unsafe=True)
    nose.tools.ok_(status, msg="unexpected readdition status: %s" % status)

def test_10_list_hap():
    '''
    check if the HAProxy Load-balancer is still tracked, and only once
    '''
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [HA_HOSTNAME])

def test_11_delete_hap_noforce():
    '''
    check if rhui refuses to delete the node when it's the only/last one and force isn't used
    '''
    status = RHUICLI.delete(CONNECTION, "haproxy", [HA_HOSTNAME])
    nose.tools.ok_(not status, msg="unexpected deletion status: %s" % status)

def test_12_list_hap():
    '''
    check if the HAProxy Load-balancer really hasn't been deleted
    '''
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [HA_HOSTNAME])

def test_13_delete_hap_force():
    '''
    delete the HAProxy Load-balancer forcibly
    '''
    status = RHUICLI.delete(CONNECTION, "haproxy", [HA_HOSTNAME], force=True)
    nose.tools.ok_(status, msg="unexpected deletion status: %s" % status)

def test_14_list_hap():
    '''
    check if the HAProxy Load-balancer has been deleted
    '''
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [])

def test_15_add_bad_hap():
    '''
    try adding an incorrect HAProxy hostname, expect trouble and nothing added
    '''
    status = RHUICLI.add(CONNECTION, "haproxy", "foo" + HA_HOSTNAME)
    nose.tools.ok_(not status, msg="unexpected addition status: %s" % status)
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [])

# currently broken, see RHBZ#1409697
# def test_16_delete_bad_hap():
#     '''
#     try deleting a non-existing HAProxy hostname, expect trouble
#     '''
#     status = RHUICLI.delete(CONNECTION, "haproxy", ["bar" + HA_HOSTNAME], force=True)
#     nose.tools.ok_(not status, msg="unexpected deletion status: %s" % status)

def test_17_add_hap_changed_case():
    '''
    add and delete an HAProxy Load-balancer with uppercase characters, should work
    '''
    # for RHBZ#1572623
    hap_up = HA_HOSTNAME.replace("hap", "HAP")
    status = RHUICLI.add(CONNECTION, "haproxy", hap_up, unsafe=True)
    nose.tools.ok_(status, msg="unexpected %s addition status: %s" % (hap_up, status))
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [hap_up])
    status = RHUICLI.delete(CONNECTION, "haproxy", [hap_up], force=True)
    nose.tools.ok_(status, msg="unexpected deletion status: %s" % status)

def test_18_add_safe_unknown_key():
    '''
    try adding the Load-balancer when its SSH key is unknown, without using --unsafe; should fail
    '''
    # for RHBZ#1409460
    # make sure its key is unknown
    Expect.expect_retval(CONNECTION,
                         "if [ -f ~/.ssh/known_hosts ]; then ssh-keygen -R %s; fi" % HA_HOSTNAME)
    # try adding the Load-balancer
    status = RHUICLI.add(CONNECTION, "haproxy", HA_HOSTNAME)
    nose.tools.ok_(not status, msg="unexpected addition status: %s" % status)
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [])

def test_19_add_safe_known_key():
    '''
    add and delete the Load-balancer when its SSH key is known, without using --unsafe; should work
    '''
    # for RHBZ#1409460
    # accept the host's SSH key
    Expect.expect_retval(CONNECTION, "ssh-keyscan -t rsa %s >>/root/.ssh/known_hosts" % HA_HOSTNAME)
    # actually add and delete the host
    status = RHUICLI.add(CONNECTION, "haproxy", HA_HOSTNAME)
    nose.tools.ok_(status, msg="unexpected addition status: %s" % status)
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [HA_HOSTNAME])
    status = RHUICLI.delete(CONNECTION, "haproxy", [HA_HOSTNAME], force=True)
    nose.tools.ok_(status, msg="unexpected deletion status: %s" % status)
    # clean up the SSH key
    Expect.expect_retval(CONNECTION, "ssh-keygen -R %s" % HA_HOSTNAME)

def test_20_delete_unreachable():
    '''
    add a Load-balancer, make it unreachable, and see if it can still be deleted from the RHUA
    '''
    # for RHBZ#1639996
    status = RHUICLI.add(CONNECTION, "haproxy", HA_HOSTNAME, unsafe=True)
    nose.tools.ok_(status, msg="unexpected installation status: %s" % status)
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [HA_HOSTNAME])

    Helpers.break_hostname(CONNECTION, HA_HOSTNAME)

    # delete it
    status = RHUICLI.delete(CONNECTION, "haproxy", [HA_HOSTNAME], force=True)
    nose.tools.ok_(status, msg="unexpected deletion status: %s" % status)
    # check it
    hap_list = RHUICLI.list(CONNECTION, "haproxy")
    nose.tools.eq_(hap_list, [])

    Helpers.unbreak_hostname(CONNECTION)

    # the node remains configured (haproxy)... unconfigure it properly
    # not possible until RHBZ#1640002 is fixed
    # clean up the SSH key
    Expect.expect_retval(CONNECTION, "ssh-keygen -R %s" % HA_HOSTNAME)

def teardown():
    '''
    announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
