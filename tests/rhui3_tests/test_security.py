"""Various Security Tests"""

from __future__ import print_function

import csv
import logging
from os.path import basename
import subprocess

import nose

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance

logging.basicConfig(level=logging.DEBUG)

HOSTNAMES = {"RHUA": ConMgr.get_rhua_hostname(),
             "CDS": ConMgr.get_cds_hostnames(),
             "HAProxy": ConMgr.get_haproxy_hostnames()}
PORTS = {"puppet": 8140,
         "https": 443,
         "crane": 5000}
PROTOCOL_TEST_CMD = "echo | openssl s_client -%s -connect %s:%s; echo $?"
# these are in fact the s_client options for protocols, just without the dash
PROTOCOLS = {"good": ["tls1_2"],
             "bad": ["ssl3", "tls1", "tls1_1"]}
RESULTS = {"good": "Secure Renegotiation IS supported",
           "bad": "Secure Renegotiation IS NOT supported"}

# connections to the RHUA and the HAProxy nodes
RHUA = ConMgr.connect()
HAPROXIES = [ConMgr.connect(host) for host in HOSTNAMES["HAProxy"]]

def _check_protocols(hostname, port):
    """helper method to try various protocols on hostname:port"""
    # check allowed protocols
    for protocol in PROTOCOLS["good"]:
        raw_output = subprocess.check_output(PROTOCOL_TEST_CMD % (protocol, hostname, port),
                                             shell=True,
                                             stderr=subprocess.STDOUT)
        output_lines = raw_output.decode().splitlines()
        # check for the line that indicates a good result
        nose.tools.ok_(RESULTS["good"] in output_lines,
                       msg="s_client didn't print '%s' when using %s with %s:%s" % \
                       (RESULTS["good"], protocol, hostname, port))
        # also check the exit status (the last line), should be 0 to indicate success
        nose.tools.eq_(int(output_lines[-1]), 0)
    # check disallowed protocols
    for protocol in PROTOCOLS["bad"]:
        raw_output = subprocess.check_output(PROTOCOL_TEST_CMD % (protocol, hostname, port),
                                             shell=True,
                                             stderr=subprocess.STDOUT)
        output_lines = raw_output.decode().splitlines()
        # check for the line that indicates a bad result
        nose.tools.ok_(RESULTS["bad"] in output_lines,
                       msg="s_client didn't print '%s' when using %s with %s:%s" % \
                       (RESULTS["bad"], protocol, hostname, port))
        # also check the exit status (the last line), should be 1 to indicate a failure
        nose.tools.eq_(int(output_lines[-1]), 1)

def setup():
    """announce the beginning of the test run"""
    print("*** Running %s: *** " % basename(__file__))

def test_01_login_add_cds_hap():
    """log in to RHUI, add CDS and HAProxy nodes"""
    RHUIManager.initial_run(RHUA)
    for cds in HOSTNAMES["CDS"]:
        RHUIManagerInstance.add_instance(RHUA, "cds", cds)
    for haproxy in HOSTNAMES["HAProxy"]:
        RHUIManagerInstance.add_instance(RHUA, "loadbalancers", haproxy)

def test_02_puppet():
    """check protocols allowed by Puppet on the RHUA"""
    # for RHBZ#1637261
    _check_protocols(HOSTNAMES["RHUA"], PORTS["puppet"])

def test_03_https_rhua():
    """check protocols allowed by Apache on the RHUA"""
    # for RHBZ#1637261
    _check_protocols(HOSTNAMES["RHUA"], PORTS["https"])

def test_04_https_cds():
    """check protocols allowed by Apache on the CDS nodes"""
    # for RHBZ#1637261
    for cds in HOSTNAMES["CDS"]:
        _check_protocols(cds, PORTS["https"])

def test_05_crane_cds():
    """check protocols allowed by Crane on the CDS nodes"""
    # for RHBZ#1637261
    for cds in HOSTNAMES["CDS"]:
        _check_protocols(cds, PORTS["crane"])

def test_06_haproxy_stats():
    """check haproxy stats"""
    # for RHBZ#1718066
    for haproxy in HAPROXIES:
        _, stdout, _ = haproxy.exec_command("echo 'show stat' | nc -U /var/lib/haproxy/stats")
        stats = list(csv.DictReader(stdout))
        cranestats = {row["svname"]: row["status"] for row in stats if row["# pxname"] == "crane00"}
        httpsstats = {row["svname"]: row["status"] for row in stats if row["# pxname"] == "https00"}
        # check the stats for the frontend, the CDS nodes, and the backend; crane & https
        nose.tools.eq_(cranestats["FRONTEND"], "OPEN")
        nose.tools.eq_(cranestats["BACKEND"], "UP")
        for cds in HOSTNAMES["CDS"]:
            nose.tools.eq_(cranestats[cds], "UP")
        nose.tools.eq_(httpsstats["FRONTEND"], "OPEN")
        nose.tools.eq_(httpsstats["BACKEND"], "UP")
        for cds in HOSTNAMES["CDS"]:
            nose.tools.eq_(httpsstats[cds], "UP")

def test_99_cleanup():
    """delete CDS and HAProxy nodes"""
    RHUIManagerInstance.delete_all(RHUA, "loadbalancers")
    RHUIManagerInstance.delete_all(RHUA, "cds")

def teardown():
    """announce the end of the test run"""
    print("*** Finished running %s. *** " % basename(__file__))
