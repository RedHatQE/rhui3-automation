'''Container Management Tests'''

# To skip the upload of an entitlement certificate and the registration of CDS and HAProxy nodes --
# because you want to save time in each client test case and do this beforehand -- run:
# export RHUISKIPSETUP=1
# in your shell before running this script.
# The cleanup will be skipped, too, so you ought to clean up eventually.

from os import getenv
from os.path import basename
import time

import logging
import nose
import stitches
from stitches.expect import Expect, ExpectFailed
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.rhuimanager_sync import RHUIManagerSync
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

RHUA = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
# To make this script communicate with a client machine different from cli01.example.com, run:
# export RHUICLI=hostname
# in your shell before running this script, replacing "hostname" with the actual client host name.
# This allows for multiple client machines in one stack.
CLI = stitches.Connection(getenv("RHUICLI", "cli01.example.com"), "root", "/root/.ssh/id_rsa_test")

CONF_RPM_NAME = "containers-rhui"
CONF_RPM_PATH = "/tmp/%s-1/build/RPMS/noarch/%s-1-1ui.noarch.rpm" % (CONF_RPM_NAME, CONF_RPM_NAME)

class TestClient(object):
    '''
       class for container tests
    '''

    def __init__(self):
        self.cli_os_version = Util.get_rhel_version(CLI)["major"]
        self.cli_supported = self.cli_os_version in [7, 8]

        arch = Util.get_arch(CLI)

        with open("/etc/rhui3_tests/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)

        try:
            self.container_name = doc["container_rhel7"][arch]["name"]
            self.container_id = doc["container_rhel7"][arch]["id"]
            self.container_displayname = doc["container_rhel7"][arch]["displayname"]
        except KeyError:
            raise nose.SkipTest("No test container defined for %s" % arch)

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_init():
        '''log in to RHUI'''
        if not getenv("RHUISKIPSETUP"):
            RHUIManager.initial_run(RHUA)

    @staticmethod
    def test_02_add_cds():
        '''
            add a CDS
        '''
        if not getenv("RHUISKIPSETUP"):
            RHUIManagerInstance.add_instance(RHUA, "cds", "cds01.example.com")

    @staticmethod
    def test_03_add_hap():
        '''
            add an HAProxy Load-balancer
        '''
        if not getenv("RHUISKIPSETUP"):
            RHUIManagerInstance.add_instance(RHUA, "loadbalancers", "hap01.example.com")

    def test_04_add_container(self):
        '''
           add a container
        '''
        RHUIManagerRepo.add_container(RHUA,
                                      self.container_name,
                                      self.container_id,
                                      self.container_displayname)

    def test_05_display_container(self):
        '''
           check detailed information on the container
        '''
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [self.container_displayname,
                                                    "https://cds.example.com/pulp/docker/%s/" % \
                                                    self.container_id],
                                                   [False],
                                                   [True, None, True],
                                                   0)

    def test_06_sync_container(self):
        '''
           sync the container
        '''
        RHUIManagerSync.sync_repo(RHUA, [self.container_displayname])
        RHUIManagerSync.wait_till_repo_synced(RHUA, [self.container_displayname])

    @staticmethod
    def test_07_create_cli_rpm():
        '''
           create a client configuration RPM
        '''
        RHUIManagerClient.create_container_conf_rpm(RHUA, "/tmp", CONF_RPM_NAME, "1", "1ui")
        Expect.expect_retval(RHUA, "test -f %s" % CONF_RPM_PATH)

    def test_08_install_cli_rpm(self):
        '''
           install the client configuration RPM
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Util.install_pkg_from_rhua(RHUA, CLI, CONF_RPM_PATH)
        # restart the docker service for the configuration to take effect
        # (only clients running the docker service)
        Util.restart_if_present(CLI, "docker")

    def test_09_pull_image(self):
        '''
           pull the container image
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        cmd = "docker pull %s" % self.container_id
        # in some cases the container is synced but pulling fails mysteriously
        # if that happens, try again in a minute
        try:
            Expect.expect_retval(CLI, cmd, timeout=30)
        except ExpectFailed:
            time.sleep(60)
            Expect.expect_retval(CLI, cmd, timeout=30)

    def test_10_check_image(self):
        '''
           check if the container image is now available
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Expect.ping_pong(CLI, "docker images", "cds.example.com:5000/%s" % self.container_id)

    def test_11_run_command(self):
        '''
           run a test command (uname) in the container
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Expect.ping_pong(CLI, "docker run %s uname" % self.container_id, "Linux")

    def test_99_cleanup(self):
        '''
           remove the container from the client and the RHUA, uninstall HAProxy and CDS
        '''
        if self.cli_supported:
            Expect.expect_retval(CLI, "docker rm -f $(docker ps -a -f ancestor=%s -q)" % \
                                 self.container_id)
            Expect.expect_retval(CLI, "docker rmi %s" % self.container_id)
            Util.remove_rpm(CLI, [CONF_RPM_NAME])
            Util.restart_if_present(CLI, "docker")
        Expect.expect_retval(RHUA, "rm -rf /tmp/%s*" % CONF_RPM_NAME)
        RHUIManagerRepo.delete_all_repos(RHUA)
        if not getenv("RHUISKIPSETUP"):
            RHUIManagerInstance.delete(RHUA, "loadbalancers", ["hap01.example.com"])
            RHUIManagerInstance.delete(RHUA, "cds", ["cds01.example.com"])

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
