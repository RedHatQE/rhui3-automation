''' Repository management tests '''

from __future__ import print_function

# To check if all entitled repositories can be added and deleted, which takes a huge amount
# of time and can break, run:
# export RHUITESTALLREPOS=1
# in your shell before running this script.

from os import getenv
from os.path import basename

import logging
import nose
from stitches.expect import Expect
import yaml

from rhui3_tests_lib.conmgr import ConMgr
from rhui3_tests_lib.helpers import Helpers
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_entitlement import RHUIManagerEntitlements
from rhui3_tests_lib.rhuimanager_repo import AlreadyExistsError, RHUIManagerRepo
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

RHUA = ConMgr.connect()
# side channel for hacking
RHUA_2 = ConMgr.connect()

CUSTOM_REPOS = ["custom-i386-x86_64", "custom-x86_64-x86_64", "custom-i386-i386"]
CUSTOM_PATHS = [repo.replace("-", "/") for repo in CUSTOM_REPOS]
CUSTOM_RPMS_DIR = "/tmp/extra_rhui_files"

class TestRepo(object):
    '''
       class for repository manipulation tests
    '''

    def __init__(self):
        self.custom_rpms = Util.get_rpms_in_dir(RHUA, CUSTOM_RPMS_DIR)
        if not self.custom_rpms:
            raise RuntimeError("No custom RPMs to test in %s" % CUSTOM_RPMS_DIR)
        # Test the RHEL-6 repo for a change
        version = 6
        arch = "x86_64"
        with open("/etc/rhui3_tests/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)
            try:
                self.yum_repo_name = doc["yum_repos"][version][arch]["name"]
                self.yum_repo_version = doc["yum_repos"][version][arch]["version"]
                self.yum_repo_kind = doc["yum_repos"][version][arch]["kind"]
                self.yum_repo_path = doc["yum_repos"][version][arch]["path"]
                self.containers = {"rh": doc["container_primary"], "alt": doc["container_alt"]}
            except KeyError:
                raise nose.SkipTest("No test repo defined for RHEL %s on %s" % (version, arch))

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_repo_setup():
        '''log in to RHUI, upload cert, check if no repo exists'''
        RHUIManager.initial_run(RHUA)
        entlist = RHUIManagerEntitlements.upload_rh_certificate(RHUA)
        nose.tools.ok_(entlist)
        nose.tools.ok_(not RHUIManagerRepo.list(RHUA))

    @staticmethod
    def test_02_create_3_custom_repos():
        '''create 3 custom repos (protected, unprotected, no RH GPG check) '''
        RHUIManagerRepo.add_custom_repo(RHUA,
                                        CUSTOM_REPOS[0],
                                        "",
                                        CUSTOM_PATHS[0],
                                        "1",
                                        "y")
        RHUIManagerRepo.add_custom_repo(RHUA,
                                        CUSTOM_REPOS[1],
                                        "",
                                        CUSTOM_PATHS[1],
                                        "1",
                                        "n")
        RHUIManagerRepo.add_custom_repo(RHUA,
                                        CUSTOM_REPOS[2],
                                        "",
                                        CUSTOM_PATHS[2],
                                        "1",
                                        "y",
                                        "",
                                        "n")

    @staticmethod
    def test_03_check_custom_repo_list():
        '''check if the repolist contains the 3 custom repos'''
        nose.tools.eq_(RHUIManagerRepo.list(RHUA), sorted(CUSTOM_REPOS))

    @staticmethod
    def test_04_repo_id_uniqueness():
        '''verify that rhui-manager refuses to create a custom repo whose name already exists'''
        nose.tools.assert_raises(AlreadyExistsError,
                                 RHUIManagerRepo.add_custom_repo,
                                 RHUA,
                                 CUSTOM_REPOS[0])

    def test_05_upload_one_rpm(self):
        '''upload one rpm to the custom repo'''
        RHUIManagerRepo.upload_content(RHUA,
                                       [CUSTOM_REPOS[0]],
                                       "%s/%s" % (CUSTOM_RPMS_DIR, self.custom_rpms[0]))

    @staticmethod
    def test_06_upload_several_rpms():
        '''upload several rpms to the custom repo from a directory'''
        RHUIManagerRepo.upload_content(RHUA,
                                       [CUSTOM_REPOS[0]],
                                       CUSTOM_RPMS_DIR)

    def test_07_check_for_package(self):
        '''check package lists'''
        test_rpm_name = self.custom_rpms[0].rsplit('-', 2)[0]
        nose.tools.eq_(RHUIManagerRepo.check_for_package(RHUA,
                                                         CUSTOM_REPOS[0],
                                                         ""),
                       self.custom_rpms)
        nose.tools.eq_(RHUIManagerRepo.check_for_package(RHUA,
                                                         CUSTOM_REPOS[0],
                                                         test_rpm_name),
                       [self.custom_rpms[0]])
        nose.tools.eq_(RHUIManagerRepo.check_for_package(RHUA,
                                                         CUSTOM_REPOS[0],
                                                         "test"),
                       [])
        nose.tools.eq_(RHUIManagerRepo.check_for_package(RHUA,
                                                         CUSTOM_REPOS[1],
                                                         ""),
                       [])

    def test_08_display_custom_repos(self):
        '''check detailed information on the custom repos'''
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [CUSTOM_REPOS[0], CUSTOM_PATHS[0]],
                                                   [True, True],
                                                   [True, None, True],
                                                   len(self.custom_rpms))
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [CUSTOM_REPOS[1], CUSTOM_PATHS[1]],
                                                   [True, False],
                                                   [True, None, True],
                                                   0)
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [CUSTOM_REPOS[2], CUSTOM_PATHS[2]],
                                                   [True, True],
                                                   [False],
                                                   0)

    def test_09_add_rh_repo_by_repo(self):
        '''add a Red Hat repo by its name'''
        RHUIManagerRepo.add_rh_repo_by_repo(RHUA, [Util.format_repo(self.yum_repo_name,
                                                                    self.yum_repo_version,
                                                                    self.yum_repo_kind)])
        repo_list = RHUIManagerRepo.list(RHUA)
        nose.tools.ok_(Util.format_repo(self.yum_repo_name, self.yum_repo_version) in repo_list,
                       msg="The repo wasn't added. Actual repolist: %s" % repo_list)

    def test_10_display_rh_repo(self):
        '''check detailed information on the Red Hat repo'''
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [Util.format_repo(self.yum_repo_name,
                                                                     self.yum_repo_version),
                                                    self.yum_repo_path],
                                                   [False],
                                                   [True, None, True],
                                                   0)

    def test_11_delete_one_repo(self):
        '''remove the Red Hat repo'''
        RHUIManagerRepo.delete_repo(RHUA,
                                    [Util.format_repo(self.yum_repo_name, self.yum_repo_version)])
        repo_list = RHUIManagerRepo.list(RHUA)
        nose.tools.ok_(Util.format_repo(self.yum_repo_name, self.yum_repo_version) not in repo_list,
                       msg="The repo wasn't removed. Actual repolist: %s" % repo_list)

    def test_12_add_rh_repo_by_product(self):
        '''add a Red Hat repo by the product that contains it, remove it'''
        RHUIManagerRepo.add_rh_repo_by_product(RHUA, [self.yum_repo_name])
        repo_list = RHUIManagerRepo.list(RHUA)
        nose.tools.ok_(Util.format_repo(self.yum_repo_name, self.yum_repo_version) in repo_list,
                       msg="The repo wasn't added. Actual repolist: %s" % repo_list)
        RHUIManagerRepo.delete_all_repos(RHUA)
        nose.tools.ok_(not RHUIManagerRepo.list(RHUA))

    @staticmethod
    def test_13_add_all_rh_repos():
        '''add all Red Hat repos, remove them (takes a lot of time!)'''
        if not getenv("RHUITESTALLREPOS"):
            raise nose.exc.SkipTest("Not explicitly requested.")
        RHUIManagerRepo.add_rh_repo_all(RHUA)
        # it's not feasible to get the repo list if so many repos are present; skip the check
        #nose.tools.ok_(len(RHUIManagerRepo.list(RHUA)) > 100)
        RHUIManagerRepo.delete_all_repos(RHUA)
        nose.tools.ok_(not RHUIManagerRepo.list(RHUA))

    def test_14_add_containers(self):
        '''add containers'''
        # use saved credentials; save them in the RHUI configuration first
        # first a RH container
        Helpers.set_registry_credentials(RHUA)
        RHUIManagerRepo.add_container(RHUA,
                                      self.containers["rh"]["name"],
                                      "",
                                      self.containers["rh"]["displayname"])
        # then a Quay container
        Helpers.set_registry_credentials(RHUA, "quay", backup=False)
        RHUIManagerRepo.add_container(RHUA, self.containers["alt"]["quay"]["name"])
        # and finaly a Docker container; we'll need the Docker Hub URL as there's no
        # auth config for it
        url = Helpers.get_registry_url("docker")
        Helpers.set_registry_credentials(RHUA, "docker", [url], backup=False)
        RHUIManagerRepo.add_container(RHUA, self.containers["alt"]["docker"]["name"])
        # check all of that
        repo_list = RHUIManagerRepo.list(RHUA)
        nose.tools.ok_(len(repo_list) == 3,
                       msg="The containers weren't added. Actual repolist: %s" % repo_list)

    def test_15_display_container(self):
        '''check detailed information on the RH container'''
        repo_name = Util.safe_pulp_repo_name(self.containers["rh"]["name"])
        RHUIManagerRepo.check_detailed_information(RHUA,
                                                   [self.containers["rh"]["displayname"],
                                                    "https://%s/pulp/docker/%s/" % \
                                                    (ConMgr.get_cds_lb_hostname(), repo_name)],
                                                   [False],
                                                   [True, None, True],
                                                   0)

    @staticmethod
    def test_16_delete_containers():
        '''delete the containers'''
        Helpers.restore_rhui_tools_conf(RHUA)
        RHUIManagerRepo.delete_all_repos(RHUA)
        nose.tools.ok_(not RHUIManagerRepo.list(RHUA))

    @staticmethod
    def test_17_missing_cert_handling():
        '''check if rhui-manager can handle the loss of the RH cert'''
        # for RHBZ#1325390
        RHUIManagerEntitlements.upload_rh_certificate(RHUA)
        # launch rhui-manager in one connection, delete the cert in the other
        RHUIManager.screen(RHUA, "repo")
        RHUIManager.remove_rh_certs(RHUA_2)
        Expect.enter(RHUA, "a")
        # a bit strange response to see in this context, but eh, no == all if you're a geek
        Expect.expect(RHUA, "All entitled products are currently deployed in the RHUI")
        Expect.enter(RHUA, "q")
        # an error message should be logged, though
        Expect.ping_pong(RHUA,
                         "tail /root/.rhui/rhui.log",
                         "The entitlement.*has no associated certificate")

    @staticmethod
    def test_18_repo_select_0():
        '''check if no repo is chosen if 0 is entered when adding a repo'''
        # for RHBZ#1305612
        # upload the small cert and try entering 0 when the list of repos is displayed
        RHUIManagerEntitlements.upload_rh_certificate(RHUA,
                                                      "/tmp/extra_rhui_files/rhcert_atomic.pem")
        RHUIManager.screen(RHUA, "repo")
        Expect.enter(RHUA, "a")
        Expect.expect(RHUA, "Enter value", 180)
        Expect.enter(RHUA, "3")
        Expect.expect(RHUA, "Enter value")
        Expect.enter(RHUA, "0")
        Expect.expect(RHUA, "Enter value")
        Expect.enter(RHUA, "c")
        Expect.expect(RHUA, "Proceed")
        Expect.enter(RHUA, "y")
        Expect.expect(RHUA, "Content")
        Expect.enter(RHUA, "q")

        # the RHUI repo list ought to be empty now; if not, delete the repo and fail
        repo_list = RHUIManagerRepo.list(RHUA)
        RHUIManager.remove_rh_certs(RHUA)
        if repo_list:
            RHUIManagerRepo.delete_all_repos(RHUA)
            raise AssertionError("The repo list is not empty: %s." % repo_list)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
