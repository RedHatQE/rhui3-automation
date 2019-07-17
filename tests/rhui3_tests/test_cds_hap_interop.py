"""CDS-HAProxy Interoperability Tests"""

from os.path import basename

import logging
import nose
import stitches
from stitches.expect import Expect

from rhui3_tests_lib.helpers import Helpers
from rhui3_tests_lib.rhui_cmd import RHUICLI
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

# check if (at least) two CDS nodes are actually available
CDS_HOSTNAMES = Util.get_cds_hostnames()
CDS2_EXISTS = len(CDS_HOSTNAMES) > 1

HA_HOSTNAME = "hap01.example.com"

RHUA = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
HAPROXY = stitches.Connection(HA_HOSTNAME, "root", "/root/.ssh/id_rsa_test")

def setup():
    """announce the beginning of the test run"""
    print("*** Running %s: *** " % basename(__file__))

def test_01_login_add_hap():
    """log in to RHUI, add an HAProxy Load-balancer"""
    RHUIManager.initial_run(RHUA)
    RHUIManagerInstance.add_instance(RHUA, "loadbalancers", HA_HOSTNAME)

def test_02_add_first_cds():
    """[TUI] add the first CDS"""
    RHUIManagerInstance.add_instance(RHUA, "cds", CDS_HOSTNAMES[0])

def test_03_check_haproxy_cfg():
    """check if the first CDS was added to the HAProxy configuration file"""
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_04_add_second_cds():
    """[TUI] add the second CDS"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    RHUIManagerInstance.add_instance(RHUA, "cds", CDS_HOSTNAMES[1])

def test_05_check_haproxy_cfg():
    """check if the second CDS was added to the HAProxy configuration file"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[1]))
    # also check if the first one is still there
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_06_delete_second_cds():
    """[TUI] delete the second CDS"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    RHUIManagerInstance.delete(RHUA, "cds", [CDS_HOSTNAMES[1]])

def test_07_check_haproxy_cfg():
    """check if the second CDS (and only it) was deleted from the HAProxy configuration file"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    nose.tools.ok_(not Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[1]))
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_08_delete_first_cds():
    """[TUI] delete the first CDS"""
    RHUIManagerInstance.delete(RHUA, "cds", [CDS_HOSTNAMES[0]])

def test_09_check_haproxy_cfg():
    """check if the first CDS was deleted from the HAProxy configuration file"""
    nose.tools.ok_(not Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_10_add_first_cds():
    """[CLI] add the first CDS"""
    RHUICLI.add(RHUA, "cds", CDS_HOSTNAMES[0], unsafe=True)

def test_11_check_haproxy_cfg():
    """check if the first CDS was added to the HAProxy configuration file"""
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_12_add_second_cds():
    """[CLI] add the second CDS"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    RHUICLI.add(RHUA, "cds", CDS_HOSTNAMES[1], unsafe=True)

def test_13_check_haproxy_cfg():
    """check if the second CDS was added to the HAProxy configuration file"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[1]))
    # also check if the first one is still there
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_14_delete_second_cds():
    """[CLI] delete the second CDS"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    RHUICLI.delete(RHUA, "cds", [CDS_HOSTNAMES[1]])

def test_15_check_haproxy_cfg():
    """check if the second CDS (and only it) was deleted from the HAProxy configuration file"""
    if not CDS2_EXISTS:
        raise nose.exc.SkipTest("The second CDS does not exist")
    nose.tools.ok_(not Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[1]))
    nose.tools.ok_(Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_16_delete_first_cds():
    """[CLI] delete the first CDS"""
    RHUICLI.delete(RHUA, "cds", [CDS_HOSTNAMES[0]], True)

def test_17_check_haproxy_cfg():
    """check if the first CDS was deleted from the HAProxy configuration file"""
    nose.tools.ok_(not Helpers.cds_in_haproxy_cfg(HAPROXY, CDS_HOSTNAMES[0]))

def test_99_cleanup():
    """delete the HAProxy Load-balancer"""
    RHUIManagerInstance.delete(RHUA, "loadbalancers", [HA_HOSTNAME])
    # also clean up the SSH keys (if left behind)
    Expect.expect_retval(RHUA, "if [ -f ~/.ssh/known_hosts ]; then ssh-keygen -R %s; fi" % \
                         CDS_HOSTNAMES[0])
    if CDS2_EXISTS:
        Expect.expect_retval(RHUA, "if [ -f ~/.ssh/known_hosts ]; then ssh-keygen -R %s; fi" % \
                             CDS_HOSTNAMES[1])

def teardown():
    """announce the end of the test run"""
    print("*** Finished running %s. *** " % basename(__file__))
