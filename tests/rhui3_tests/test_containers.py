'''Container Management Tests'''

from __future__ import print_function

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
from stitches.expect import Expect, ExpectFailed
import yaml

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.helpers import Helpers
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.rhuimanager_sync import RHUIManagerSync
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

RHUA = ConMgr.connect()
# To make this script communicate with a client machine different from cli01.example.com, run:
# export RHUICLI=hostname
# in your shell before running this script, replacing "hostname" with the actual client host name.
# This allows for multiple client machines in one stack.
CLI = ConMgr.connect(getenv("RHUICLI", ConMgr.get_cli_hostnames()[0]))

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

        self.container_quay = doc["container_alt"]["quay"]
        self.container_docker = doc["container_alt"]["docker"]

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
            RHUIManagerInstance.add_instance(RHUA, "cds")

    @staticmethod
    def test_03_add_hap():
        '''
            add an HAProxy Load-balancer
        '''
        if not getenv("RHUISKIPSETUP"):
            RHUIManagerInstance.add_instance(RHUA, "loadbalancers")

    def test_04_add_containers(self):
        '''
           add containers
        '''
        # first, add a container from RH
        # get credentials and enter them when prompted
        credentials = Helpers.get_credentials(RHUA)
        RHUIManagerRepo.add_container(RHUA,
                                      self.container_name,
                                      self.container_id,
                                      self.container_displayname,
                                      [""] + credentials)
        # second, add a container from Quay
        # get Quay credentials
        credentials = Helpers.get_credentials(RHUA, "quay")
        quay_url = Helpers.get_registry_url("quay")
        RHUIManagerRepo.add_container(RHUA,
                                      self.container_quay["name"],
                                      credentials=[quay_url] + credentials)
        # third, add a container from the Docker hub
        docker_url = Helpers.get_registry_url("docker")
        RHUIManagerRepo.add_container(RHUA,
                                      self.container_docker["name"],
                                      credentials=[docker_url])

    def test_05_display_info(self):
        '''
           check detailed information on the RH container
        '''
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [self.container_displayname,
                                                    "https://%s/pulp/docker/%s/" % \
                                                    (ConMgr.get_cds_lb_hostname(),
                                                     self.container_id)],
                                                   [False],
                                                   [True, None, True],
                                                   0)

    def test_06_sync_containers(self):
        '''
           sync the containers
        '''
        quay_repo_name = Util.safe_pulp_repo_name(self.container_quay["name"])
        docker_repo_name = Util.safe_pulp_repo_name(self.container_docker["name"])

        RHUIManagerSync.sync_repo(RHUA,
                                  [self.container_displayname,
                                   quay_repo_name,
                                   docker_repo_name])
        RHUIManagerSync.wait_till_repo_synced(RHUA,
                                              [self.container_displayname,
                                               quay_repo_name,
                                               docker_repo_name])

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
        for container in [self.container_id,
                          Util.safe_pulp_repo_name(self.container_quay["name"]),
                          Util.safe_pulp_repo_name(self.container_docker["name"])]:
            cmd = "docker pull %s" % container
            # in some cases the container is synced but pulling fails mysteriously
            # if that happens, try again in a minute
            try:
                Expect.expect_retval(CLI, cmd, timeout=30)
            except ExpectFailed:
                time.sleep(60)
                Expect.expect_retval(CLI, cmd, timeout=30)

    def test_10_check_images(self):
        '''
           check if the container images are now available
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)

        quay_repo_name = Util.safe_pulp_repo_name(self.container_quay["name"])
        docker_repo_name = Util.safe_pulp_repo_name(self.container_docker["name"])

        _, stdout, _ = CLI.exec_command("docker images")
        images = stdout.read().decode().splitlines()
        images_cli = [image.split()[0].split("/")[1] \
                     for image in images if image.startswith(ConMgr.get_cds_lb_hostname())]
        nose.tools.eq_(sorted(images_cli),
                       sorted([self.container_id, quay_repo_name, docker_repo_name]))

    def test_11_run_command(self):
        '''
           run a test command (uname) in the RH container
        '''
        if not self.cli_supported:
            raise nose.exc.SkipTest("Not supported on RHEL %s" % self.cli_os_version)
        Expect.ping_pong(CLI, "docker run %s uname" % self.container_id, "Linux")

    def test_99_cleanup(self):
        '''
           remove the containers from the client and the RHUA, uninstall HAProxy and CDS
        '''
        if self.cli_supported:
            Expect.expect_retval(CLI, "docker rm -f $(docker ps -a -f ancestor=%s -q)" % \
                                 self.container_id)
            for container in [self.container_id,
                              Util.safe_pulp_repo_name(self.container_quay["name"]),
                              Util.safe_pulp_repo_name(self.container_docker["name"])]:
                Expect.expect_retval(CLI, "docker rmi %s" % container)
            Util.remove_rpm(CLI, [CONF_RPM_NAME])
            Util.restart_if_present(CLI, "docker")
        Expect.expect_retval(RHUA, "rm -rf /tmp/%s*" % CONF_RPM_NAME)
        RHUIManagerRepo.delete_all_repos(RHUA)
        if not getenv("RHUISKIPSETUP"):
            RHUIManagerInstance.delete_all(RHUA, "loadbalancers")
            RHUIManagerInstance.delete_all(RHUA, "cds")

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
