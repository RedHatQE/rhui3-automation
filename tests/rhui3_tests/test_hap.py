'''HAProxy management tests'''

from os.path import basename

import logging
import nose
import stitches
from stitches.expect import Expect

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance, NoSuchInstance

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_initial_run():
    '''
        log in to RHUI
    '''
    RHUIManager.initial_run(CONNECTION)

def test_02_list_empty_hap():
    '''
        check if there are no HAProxy Load-balancers
    '''
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])

def test_03_add_hap():
    '''
        add an HAProxy Load-balancer
    '''
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", "hap01.example.com")

def test_04_list_hap():
    '''
        check if the HAProxy Load-balancer was added
    '''
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_not_equal(hap_list, [])

def test_05_readd_hap():
    '''
        add the HAProxy Load-balancer again (reapply the configuration)
    '''
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", "hap01.example.com", update=True)

def test_06_list_hap():
    '''
        check if the HAProxy Load-balancer is still tracked
    '''
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_not_equal(hap_list, [])

def test_07_delete_nonexisting_hap():
    '''
        try deleting an untracked HAProxy Load-balancer, should be rejected (by rhui3_tests_lib)
    '''
    nose.tools.assert_raises(NoSuchInstance,
                             RHUIManagerInstance.delete,
                             CONNECTION,
                             "loadbalancers",
                             ["hapfoo.example.com"])

def test_08_delete_hap():
    '''
        delete the HAProxy Load-balancer
    '''
    RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["hap01.example.com"])

def test_09_list_hap():
    '''
        list HAProxy Load-balancers again, expect none
    '''
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])

def test_10_add_hap_uppercase():
    '''
        add (and delete) an HAProxy Load-balancer with uppercase characters
    '''
    # for RHBZ#1572623
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", "HAP01.example.com")
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_not_equal(hap_list, [])
    RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["HAP01.example.com"])
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])

def test_11_delete_unreachable():
    '''
    add a Load-balancer, make it unreachable, and see if it can still be deleted from the RHUA
    '''
    # for RHBZ#1639996
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", "hap01.example.com")
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_not_equal(hap_list, [])
    # make it unreachable by setting its IP address to some nonsense and also stopping bind
    tweak_hosts_cmd = r"sed -i.bak 's/^[^ ]*\(.*hap01.example.com\)$/256.0.0.0\1/' /etc/hosts"
    Expect.expect_retval(CONNECTION, tweak_hosts_cmd)
    Expect.expect_retval(CONNECTION, "service named stop")
    # delete it
    RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["hap01.example.com"])
    # check it
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])
    # undo the DNS changes
    Expect.expect_retval(CONNECTION, "mv -f /etc/hosts.bak /etc/hosts")
    Expect.expect_retval(CONNECTION, "service named start")
    # the node remains configured (haproxy)... unconfigure it properly
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", "hap01.example.com")
    RHUIManagerInstance.delete(CONNECTION, "loadbalancers", ["hap01.example.com"])

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
