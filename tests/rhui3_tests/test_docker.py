'''Docker Container Management Tests'''

from os import getenv
from os.path import basename

import logging
import nose
import stitches
from stitches.expect import Expect
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

CONF_RPM_NAME = "docker-rhui"
CONF_RPM_PATH = "/tmp/%s-2.0/build/RPMS/noarch/%s-2.0-1.noarch.rpm" % (CONF_RPM_NAME, CONF_RPM_NAME)

class TestClient(object):
    '''
       class for Docker container tests
    '''

    def __init__(self):
        self.cli_os_version = Util.get_rhel_version(CLI)["major"]
        self.cli_supported = self.cli_os_version in [7, 8]

        arch = Util.get_arch(CLI)

        with open("/usr/share/rhui3_tests_lib/config/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)

        try:
            self.docker_container_name = doc["docker_container_rhel7"][arch]["name"]
            self.docker_container_id = doc["docker_container_rhel7"][arch]["id"]
            self.docker_container_displayname = doc["docker_container_rhel7"][arch]["displayname"]
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
        RHUIManager.initial_run(RHUA)

    @staticmethod
    def test_02_add_cds():
        '''
            add a CDS
        '''
        RHUIManagerInstance.add_instance(RHUA, "cds", "cds01.example.com")

    @staticmethod
    def test_03_add_hap():
        '''
            add an HAProxy Load-balancer
        '''
        RHUIManagerInstance.add_instance(RHUA, "loadbalancers", "hap01.example.com")

    def test_04_add_container(self):
        '''
           add a Docker container
        '''
        RHUIManagerRepo.add_docker_container(RHUA,
                                             self.docker_container_name,
                                             self.docker_container_id,
                                             self.docker_container_displayname)

    def test_05_display_container(self):
        '''
           check detailed information on the Docker container
        '''
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [self.docker_container_displayname,
                                                    "https://cds.example.com/pulp/docker/%s/" % \
                                                    self.docker_container_id],
                                                   [False],
                                                   [True, None, True],
                                                   0)

    def test_06_sync_container(self):
        '''
           sync the Docker container
        '''
        RHUIManagerSync.sync_repo(RHUA, [self.docker_container_displayname])
        RHUIManagerSync.wait_till_repo_synced(RHUA, [self.docker_container_displayname])

    @staticmethod
    def test_07_create_docker_cli_rpm():
        '''
           create a Docker client configuration RPM
        '''
        RHUIManagerClient.create_docker_conf_rpm(RHUA, "/tmp", CONF_RPM_NAME)
        Expect.expect_retval(RHUA, "test -f %s" % CONF_RPM_PATH)

    def test_08_install_docker_cli_rpm(self):
        '''
           install the Docker client configuration RPM
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Util.install_pkg_from_rhua(RHUA, CLI, CONF_RPM_PATH)
        # restart the Docker service for the configuration to take effect
        # (systemd-based Docker clients only)
        Util.restart_if_present(CLI, "docker")

    def test_09_pull_image(self):
        '''
           pull the Docker container
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Expect.expect_retval(CLI, "docker pull %s" % self.docker_container_id, timeout=30)

    def test_10_check_image(self):
        '''
           check if the container is now available
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Expect.ping_pong(CLI, "docker images", "cds.example.com:5000/%s" % self.docker_container_id)

    def test_11_run_command(self):
        '''
           run a test command (uname) in the container
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Expect.ping_pong(CLI, "docker run %s uname" % self.docker_container_id, "Linux")

    def test_99_cleanup(self):
        '''
           remove the container from the client and the RHUA, uninstall HAProxy and CDS
        '''
        if self.cli_supported:
            Expect.expect_retval(CLI, "docker rm $(docker ps -a -f ancestor=%s -q)" % \
                                 self.docker_container_id)
            Expect.expect_retval(CLI, "docker rmi %s" % self.docker_container_id)
            Util.remove_rpm(CLI, [CONF_RPM_NAME])
            Util.restart_if_present(CLI, "docker")
        Expect.expect_retval(RHUA, "rm -rf /tmp/%s*" % CONF_RPM_NAME)
        RHUIManagerRepo.delete_all_repos(RHUA)
        RHUIManagerInstance.delete(RHUA, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(RHUA, "cds", ["cds01.example.com"])

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
