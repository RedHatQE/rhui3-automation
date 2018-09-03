'''Docker Container Management Tests'''

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
CLI = stitches.Connection("cli01.example.com", "root", "/root/.ssh/id_rsa_test")

CONF_RPM_NAME = "docker-rhui"
CONF_RPM_PATH = "/tmp/%s-2.0/build/RPMS/noarch/%s-2.0-1.noarch.rpm" % (CONF_RPM_NAME, CONF_RPM_NAME)

class TestClient(object):
    '''
       class for Docker container tests
    '''

    def __init__(self):
        self.cli_os_version = Util.get_rhua_version(CLI)["major"]

        with open('/usr/share/rhui3_tests_lib/config/tested_repos.yaml', 'r') as configfile:
            doc = yaml.load(configfile)

        self.docker_container_name = doc['docker_container2']['name']
        self.docker_container_id = doc['docker_container2']['id']
        self.docker_container_displayname = doc['docker_container2']['displayname']

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_init():
        '''log in to rhui-manager'''
        RHUIManager.initial_run(RHUA)

    @staticmethod
    def test_02_add_cds():
        '''
            add a CDS
        '''
        RHUIManagerInstance.add_instance(RHUA, "cds", "cds01.example.com")

    @staticmethod
    def test_04_add_hap():
        '''
            add an HAProxy Load-balancer
        '''
        RHUIManagerInstance.add_instance(RHUA, "loadbalancers", "hap01.example.com")

    def test_05_add_container(self):
        '''
           add a Docker container
        '''
        RHUIManagerRepo.add_docker_container(RHUA,
                                             self.docker_container_name,
                                             self.docker_container_id,
                                             self.docker_container_displayname)

    def test_06_display_container(self):
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

    def test_07_sync_container(self):
        '''
           sync the Docker container
        '''
        RHUIManagerSync.sync_repo(RHUA, [self.docker_container_displayname])
        RHUIManagerSync.wait_till_repo_synced(RHUA, [self.docker_container_displayname])

    @staticmethod
    def test_08_create_docker_cli_rpm():
        '''
           create a Docker client configuration RPM
        '''
        RHUIManagerClient.create_docker_conf_rpm(RHUA,
                                                 "/tmp",
                                                 CONF_RPM_NAME)
        Expect.expect_retval(RHUA, "test -f %s" % CONF_RPM_PATH)

    def test_09_install_docker_cli_rpm(self):
        '''
           install the Docker client configuration RPM
        '''
        if self.cli_os_version < 7:
            raise nose.exc.SkipTest("Not supported on RHEL " + str(self.cli_os_version))
        Util.install_pkg_from_rhua(RHUA,
                                   CLI,
                                   CONF_RPM_PATH)

    def test_10_restart_docker_service(self):
        '''
           restart the Docker service for the configuration to take effect
        '''
        if self.cli_os_version < 7:
            raise nose.exc.SkipTest("Not supported on RHEL " + str(self.cli_os_version))
        Expect.expect_retval(CLI, "systemctl restart docker")

    def test_11_pull_image(self):
        '''
           pull the Docker container
        '''
        if self.cli_os_version < 7:
            raise nose.exc.SkipTest("Not supported on RHEL " + str(self.cli_os_version))
        Expect.expect_retval(CLI, "docker pull %s" % self.docker_container_id, timeout=30)

    def test_12_check_image(self):
        '''
           check if the container is now available
        '''
        if self.cli_os_version < 7:
            raise nose.exc.SkipTest("Not supported on RHEL " + str(self.cli_os_version))
        Expect.ping_pong(CLI, "docker images", "cds.example.com:5000/%s" % self.docker_container_id)

    def test_13_run_command(self):
        '''
           run a test command (uname) in the container
        '''
        if self.cli_os_version < 7:
            raise nose.exc.SkipTest("Not supported on RHEL " + str(self.cli_os_version))
        Expect.ping_pong(CLI, "docker run rhel7-minimal-from-rhui uname", "Linux")

    def test_99_cleanup(self):
        '''
           remove the container from RHUA and the client, restart docker, uninstall HAProxy and CDS
        '''
        if self.cli_os_version >= 7:
            Expect.expect_retval(CLI, "docker rm $(docker ps -a -f ancestor=%s -q)" % \
                                 self.docker_container_id)
            Expect.expect_retval(CLI, "docker rmi %s" % self.docker_container_id)
            Util.remove_rpm(CLI, [CONF_RPM_NAME])
            Expect.expect_retval(CLI, "systemctl restart docker")
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
