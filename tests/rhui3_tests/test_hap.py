'''HAProxy management tests'''

from os.path import basename

import logging
import nose
import stitches

from rhui3_tests_lib.helpers import Helpers
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance, NoSuchInstance

logging.basicConfig(level=logging.DEBUG)

HA_HOSTNAME = "hap01.example.com"

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
HAPROXY = stitches.Connection(HA_HOSTNAME, "root", "/root/.ssh/id_rsa_test")

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
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", HA_HOSTNAME)

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
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", HA_HOSTNAME, update=True)

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
    RHUIManagerInstance.delete(CONNECTION, "loadbalancers", [HA_HOSTNAME])

def test_09_list_hap():
    '''
        list HAProxy Load-balancers again, expect none
    '''
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])

def test_10_check_cleanup():
    '''
        check if the haproxy service was stopped
    '''
    nose.tools.ok_(not Helpers.check_service(HAPROXY, "haproxy"),
                   msg="haproxy is still running on %s" % HA_HOSTNAME)

def test_11_add_hap_uppercase():
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

def test_12_delete_unreachable():
    '''
    add a Load-balancer, make it unreachable, and see if it can still be deleted from the RHUA
    '''
    # for RHBZ#1639996
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", HA_HOSTNAME)
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_not_equal(hap_list, [])

    Helpers.break_hostname(CONNECTION, HA_HOSTNAME)

    # delete it
    RHUIManagerInstance.delete(CONNECTION, "loadbalancers", [HA_HOSTNAME])
    # check it
    hap_list = RHUIManagerInstance.list(CONNECTION, "loadbalancers")
    nose.tools.assert_equal(hap_list, [])

    Helpers.unbreak_hostname(CONNECTION)

    # the node remains configured (haproxy)... unconfigure it properly
    RHUIManagerInstance.add_instance(CONNECTION, "loadbalancers", HA_HOSTNAME)
    RHUIManagerInstance.delete(CONNECTION, "loadbalancers", [HA_HOSTNAME])

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
