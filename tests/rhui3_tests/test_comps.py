"""Comps XML (Yum Package Groups) Tests"""

from __future__ import print_function

# To skip the registration of CDS and HAProxy nodes --
# because you want to save time in each client test case and do this beforehand -- run:
# export RHUISKIPSETUP=1
# in your shell before running this script.
# The cleanup will be skipped, too, so you ought to clean up eventually.

from os import getenv
from os.path import basename

from bisect import insort
import logging
import nose
from stitches.expect import Expect, ExpectFailed
import yaml

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.rhui_cmd import RHUICLI
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_cmdline import RHUIManagerCLI
from rhui3_tests_lib.rhuimanager_sync import RHUIManagerSync
from rhui3_tests_lib.util import Util
from rhui3_tests_lib.yummy import Yummy

logging.basicConfig(level=logging.DEBUG)

RHUA = ConMgr.connect()
# To make this script communicate with a client machine different from cli01.example.com, run:
# export RHUICLI=hostname
# in your shell before running this script, replacing "hostname" with the actual client host name.
# This allows for multiple client machines in one stack.
CLI = ConMgr.connect(getenv("RHUICLI", ConMgr.get_cli_hostnames()[0]))

BIG_REPO = "rhel-7-server-rhui-rpms"
EMP_REPO = "rhel-7-server-rhui-rh-common-rpms"
ZIP_REPO = "rhel-7-server-rhui-optional-rpms"

class TestCompsXML(object):
    """class to test comps XML handling"""
    def __init__(self):
        with open("/etc/rhui3_tests/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)
            self.test_repos = list(doc["comps"].keys())
            self.test_repo_names = [doc["comps"][repo]["name"] for repo in self.test_repos]
            self.test_groups = [doc["comps"][repo]["test_group"] for repo in self.test_repos]
            self.test_packages = [doc["comps"][repo]["test_package"] for repo in self.test_repos]
            self.test_langpacks = [doc["comps"][repo]["test_langpack"] for repo in self.test_repos]
            self.repo_with_mod_groups = [repo for repo in doc["comps"] \
                                         if "test_group_mod" in doc["comps"][repo].keys()][0]
            self.test_group_mod = doc["comps"][self.repo_with_mod_groups]["test_group_mod"]

    @staticmethod
    def setup_class():
        """announce the beginning of the test run"""
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_setup():
        """log in to RHUI, ensure CDS & HAProxy nodes have been added"""
        if not getenv("RHUISKIPSETUP"):
            RHUIManager.initial_run(RHUA)
            RHUICLI.add(RHUA, "cds", unsafe=True)
            RHUICLI.add(RHUA, "haproxy", unsafe=True)
        # check that
        cds_list = RHUICLI.list(RHUA, "cds")
        nose.tools.ok_(cds_list)
        hap_list = RHUICLI.list(RHUA, "haproxy")
        nose.tools.ok_(hap_list)
        # if running RHEL Beta, temporarily restore the non-Beta repos,
        # potentially disabled by choose_repo.py
        cmd = "if grep -q Beta /etc/redhat-release; then " \
              "cp /etc/yum.repos.d/redhat-rhui.repo{.disabled,}; " \
              "yum-config-manager --enable %s %s; fi" % (BIG_REPO, EMP_REPO)
        Expect.expect_retval(RHUA, cmd)

    def test_02_add_repos(self):
        """create custom repos for testing"""
        for repo_id, repo_name in zip(self.test_repos, self.test_repo_names):
            RHUIManagerCLI.repo_create_custom(RHUA,
                                              repo_id,
                                              display_name=repo_name,
                                              protected=True)

    def test_03_add_comps(self):
        """import comps XML files to the repos"""
        for repo in self.test_repos:
            RHUIManagerCLI.repo_add_comps(RHUA, repo, "/tmp/extra_rhui_files/%s/comps.xml" % repo)

    def test_04_create_cli_config_rpms(self):
        """create client configuration RPMs for the repos"""
        for repo in self.test_repos:
            RHUIManagerCLI.client_rpm(RHUA, [repo], [repo], "/tmp")

    def test_05_install_conf_rpm(self):
        """install the 1st client configuration RPM on the client"""
        # get rid of undesired repos first
        Util.remove_amazon_rhui_conf_rpm(CLI)
        Util.disable_beta_repos(CLI)
        Util.install_pkg_from_rhua(RHUA,
                                   CLI,
                                   "/tmp/%s-2.0/build/RPMS/noarch/%s-2.0-1.noarch.rpm" % \
                                   (self.test_repos[0], self.test_repos[0]))

    def test_06_check_groups(self):
        """compare client's available groups with the 1st original comps file, check a test group"""
        groups_on_client = Yummy.yum_grouplist(CLI)
        original_comps_xml = "/tmp/extra_rhui_files/%s/comps.xml" % self.test_repos[0]
        groups_in_xml = Yummy.comps_xml_grouplist(RHUA, original_comps_xml)
        nose.tools.eq_(groups_on_client, groups_in_xml)
        nose.tools.ok_(self.test_groups[0] in groups_on_client)

    def test_07_check_test_package(self):
        """check if the client can see the 1st test package as available in group information"""
        packages = Yummy.yum_group_packages(CLI, self.test_groups[0])
        nose.tools.ok_(self.test_packages[0] in packages,
                       msg="%s not found in %s" % (self.test_packages[0], packages))

    def test_08_install_conf_rpm(self):
        """replace the 1st client configuration RPM with the 2nd one on the client"""
        # get rid of the first one before installing the second one
        Util.remove_rpm(CLI, [self.test_repos[0]])
        Util.install_pkg_from_rhua(RHUA,
                                   CLI,
                                   "/tmp/%s-2.0/build/RPMS/noarch/%s-2.0-1.noarch.rpm" % \
                                   (self.test_repos[1], self.test_repos[1]))

    def test_09_check_groups(self):
        """compare client's available groups with the 2nd original comps file, check a test group"""
        groups_on_client = Yummy.yum_grouplist(CLI)
        original_comps_xml = "/tmp/extra_rhui_files/%s/comps.xml" % self.test_repos[1]
        groups_in_xml = Yummy.comps_xml_grouplist(RHUA, original_comps_xml)
        nose.tools.eq_(groups_on_client, groups_in_xml)
        nose.tools.ok_(self.test_groups[1] in groups_on_client)

    def test_10_check_test_package(self):
        """check if the client can see the 2nd test package as available in group information"""
        packages = Yummy.yum_group_packages(CLI, self.test_groups[1])
        nose.tools.ok_(self.test_packages[1] in packages,
                       msg="%s not found in %s" % (self.test_packages[1], packages))

    def test_11_check_langpacks(self):
        """check available langpacks in the processed comps files"""
        for repo, langpack in zip(self.test_repos, self.test_langpacks):
            langpacks = Yummy.comps_xml_langpacks(RHUA,
                                                  Yummy.repodata_location(RHUA,
                                                                          repo,
                                                                          "group"))
            if not langpacks:
                nose.tools.ok_(not langpack,
                               msg="a test langpack is defined, " +
                               "but there are no langpacks for %s" % repo)
            else:
                nose.tools.ok_(tuple(langpack.split()) in langpacks,
                               msg="%s not found in %s" % (langpack.split()[0], langpacks))

    def test_12_additional_group(self):
        """import a comps file containing one more group and expect the group to be added"""
        # and nothing lost...
        # import the "updated" comps file
        repo = self.repo_with_mod_groups
        modified_comps_xml = "/tmp/extra_rhui_files/%s/mod-comps.xml" % repo
        RHUIManagerCLI.repo_add_comps(RHUA, repo, modified_comps_xml)
        # create a client configuration RPM, install it on the client
        RHUIManagerCLI.client_rpm(RHUA, [repo], [repo, "2.1"], "/tmp")
        Util.remove_rpm(CLI, [self.test_repos[1]])
        Util.install_pkg_from_rhua(RHUA,
                                   CLI,
                                   "/tmp/%s-2.1/build/RPMS/noarch/%s-2.1-1.noarch.rpm" % \
                                   (repo, repo))
        # compare client's available groups with the *original* comps file,
        # expecting all the original groups plus the extra group
        groups_on_client = Yummy.yum_grouplist(CLI)
        original_comps_xml = "/tmp/extra_rhui_files/%s/comps.xml" % repo
        groups_in_xml = Yummy.comps_xml_grouplist(RHUA, original_comps_xml)
        # trick: put the extra group to the right place in the sorted list
        insort(groups_in_xml, self.test_group_mod)
        nose.tools.eq_(groups_on_client, groups_in_xml)
        nose.tools.ok_(self.test_group_mod in groups_on_client)

    @staticmethod
    def test_13_big_comps():
        """import comps for the (big) RHEL 7Server repo and check if all its groups get processed"""
        # first force the RHUA to cache RHEL repodata
        # (using a recent 3.x AWS client RPM; remove this when such an RPM is common in RHEL 7 AMIs)
        Expect.expect_retval(RHUA, "yum -y update rh-amazon-rhui-client", timeout=60)
        Expect.expect_retval(RHUA, "yum repolist enabled", timeout=60)
        # get all groups from this repodata; using a wildcard as there's only one cached comps file
        original_comps_xml = "/var/cache/yum/x86_64/7Server/%s/*comps.xml" % BIG_REPO
        original_groups = Yummy.comps_xml_grouplist(RHUA, original_comps_xml, False)
        # create a custom repo for the 7Server repo, import the cached comps file
        RHUIManagerCLI.repo_create_custom(RHUA, BIG_REPO)
        RHUIManagerCLI.repo_add_comps(RHUA, BIG_REPO, original_comps_xml)
        # this can actually take a while to get fully processed, so better check for Pulp tasks
        RHUIManagerSync.wait_till_pulp_tasks_finish(RHUA)
        # get all groups from the imported metadata
        processed_comps_xml = Yummy.repodata_location(RHUA, BIG_REPO, "group")
        processed_groups = Yummy.comps_xml_grouplist(RHUA, processed_comps_xml, False)
        # compare the groups
        nose.tools.eq_(original_groups, processed_groups)

    @staticmethod
    def test_14_empty_comps():
        """import a comps file containing no group and expect no problem and no repodata refresh"""
        # use the cached comps file for RH-Common, which is known to be empty
        original_comps_xml = "/var/cache/yum/x86_64/7Server/%s/*comps.xml" % EMP_REPO
        # re-use the big repo for testing
        # get the current comps file name for that repo in RHUI
        processed_comps_xml_before = Yummy.repodata_location(RHUA, BIG_REPO, "group")
        # import the empty comps; should be accepted
        RHUIManagerCLI.repo_add_comps(RHUA, BIG_REPO, original_comps_xml)
        # re-get the comps file in RHUI name after the import
        processed_comps_xml_after = Yummy.repodata_location(RHUA, BIG_REPO, "group")
        # should be the same; comparing just the file names as the directory is definitely identical
        nose.tools.eq_(basename(processed_comps_xml_before), basename(processed_comps_xml_after))

    @staticmethod
    def test_15_gzip():
        """try using a compressed comps XML file, should be handled well"""
        # first force the RHUA to cache RHEL Optional repodata, which contains extra groups
        Expect.expect_retval(RHUA, "yum --enablerepo=%s repolist enabled" % ZIP_REPO, timeout=20)
        # get all groups from the cached file
        original_comps_xml = "/var/cache/yum/x86_64/7Server/%s/*comps.xml" % ZIP_REPO
        original_groups = Yummy.comps_xml_grouplist(RHUA, original_comps_xml, False)
        # prepare a temporary file and compress the original comps into it
        compressed_comps_xml = Util.mktemp_remote(RHUA, ".xml.gz")
        Expect.expect_retval(RHUA, "gzip -c %s > %s" % (original_comps_xml, compressed_comps_xml))
        # create another test repo and add the compressed comps to it
        RHUIManagerCLI.repo_create_custom(RHUA, ZIP_REPO)
        RHUIManagerCLI.repo_add_comps(RHUA, ZIP_REPO, compressed_comps_xml)
        # get all groups from the imported metadata
        processed_comps_xml = Yummy.repodata_location(RHUA, ZIP_REPO, "group")
        processed_groups = Yummy.comps_xml_grouplist(RHUA, processed_comps_xml, False)
        # compare the groups
        nose.tools.eq_(original_groups, processed_groups)
        Expect.expect_retval(RHUA, "rm -f %s" % compressed_comps_xml)

    @staticmethod
    def test_16_wrong_input_files():
        """try using an invalid XML file and a file with an invalid extension"""
        # create a bad XML file and use a known non-XML file; reuse the big repo
        bad_xml = Util.mktemp_remote(RHUA, ".xml")
        not_xml = "/etc/motd"
        Expect.expect_retval(RHUA, "echo '<foo></bar>' > %s" % bad_xml)
        for comps_file in [bad_xml, not_xml]:
            nose.tools.assert_raises(ExpectFailed,
                                     RHUIManagerCLI.repo_add_comps,
                                     RHUA,
                                     BIG_REPO,
                                     comps_file)
        Expect.expect_retval(RHUA, "rm -f %s" % bad_xml)

    def test_17_wrong_repo(self):
        """try using an invalid repository ID"""
        # a valid XML file is needed anyway (is parsed first), so reuse the first test repo
        nose.tools.assert_raises(ExpectFailed,
                                 RHUIManagerCLI.repo_add_comps,
                                 RHUA,
                                 BIG_REPO.replace("rpms", "foo"),
                                 "/tmp/extra_rhui_files/%s/comps.xml" % self.test_repos[0])

    def test_99_cleanup(self):
        """clean up"""
        # remove the configuration RPM from the client
        Util.remove_rpm(CLI, [self.repo_with_mod_groups])
        # remove comps info from MongoDB
        units = ["category", "environment", "group", "langpacks"]
        base_mongo_cmd = "db.units_package_%s.remove({})"
        all_mongo_cmds = [base_mongo_cmd % unit for unit in units]
        shell_cmd = "mongo pulp_database --eval '%s'" % "; ".join(all_mongo_cmds)
        Expect.expect_retval(RHUA, shell_cmd)
        # remove repos
        for repo in self.test_repos:
            RHUIManagerCLI.repo_delete(RHUA, repo)
            Expect.expect_retval(RHUA, "rm -rf /tmp/%s*" % repo)
        RHUIManagerCLI.repo_delete(RHUA, BIG_REPO)
        RHUIManagerCLI.repo_delete(RHUA, ZIP_REPO)
        # uninstall HAProxy & CDS, forget their keys
        if not getenv("RHUISKIPSETUP"):
            RHUICLI.delete(RHUA, "haproxy", force=True)
            RHUICLI.delete(RHUA, "cds", force=True)
            ConMgr.remove_ssh_keys(RHUA)
        # if running RHEL Beta, destroy the non-Beta repos again
        cmd = "if grep -c Beta /etc/redhat-release; then " \
              "rm -f /etc/yum.repos.d/redhat-rhui.repo; fi"
        Expect.expect_retval(RHUA, cmd)

    @staticmethod
    def teardown_class():
        """announce the end of the test run"""
        print("*** Finished running %s. *** " % basename(__file__))
