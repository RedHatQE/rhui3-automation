'''RHUI CLI tests'''

import logging
from os.path import basename, join
import re
from shutil import rmtree
from tempfile import mkdtemp

import nose
import stitches
from stitches.expect import Expect
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_cmdline import RHUIManagerCLI, \
                                                CustomRepoAlreadyExists, \
                                                CustomRepoGpgKeyNotFound
from rhui3_tests_lib.subscription import RHSMRHUI

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
CUSTOM_REPOS = ["my_custom_repo", "another_custom_repo"]
CR_NAMES = ["", CUSTOM_REPOS[1].replace("_", " ").title()]
TMPDIR = mkdtemp()
AVAILABLE_POOL_FILE = join(TMPDIR, "available")
REGISTERED_POOL_FILE = join(TMPDIR, "registered")

class TestCLI(object):
    '''
        class for CLI tests
    '''

    def __init__(self):
        with open('/usr/share/rhui3_tests_lib/config/tested_repos.yaml', 'r') as configfile:
            doc = yaml.load(configfile)

        self.yum_repo_name_1 = doc['CLI_repo1']['name']
        self.yum_repo_id_1 = doc['CLI_repo1']['id']
        self.yum_repo_label_1 = doc['CLI_repo1']['label']
        self.yum_repo_name_2 = doc['CLI_repo2']['name']
        self.yum_repo_id_2 = doc['CLI_repo2']['id']
        self.yum_repo_label_2 = doc['CLI_repo2']['label']
        self.subscription_name_1 = doc['subscription1']['name']

    @staticmethod
    def setup_class():
        '''
           announce the beginning of the test run
        '''
        print("*** Running %s: *** " % basename(__file__))

    @staticmethod
    def test_01_initial_run():
        '''log in to RHUI'''
        RHUIManager.initial_run(CONNECTION)

    @staticmethod
    def test_02_check_empty_repo_list():
        '''check if the repo list is empty'''
        repolist = RHUIManagerCLI.get_repo_lists(CONNECTION)
        nose.tools.ok_(not repolist["redhat"] and not repolist["custom"],
                       msg="there are some repos already: %s" % repolist)

    @staticmethod
    def test_03_create_custom_repos():
        '''create two custom repos for testing'''
        RHUIManagerCLI.repo_create_custom(CONNECTION, CUSTOM_REPOS[0])
        RHUIManagerCLI.repo_create_custom(CONNECTION,
                                          repo_id=CUSTOM_REPOS[1],
                                          path="t_path",
                                          display_name=CR_NAMES[1],
                                          legacy_md=True,
                                          gpg_public_keys="/tmp/extra_rhui_files/test_gpg_key")

    @staticmethod
    def test_04_custom_repo_checks():
        '''check if the custom repo cannot be added twice and if the GPG key path is validated'''
        nose.tools.assert_raises(CustomRepoAlreadyExists,
                                 RHUIManagerCLI.repo_create_custom,
                                 CONNECTION,
                                 CUSTOM_REPOS[0])
        nose.tools.assert_raises(CustomRepoGpgKeyNotFound,
                                 RHUIManagerCLI.repo_create_custom,
                                 CONNECTION,
                                 CUSTOM_REPOS[0] + "2",
                                 gpg_public_keys="/this_file_cant_be_there")

    @staticmethod
    def test_05_check_custom_repos():
        '''check if the custom repos were actually created'''
        RHUIManagerCLI.repo_list(CONNECTION, CUSTOM_REPOS[0], CUSTOM_REPOS[0])
        RHUIManagerCLI.repo_list(CONNECTION, CUSTOM_REPOS[1], CR_NAMES[1])

    @staticmethod
    def test_06_upload_rpm():
        '''upload content to one of the custom repos'''
        RHUIManagerCLI.packages_upload(CONNECTION,
                                       CUSTOM_REPOS[0],
                                       "/tmp/extra_rhui_files/rhui-rpm-upload-test-1-1.noarch.rpm")

    @staticmethod
    def test_07_check_package():
        '''check that the uploaded package is now in the repo'''
        RHUIManagerCLI.packages_list(CONNECTION,
                                     CUSTOM_REPOS[0],
                                     "rhui-rpm-upload-test-1-1.noarch.rpm")

    @staticmethod
    def test_08_upload_certificate():
        '''upload the Atomic (the small) entitlement certificate'''
        RHUIManagerCLI.cert_upload(CONNECTION, "/tmp/extra_rhui_files/rhcert_atomic.pem", "Atomic")

    @staticmethod
    def test_09_check_certificate_info():
        '''check certificate info for validity'''
        RHUIManagerCLI.cert_info(CONNECTION)

    @staticmethod
    def test_10_check_certificate_exp():
        '''check if the certificate expiration date is OK'''
        RHUIManagerCLI.cert_expiration(CONNECTION)

    def test_11_check_unused_product(self):
        '''check if a repo is available'''
        RHUIManagerCLI.repo_unused(CONNECTION, self.yum_repo_name_1)

    def test_12_add_rh_repo_by_id(self):
        '''add a Red Hat repo by its ID'''
        RHUIManagerCLI.repo_add_by_repo(CONNECTION, [self.yum_repo_id_2])

    def test_13_add_rh_repo_by_product(self):
        '''add a Red Hat repo by its product name'''
        RHUIManagerCLI.repo_add(CONNECTION, self.yum_repo_name_1)

    def test_14_repo_list(self):
        '''check the added repos'''
        RHUIManagerCLI.repo_list(CONNECTION, self.yum_repo_id_1, self.yum_repo_name_1)
        RHUIManagerCLI.repo_list(CONNECTION, self.yum_repo_id_2, self.yum_repo_name_2)

    def test_15_no_unexpected_repos(self):
        '''check if no stray repo was added'''
        repolist_expected = {"redhat": sorted([[self.yum_repo_id_1, self.yum_repo_name_1],
                                               [self.yum_repo_id_2, self.yum_repo_name_2]]),
                             "custom": sorted([[CUSTOM_REPOS[0], CUSTOM_REPOS[0]],
                                               [CUSTOM_REPOS[1], CR_NAMES[1]]])}
        repolist_actual = RHUIManagerCLI.get_repo_lists(CONNECTION)
        nose.tools.eq_(repolist_expected, repolist_actual)

    def test_16_start_syncing_repo(self):
        '''sync one of the repos'''
        RHUIManagerCLI.repo_sync(CONNECTION, self.yum_repo_id_2, self.yum_repo_name_2)

    def test_17_repo_info(self):
        '''verify that the repo name is part of the information about the specified repo ID'''
        RHUIManagerCLI.repo_info(CONNECTION, self.yum_repo_id_2, self.yum_repo_name_2)

    def test_18_check_package_in_repo(self):
        '''check a random package in the repo'''
        RHUIManagerCLI.packages_list(CONNECTION, self.yum_repo_id_2, "ostree")

    def test_19_list_labels(self):
        '''check repo labels'''
        RHUIManagerCLI.repo_labels(CONNECTION, self.yum_repo_label_1)

    def test_20_generate_certificate(self):
        '''generate an entitlement certificate'''
        RHUIManagerCLI.client_cert(CONNECTION,
                                   [self.yum_repo_label_1, self.yum_repo_label_2],
                                   "atomic_and_my",
                                   365,
                                   "/tmp")

    @staticmethod
    def test_21_check_cli_crt_sig():
        '''check if SHA-256 is used in the client certificate signature'''
        # for RHBZ#1628957
        sigs_expected = ["sha256", "sha256"]
        _, stdout, _ = CONNECTION.exec_command("openssl x509 -noout -text -in " +
                                               "/tmp/atomic_and_my.crt")
        with stdout as output:
            cert_details = output.read().decode()
        sigs_actual = re.findall("sha[0-9]+", cert_details)
        nose.tools.eq_(sigs_expected, sigs_actual)

    @staticmethod
    def test_22_create_cli_config_rpm():
        '''create a client configuration RPM'''
        RHUIManagerCLI.client_rpm(CONNECTION,
                                  ["/tmp/atomic_and_my.key", "/tmp/atomic_and_my.crt"],
                                  ["1.0", "atomic_and_my"],
                                  "/tmp",
                                  [CUSTOM_REPOS[0]])

    @staticmethod
    def test_23_ensure_gpgcheck_config():
        '''ensure that GPG checking is enabled in the client configuration'''
        Expect.expect_retval(CONNECTION,
                             r"grep -q '^gpgcheck\s*=\s*1$' " +
                             "/tmp/atomic_and_my-1.0/build/BUILD/atomic_and_my-1.0/rh-cloud.repo")

    @staticmethod
    def test_24_upload_expired_cert():
        '''check expired certificate handling'''
        RHUIManagerCLI.cert_upload(CONNECTION, "/tmp/extra_rhui_files/rhcert_expired.pem",
                                   "The provided certificate is expired or invalid")

    @staticmethod
    def test_25_upload_incompat_cert():
        '''check incompatible certificate handling'''
        RHUIManagerCLI.cert_upload(CONNECTION, "/tmp/extra_rhui_files/rhcert_incompatible.pem",
                                   "does not contain any entitlements")

    @staticmethod
    def test_26_register_system():
        '''register the system in RHSM, attach RHUI SKU'''
        RHSMRHUI.register_system(CONNECTION)
        RHSMRHUI.attach_rhui_sku(CONNECTION)

    @staticmethod
    def test_27_fetch_available_pool():
        '''fetch the available pool ID'''
        available_pool = RHUIManagerCLI.subscriptions_list(CONNECTION, "available", True)
        nose.tools.ok_(re.search(r'^[0-9a-f]+$', available_pool) is not None)
        with open(AVAILABLE_POOL_FILE, "w") as apf:
            apf.write(available_pool)

    @staticmethod
    def test_28_register_subscription():
        '''register the subscription using the fetched pool ID'''
        with open(AVAILABLE_POOL_FILE) as apf:
            available_pool = apf.read()
        nose.tools.ok_(re.search(r'^[0-9a-f]+$', available_pool) is not None)
        RHUIManagerCLI.subscriptions_register(CONNECTION, available_pool)

    @staticmethod
    def test_29_fetch_registered_pool():
        '''fetch the registered pool ID'''
        registered_pool = RHUIManagerCLI.subscriptions_list(CONNECTION, "registered", True)
        nose.tools.ok_(re.search(r'^[0-9a-f]+$', registered_pool) is not None)
        with open(REGISTERED_POOL_FILE, "w") as rpf:
            rpf.write(registered_pool)

    @staticmethod
    def test_30_compare_pools():
        '''check if the previously available and now registered pool IDs are the same'''
        with open(AVAILABLE_POOL_FILE) as apf:
            available_pool = apf.read()
        with open(REGISTERED_POOL_FILE) as rpf:
            registered_pool = rpf.read()
        nose.tools.assert_equal(available_pool, registered_pool)

    def test_31_check_reg_pool_for_rhui(self):
        '''check if the registered subscription's description is RHUI for CCSP'''
        list_reg = RHUIManagerCLI.subscriptions_list(CONNECTION)
        nose.tools.ok_(self.subscription_name_1 in list_reg,
                       msg="Expected subscription not registered in RHUI! Got: " + list_reg)

    @staticmethod
    def test_32_unregister_subscription():
        '''remove the subscription from RHUI'''
        with open(REGISTERED_POOL_FILE) as rpf:
            registered_pool = rpf.read()
        nose.tools.ok_(re.search(r'^[0-9a-f]+$', registered_pool) is not None)
        RHUIManagerCLI.subscriptions_unregister(CONNECTION, registered_pool)

    @staticmethod
    def test_33_unregister_system():
        '''unregister the system from RHSM'''
        RHSMRHUI.unregister_system(CONNECTION)

    def test_34_resync_repo(self):
        '''sync the repo again'''
        RHUIManagerCLI.repo_sync(CONNECTION, self.yum_repo_id_2, self.yum_repo_name_2)

    @staticmethod
    def test_35_resync_no_warning():
        '''check if the syncs did not cause known unnecessary warnings'''
        # for RHBZ#1506872
        Expect.expect_retval(CONNECTION, "grep -q 'pulp.*metadata:WARNING' /var/log/messages", 1)
        # for RHBZ#1579294
        Expect.expect_retval(CONNECTION, "grep -q 'pulp.*publish:WARNING' /var/log/messages", 1)

    @staticmethod
    def test_36_list_repos():
        '''get a list of available repos for further examination'''
        Expect.expect_retval(CONNECTION,
                             "rhui-manager repo unused > /tmp/repos.stdout 2> /tmp/repos.stderr",
                             timeout=1200)

    @staticmethod
    def test_37_check_iso_repos():
        '''check if non-RPM repos were ignored'''
        # for RHBZ#1199426
        Expect.expect_retval(CONNECTION,
                             "egrep -q 'Containers|Images|ISOs|Kickstart' /tmp/repos.stdout", 1)

    @staticmethod
    def test_38_check_pygiwarning():
        '''check if PyGIWarning was not issued'''
        # for RHBZ#1450430
        Expect.expect_retval(CONNECTION, "grep -q PyGIWarning /tmp/repos.stderr", 1)

    @staticmethod
    def test_39_check_repo_sorting():
        '''check if repo lists are sorted'''
        # for RHBZ#1601478
        repos = RHUIManagerCLI.get_repo_lists(CONNECTION)
        nose.tools.assert_equal(repos["redhat"], sorted(repos["redhat"]))
        nose.tools.assert_equal(repos["custom"], sorted(repos["custom"]))

    def test_40_upload_semi_bad_cert(self):
        '''check that a partially invalid certificate can still be accepted'''
        # for RHBZ#1588931 & RHBZ#1584527
        # delete currently used certificates and repos first
        RHUIManager.remove_rh_certs(CONNECTION)
        for repo in CUSTOM_REPOS + [self.yum_repo_id_1, self.yum_repo_id_2]:
            RHUIManagerCLI.repo_delete(CONNECTION, repo)
        repolist = RHUIManagerCLI.get_repo_lists(CONNECTION)
        nose.tools.ok_(not repolist["redhat"] and not repolist["custom"],
                       msg="can't continue as some repos remain: %s" % repolist)
        # try uploading the cert now
        RHUIManagerCLI.cert_upload(CONNECTION,
                                   "/tmp/extra_rhui_files/rhcert_partially_invalid.pem",
                                   "Red Hat Enterprise Linux 7 Server from RHUI")
        # the RHUI log must contain the fact that an invalid path was found in the cert
        Expect.ping_pong(CONNECTION, "tail /root/.rhui/rhui.log", "Invalid entitlement path")

    @staticmethod
    def test_99_cleanup():
        '''cleanup: remove certs and other files'''
        RHUIManager.remove_rh_certs(CONNECTION)
        Expect.ping_pong(CONNECTION, "rm -rf /tmp/atomic_and_my* ; " +
                         "ls /tmp/atomic_and_my* 2>&1",
                         "No such file or directory")
        Expect.ping_pong(CONNECTION, "rm -f /tmp/repos.std{out,err} ; " +
                         "ls /tmp/repos.std{out,err} 2>&1",
                         "No such file or directory")
        rmtree(TMPDIR)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
