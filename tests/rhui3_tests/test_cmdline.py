'''RHUI CLI tests'''

import logging
from os.path import basename, getsize, join
import re
from shutil import rmtree
from tempfile import mkdtemp
import time

try:
    from configparser import ConfigParser # Python 3+
except ImportError:
    from ConfigParser import ConfigParser # Python 2
import nose
import stitches
from stitches.expect import Expect
import yaml

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_cmdline import RHUIManagerCLI, \
                                                CustomRepoAlreadyExists, \
                                                CustomRepoGpgKeyNotFound
from rhui3_tests_lib.subscription import RHSMRHUI
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

CONNECTION = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
CUSTOM_REPOS = ["my_custom_repo", "another_custom_repo", "yet_another_custom_repo"]
CR_NAMES = ["", CUSTOM_REPOS[1].replace("_", " ").title()]
ALT_CONTENT_SRC_NAME = "atomic_cs"
TMPDIR = mkdtemp()
AVAILABLE_POOL_FILE = join(TMPDIR, "available")
REGISTERED_POOL_FILE = join(TMPDIR, "registered")
YUM_REPO_FILE = join(TMPDIR, "rh-cloud.repo")

class TestCLI(object):
    '''
        class for CLI tests
    '''

    def __init__(self):
        with open("/usr/share/rhui3_tests_lib/config/tested_repos.yaml") as configfile:
            doc = yaml.load(configfile)

        self.yum_repo_names = [doc["CLI_repo1"]["name"], doc["CLI_repo2"]["name"]]
        self.yum_repo_ids = [doc["CLI_repo1"]["id"], doc["CLI_repo2"]["id"]]
        self.yum_repo_labels = [doc["CLI_repo1"]["label"], doc["CLI_repo2"]["label"]]
        self.yum_repo_paths = [doc["CLI_repo1"]["path"], doc["CLI_repo2"]["path"]]
        self.product_name = doc["CLI_product"]["name"]
        self.product_repos = ["%s-%s" % (doc["CLI_product"]["repos_basename"], arch)
                              for arch in doc["CLI_product"]["arches"].split()]
        self.subscription_name = doc["subscription"]["name"]

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
        repolist = RHUIManagerCLI.repo_list(CONNECTION, True)
        nose.tools.ok_(not repolist, msg="there are some repos already: %s" % repolist)

    @staticmethod
    def test_03_create_custom_repos():
        '''create three custom repos for testing'''
        # the first repo will be unprotected, with default parameters
        RHUIManagerCLI.repo_create_custom(CONNECTION, CUSTOM_REPOS[0])
        # the second repo will have a lot of custom parameters; it will be a protected repo
        RHUIManagerCLI.repo_create_custom(CONNECTION,
                                          repo_id=CUSTOM_REPOS[1],
                                          path="huh-%s" % CUSTOM_REPOS[1],
                                          display_name=CR_NAMES[1],
                                          legacy_md=True,
                                          protected=True,
                                          gpg_public_keys="/tmp/extra_rhui_files/test_gpg_key")
        # the third repo will also be protected
        RHUIManagerCLI.repo_create_custom(CONNECTION,
                                          repo_id=CUSTOM_REPOS[2],
                                          protected=True)

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
        # try a delimiter this time
        delimiter = ","
        repos_expected = delimiter.join(sorted(CUSTOM_REPOS))
        repos_actual = RHUIManagerCLI.repo_list(CONNECTION, True, False, delimiter)
        nose.tools.eq_(repos_expected, repos_actual)
        # ^ also checks if the repo IDs are sorted

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
        RHUIManager.cacert_expiration(CONNECTION)

    def test_11_check_unused_product(self):
        '''check if a repo is available'''
        RHUIManagerCLI.repo_unused(CONNECTION, self.yum_repo_names[0])

    def test_12_add_rh_repo_by_id(self):
        '''add a Red Hat repo by its ID'''
        RHUIManagerCLI.repo_add_by_repo(CONNECTION, [self.yum_repo_ids[1]])

    def test_13_add_rh_repo_by_product(self):
        '''add a Red Hat repo by its product name'''
        RHUIManagerCLI.repo_add(CONNECTION, self.yum_repo_names[0])

    def test_14_repo_list(self):
        '''check the added repos'''
        repolist_actual = RHUIManagerCLI.repo_list(CONNECTION, True, True).splitlines()
        nose.tools.eq_(self.yum_repo_ids, repolist_actual)

    def test_15_start_syncing_repo(self):
        '''sync one of the repos'''
        RHUIManagerCLI.repo_sync(CONNECTION, self.yum_repo_ids[1], self.yum_repo_names[1])

    def test_16_repo_info(self):
        '''verify that the repo name is part of the information about the specified repo ID'''
        RHUIManagerCLI.repo_info(CONNECTION, self.yum_repo_ids[1], self.yum_repo_names[1])

    def test_17_check_package_in_repo(self):
        '''check a random package in the repo'''
        RHUIManagerCLI.packages_list(CONNECTION, self.yum_repo_ids[1], "ostree")

    def test_18_list_labels(self):
        '''check repo labels'''
        actual_labels = RHUIManagerCLI.repo_labels(CONNECTION)
        nose.tools.ok_(all(repo in actual_labels for repo in self.yum_repo_labels),
                       msg="%s not found in %s" % (self.yum_repo_labels, actual_labels))

    def test_19_generate_certificate(self):
        '''generate an entitlement certificate'''
        # generate it for RH repos and the first protected custom repo
        # the label is the repo ID in the case of custom repos
        RHUIManagerCLI.client_cert(CONNECTION,
                                   self.yum_repo_labels + [CUSTOM_REPOS[1]],
                                   "atomic_and_my",
                                   365,
                                   "/tmp")

    @staticmethod
    def test_20_check_cli_crt_sig():
        '''check if SHA-256 is used in the client certificate signature'''
        # for RHBZ#1628957
        sigs_expected = ["sha256", "sha256"]
        _, stdout, _ = CONNECTION.exec_command("openssl x509 -noout -text -in " +
                                               "/tmp/atomic_and_my.crt")
        with stdout as output:
            cert_details = output.read().decode()
        sigs_actual = re.findall("sha[0-9]+", cert_details)
        nose.tools.eq_(sigs_expected, sigs_actual)

    def test_21_check_stray_custom_repo(self):
        '''check if only the wanted repos are in the certificate'''
        repo_labels_expected = ["custom-%s" % CUSTOM_REPOS[1]] + self.yum_repo_labels
        _, stdout, _ = CONNECTION.exec_command("cat /tmp/atomic_and_my-extensions.txt")
        with stdout as output:
            extensions = output.read().decode()
        repo_labels_actual = re.findall("|".join(["custom-.*"] + self.yum_repo_labels),
                                        extensions)
        nose.tools.eq_(sorted(repo_labels_expected), sorted(repo_labels_actual))

    @staticmethod
    def test_22_create_cli_config_rpm():
        '''create a client configuration RPM'''
        RHUIManagerCLI.client_rpm(CONNECTION,
                                  ["/tmp/atomic_and_my.key", "/tmp/atomic_and_my.crt"],
                                  ["atomic_and_my", "1.0", "0.1"],
                                  "/tmp",
                                  [CUSTOM_REPOS[0]],
                                  "_none_")
        # check if the rpm was created
        Expect.expect_retval(CONNECTION,
                             "test -f /tmp/atomic_and_my-1.0/build/RPMS/noarch/" +
                             "atomic_and_my-1.0-0.1.noarch.rpm")

    def test_23_ensure_gpgcheck_config(self):
        '''ensure that GPG checking is configured in the client configuration as expected'''
        # for RHBZ#1428756
        # we'll need the repo file in a few tests; fetch it now
        remote_repo_file = "/tmp/atomic_and_my-1.0/build/BUILD/atomic_and_my-1.0/rh-cloud.repo"
        try:
            Util.fetch(CONNECTION,
                       remote_repo_file,
                       YUM_REPO_FILE)
        except IOError:
            raise RuntimeError("configuration not created, can't test it")
        yum_cfg = ConfigParser()
        yum_cfg.read(YUM_REPO_FILE)
        # check RH repos: they all must have GPG checking enabled; get a list of those that don't
        bad = [r for r in self.yum_repo_labels if not yum_cfg.getboolean("rhui-%s" % r, "gpgcheck")]
        # check custom repos: the 2nd must have GPG checking enabled:
        if not yum_cfg.getboolean("rhui-custom-%s" % CUSTOM_REPOS[1], "gpgcheck"):
            bad.append(CUSTOM_REPOS[1])
        # the first one mustn't:
        if yum_cfg.getboolean("rhui-custom-%s" % CUSTOM_REPOS[0], "gpgcheck"):
            bad.append(CUSTOM_REPOS[0])
        nose.tools.ok_(not bad, msg="Unexpected GPG checking configuration for %s" % bad)

    @staticmethod
    def test_24_ensure_proxy_config():
        '''ensure that the proxy setting is used in the client configuration'''
        # for RHBZ#1658088
        # reuse the fetched file if possible
        if not getsize(YUM_REPO_FILE):
            raise RuntimeError("configuration not created, can't test it")
        yum_cfg = ConfigParser()
        yum_cfg.read(YUM_REPO_FILE)
        nose.tools.ok_(all([yum_cfg.get(r, "proxy") == "_none_" for r in yum_cfg.sections()]))

    @staticmethod
    def test_25_custom_repo_used():
        '''check if the protected custom repo is included in the client configuration'''
        # for RHBZ#1663422
        # reuse the fetched file if possible
        if not getsize(YUM_REPO_FILE):
            raise RuntimeError("configuration not created, can't test it")
        yum_cfg = ConfigParser()
        yum_cfg.read(YUM_REPO_FILE)
        nose.tools.ok_("rhui-custom-%s" % CUSTOM_REPOS[1] in yum_cfg.sections())

    def test_26_create_acs_config_rpm(self):
        '''create an alternate content source configuration RPM'''
        # for RHBZ#1695464
        name = ALT_CONTENT_SRC_NAME
        RHUIManagerCLI.client_content_source(CONNECTION,
                                             self.yum_repo_labels,
                                             [name],
                                             "/tmp")
        # check that
        cmd = "rpm2cpio /tmp/%s-2.0/build/RPMS/noarch/%s-2.0-1.noarch.rpm | " % (name, name) + \
              r"cpio -i --to-stdout \*.conf | " + \
              "sed -n -e '/^paths:/,$p' | " + \
              "sed s/paths://"
        _, stdout, _ = CONNECTION.exec_command(cmd)
        with stdout as output:
            paths_actual_raw = output.read().decode().splitlines()
            # the paths are indented, let's get rid of the formatting
            paths_actual = [p.lstrip() for p in paths_actual_raw]
            # the OSTree repo must not be included
            paths_expected = [p for p in self.yum_repo_paths if "ostree" not in p]
            nose.tools.eq_(paths_expected, paths_actual)

    @staticmethod
    def test_27_upload_expired_cert():
        '''check expired certificate handling'''
        RHUIManagerCLI.cert_upload(CONNECTION, "/tmp/extra_rhui_files/rhcert_expired.pem",
                                   "The provided certificate is expired or invalid")

    @staticmethod
    def test_28_upload_incompat_cert():
        '''check incompatible certificate handling'''
        cert = "/tmp/extra_rhui_files/rhcert_incompatible.pem"
        if Util.cert_expired(CONNECTION, cert):
            raise nose.exc.SkipTest("The given certificate has already expired.")
        RHUIManagerCLI.cert_upload(CONNECTION, cert, "does not contain any entitlements")

    @staticmethod
    def test_29_register_system():
        '''register the system in RHSM, attach RHUI SKU'''
        RHSMRHUI.register_system(CONNECTION)
        RHSMRHUI.attach_rhui_sku(CONNECTION)

    @staticmethod
    def test_30_fetch_available_pool():
        '''fetch the available pool ID'''
        available_pool = RHUIManagerCLI.subscriptions_list(CONNECTION, "available", True)
        nose.tools.ok_(re.search(r"^[0-9a-f]+$", available_pool) is not None,
                       msg="invalid pool ID: '%s'" % available_pool)
        with open(AVAILABLE_POOL_FILE, "w") as apf:
            apf.write(available_pool)

    @staticmethod
    def test_31_register_subscription():
        '''register the subscription using the fetched pool ID'''
        try:
            with open(AVAILABLE_POOL_FILE) as apf:
                available_pool = apf.read()
        except IOError:
            raise RuntimeError("pool ID was not fetched")
        nose.tools.ok_(re.search(r"^[0-9a-f]+$", available_pool) is not None,
                       msg="invalid pool ID: '%s'" % available_pool)
        RHUIManagerCLI.subscriptions_register(CONNECTION, available_pool)

    @staticmethod
    def test_32_fetch_registered_pool():
        '''fetch the registered pool ID'''
        registered_pool = RHUIManagerCLI.subscriptions_list(CONNECTION, "registered", True)
        nose.tools.ok_(re.search(r"^[0-9a-f]+$", registered_pool) is not None,
                       msg="invalid pool ID: '%s'" % registered_pool)
        with open(REGISTERED_POOL_FILE, "w") as rpf:
            rpf.write(registered_pool)

    @staticmethod
    def test_33_compare_pools():
        '''check if the previously available and now registered pool IDs are the same'''
        try:
            with open(AVAILABLE_POOL_FILE) as apf:
                available_pool = apf.read()
        except IOError:
            raise RuntimeError("no known available pool ID")
        try:
            with open(REGISTERED_POOL_FILE) as rpf:
                registered_pool = rpf.read()
        except IOError:
            raise RuntimeError("no known registered pool ID")
        nose.tools.eq_(available_pool, registered_pool)

    def test_34_check_reg_pool_for_rhui(self):
        '''check if the registered subscription's description is RHUI for CCSP'''
        list_reg = RHUIManagerCLI.subscriptions_list(CONNECTION)
        nose.tools.ok_(self.subscription_name in list_reg,
                       msg="Expected subscription not registered in RHUI! Got: %s" % list_reg)

    @staticmethod
    def test_35_unregister_subscription():
        '''remove the subscription from RHUI'''
        try:
            with open(REGISTERED_POOL_FILE) as rpf:
                registered_pool = rpf.read()
        except IOError:
            raise RuntimeError("no known registered pool ID")
        nose.tools.ok_(re.search(r"^[0-9a-f]+$", registered_pool) is not None,
                       msg="invalid pool ID: '%s'" % registered_pool)
        RHUIManagerCLI.subscriptions_unregister(CONNECTION, registered_pool)

    @staticmethod
    def test_36_unregister_system():
        '''unregister the system from RHSM'''
        RHSMRHUI.unregister_system(CONNECTION)

    def test_37_resync_repo(self):
        '''sync the repo again'''
        RHUIManagerCLI.repo_sync(CONNECTION, self.yum_repo_ids[1], self.yum_repo_names[1])

    @staticmethod
    def test_38_resync_no_warning():
        '''check if the syncs did not cause known unnecessary warnings'''
        # for RHBZ#1506872
        Expect.expect_retval(CONNECTION, "grep 'pulp.*metadata:WARNING' /var/log/messages", 1)
        # for RHBZ#1579294
        Expect.expect_retval(CONNECTION, "grep 'pulp.*publish:WARNING' /var/log/messages", 1)
        # for RHBZ#1487523
        Expect.expect_retval(CONNECTION,
                             "grep 'pulp.*Purging duplicate NEVRA can' /var/log/messages", 1)

    @staticmethod
    def test_39_list_repos():
        '''get a list of available repos for further examination'''
        Expect.expect_retval(CONNECTION,
                             "rhui-manager repo unused > /tmp/repos.stdout 2> /tmp/repos.stderr",
                             timeout=1200)

    @staticmethod
    def test_40_check_iso_repos():
        '''check if non-RPM repos were ignored'''
        # for RHBZ#1199426
        Expect.expect_retval(CONNECTION,
                             "egrep 'Containers|Images|ISOs|Kickstart' /tmp/repos.stdout", 1)

    @staticmethod
    def test_41_check_pygiwarning():
        '''check if PyGIWarning was not issued'''
        # for RHBZ#1450430
        Expect.expect_retval(CONNECTION, "grep PyGIWarning /tmp/repos.stderr", 1)

    def test_42_check_repo_sorting(self):
        '''check if repo lists are sorted'''
        # for RHBZ#1601478
        repolist_expected = sorted(CUSTOM_REPOS + self.yum_repo_ids)
        repolist_actual = RHUIManagerCLI.repo_list(CONNECTION, True).splitlines()
        nose.tools.eq_(repolist_expected, repolist_actual)

    def test_43_upload_semi_bad_cert(self):
        '''check that a partially invalid certificate can still be accepted'''
        # for RHBZ#1588931 & RHBZ#1584527
        # delete currently used certificates and repos first
        RHUIManager.remove_rh_certs(CONNECTION)
        for repo in CUSTOM_REPOS + self.yum_repo_ids:
            RHUIManagerCLI.repo_delete(CONNECTION, repo)
        repolist = RHUIManagerCLI.repo_list(CONNECTION, True)
        nose.tools.ok_(not repolist, msg="can't continue as some repos remain: %s" % repolist)
        # try uploading the cert now
        cert = "/tmp/extra_rhui_files/rhcert_partially_invalid.pem"
        if Util.cert_expired(CONNECTION, cert):
            raise nose.exc.SkipTest("The given certificate has already expired.")
        RHUIManagerCLI.cert_upload(CONNECTION,
                                   cert,
                                   "Red Hat Enterprise Linux 7 Server from RHUI")
        # the RHUI log must contain the fact that an invalid path was found in the cert
        Expect.ping_pong(CONNECTION, "tail /root/.rhui/rhui.log", "Invalid entitlement path")
        RHUIManager.remove_rh_certs(CONNECTION)

    @staticmethod
    def test_44_upload_empty_cert():
        '''check that an empty certificate is rejected (no traceback)'''
        # for RHBZ#1497028
        cert = "/tmp/extra_rhui_files/rhcert_empty.pem"
        if Util.cert_expired(CONNECTION, cert):
            raise nose.exc.SkipTest("The given certificate has already expired.")
        RHUIManagerCLI.cert_upload(CONNECTION, cert, "does not contain any entitlements")

    def test_45_multi_repo_product(self):
        '''check that all repos in a multi-repo product get added'''
        # for RHBZ#1651638
        RHUIManagerCLI.cert_upload(CONNECTION, "/tmp/extra_rhui_files/rhcert_atomic.pem", "Atomic")
        RHUIManagerCLI.repo_add(CONNECTION, self.product_name)
        # wait a few seconds for the repos to actually get added
        time.sleep(10)
        repolist_actual = RHUIManagerCLI.repo_list(CONNECTION, True).splitlines()
        nose.tools.eq_(self.product_repos, repolist_actual)
        # ^ also checks if the repolist is sorted

    def test_99_cleanup(self):
        '''cleanup: remove repos and temporary files'''
        # better to remove the product repos here; if the comparison in the previous test fails,
        # the test can't continue and remove them
        for repo in self.product_repos:
            RHUIManagerCLI.repo_delete(CONNECTION, repo)
        RHUIManager.remove_rh_certs(CONNECTION)
        Expect.ping_pong(CONNECTION, "rm -rf /tmp/atomic_and_my* ; " +
                         "ls /tmp/atomic_and_my* 2>&1",
                         "No such file or directory")
        Expect.ping_pong(CONNECTION, "rm -f /tmp/repos.std{out,err} ; " +
                         "ls /tmp/repos.std{out,err} 2>&1",
                         "No such file or directory")
        Expect.ping_pong(CONNECTION, "rm -rf /tmp/%s* ; " % ALT_CONTENT_SRC_NAME +
                         "ls /tmp/%s* 2>&1" % ALT_CONTENT_SRC_NAME,
                         "No such file or directory")
        rmtree(TMPDIR)

    @staticmethod
    def teardown_class():
        '''
           announce the end of the test run
        '''
        print("*** Finished running %s. *** " % basename(__file__))
