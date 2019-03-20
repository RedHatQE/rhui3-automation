'''Update Info Tests'''

# To skip the upload of an entitlement certificate and the registration of CDS and HAProxy nodes --
# because you want to save time in each client test case and do this beforehand -- run:
# export RHUISKIPSETUP=1
# in your shell before running this script.
# The cleanup will be skipped, too, so you ought to clean up eventually.

from os import getenv
from os.path import basename

import logging
import nose
import stitches
from stitches.expect import Expect
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
from rhui3_tests_lib.rhuimanager_cmdline import RHUIManagerCLI
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

RHUA = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
# To make this script communicate with a client machine different from cli01.example.com, run:
# export RHUICLI=hostname
# in your shell before running this script, replacing "hostname" with the actual client host name.
# This allows for multiple client machines in one stack.
CLI = stitches.Connection(getenv("RHUICLI", "cli01.example.com"), "root", "/root/.ssh/id_rsa_test")

class TestClient(object):
    '''
       class for client tests
    '''

    def __init__(self):
        self.arch = Util.get_arch(CLI)
        self.version = Util.get_rhel_version(CLI)["major"]
        with open("/usr/share/rhui3_tests_lib/config/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)
            try:
                self.test = doc["updateinfo"][self.version][self.arch]
            except KeyError:
                raise nose.SkipTest("No test repo defined for RHEL %s on %s" % \
                                    (self.version, self.arch))

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_repo_setup():
        '''
           log in to RHUI
        '''
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

    def test_04_add_repo(self):
        '''
           add a custom repo
        '''
        # custom GPG key can have a name, or it can be set to "nokey" (not used with the packages),
        # or it can be undefined altogether, in which case the packages are supposedly signed by RH
        try:
            if self.test["gpg_key"] == "nokey":
                custom_gpg = None
            else:
                custom_gpg = "/tmp/extra_rhui_files/%s/%s" % \
                             (self.test["repo_id"], self.test["gpg_key"])
            redhat_gpg = "n"
        except KeyError:
            custom_gpg = None
            redhat_gpg = "y"
        RHUIManagerRepo.add_custom_repo(RHUA,
                                        self.test["repo_id"],
                                        self.test["repo_name"],
                                        redhat_gpg=redhat_gpg,
                                        custom_gpg=custom_gpg)

    def test_05_upload_packages(self):
        '''
           upload packages to the custom repo
        '''
        RHUIManagerRepo.upload_content(RHUA,
                                       [self.test["repo_name"]],
                                       "/tmp/extra_rhui_files/%s" % self.test["repo_id"])

    def test_06_import_updateinfo(self):
        '''
           import update info
        '''
        # only doable in the CLI
        RHUIManagerCLI.repo_add_errata(RHUA,
                                       self.test["repo_id"],
                                       "/tmp/extra_rhui_files/%s/updateinfo.xml.gz" % \
                                       self.test["repo_id"])

    def test_07_generate_ent_cert(self):
        '''
           generate an entitlement certificate
        '''
        RHUIManagerClient.generate_ent_cert(RHUA,
                                            [self.test["repo_name"]],
                                            self.test["repo_id"],
                                            "/tmp")

    def test_08_create_cli_rpm(self):
        '''
           create a client configuration RPM from the entitlement certificate
        '''
        RHUIManagerClient.create_conf_rpm(RHUA,
                                          "/tmp",
                                          "/tmp/%s.crt" % self.test["repo_id"],
                                          "/tmp/%s.key" % self.test["repo_id"],
                                          self.test["repo_id"])

    def test_09_install_conf_rpm(self):
        '''
           install the client configuration RPM
        '''
        # remove Amazon RHUI config first, if needed
        Util.remove_amazon_rhui_conf_rpm(CLI)
        Util.install_pkg_from_rhua(RHUA,
                                   CLI,
                                   "/tmp/%s-2.0/build/RPMS/noarch/%s-2.0-1.noarch.rpm" % \
                                   (self.test["repo_id"], self.test["repo_id"]))

    def test_10_install_test_rpm(self):
        '''
           install an old version of an RPM from the repo
        '''
        nvr = "%s-%s" % (self.test["test_package"], self.test["old_version"])
        Expect.expect_retval(CLI, "yum -y install %s" % nvr, timeout=60)

    def test_11_check_updateinfo(self):
        '''
           check if the expected update info is found
        '''
        # yum should print Update ID : RHXA-YYYY:NNNNN
        # dnf should print Update ID: RHXA-YYYY:NNNNN
        Expect.ping_pong(CLI,
                         "yum updateinfo info",
                         "Update ID ?: %s" % self.test["errata"])

    def test_12_compare_n_of_updates(self):
        '''
           check if the all the updates from the original updateinfo file are available from RHUI
        '''
        errata_pattern = "RH.A-[0-9]*:[0-9]*"
        if self.version <= 7:
            cache = "/var/cache/yum/%s/%sServer/rhui-custom-%s" % \
                    (self.arch, self.version, self.test["repo_id"])
        else:
            cache = "/var/cache/dnf/rhui-custom-%s*/repodata" % self.test["repo_id"]

        _, stdout, _ = RHUA.exec_command("zgrep -o '%s' " % errata_pattern +
                                         "/tmp/extra_rhui_files/%s/updateinfo.xml.gz " % \
                                         self.test["repo_id"] +
                                         "| sort -u")
        with stdout as output:
            orig_errata = output.read().decode().splitlines()

        _, stdout, _ = CLI.exec_command("zgrep -o '%s' " % errata_pattern +
                                        "%s/*updateinfo.xml.gz " % \
                                        cache +
                                        "| sort -u")
        with stdout as output:
            processed_errata = output.read().decode().splitlines()
        nose.tools.eq_(orig_errata, processed_errata)

    def test_99_cleanup(self):
        '''
           remove the repo, uninstall hap, cds, cli rpm artefacts; remove rpms from cli
        '''
        Util.remove_rpm(CLI, [self.test["test_package"], self.test["repo_id"]])
        # the errata must be removed in the DB directly:
        Expect.expect_retval(RHUA, "mongo pulp_database --eval 'db.units_erratum.remove({})'")
        RHUIManagerRepo.delete_all_repos(RHUA)
        Expect.expect_retval(RHUA, "rm -rf /tmp/%s*" % self.test["repo_id"])
        if not getenv("RHUISKIPSETUP"):
            RHUIManagerInstance.delete(RHUA, "loadbalancers", ["hap01.example.com"])
            RHUIManagerInstance.delete(RHUA, "cds", ["cds01.example.com"])

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
