'''Tests for working with a custom GPG key in a custom repo'''

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

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
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

REPO = "custom_gpg"
SIG = "9f6e93a2"
SIGNED_PACKAGE = "rhui-rpm-upload-trial"
UNSIGNED_PACKAGE = "rhui-rpm-upload-test"
SIGNED_PACKAGE_SIG2 = "rhui-rpm-upload-tryout"
CUSTOM_RPMS_DIR = "/tmp/extra_rhui_files"

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_initial_run():
    '''
        log in to RHUI
    '''
    if not getenv("RHUISKIPSETUP"):
        RHUIManager.initial_run(RHUA)

def test_02_add_cds():
    '''
        add a CDS
    '''
    if not getenv("RHUISKIPSETUP"):
        RHUIManagerInstance.add_instance(RHUA, "cds", "cds01.example.com")

def test_03_add_hap():
    '''
        add an HAProxy Load-balancer
    '''
    if not getenv("RHUISKIPSETUP"):
        RHUIManagerInstance.add_instance(RHUA, "loadbalancers", "hap01.example.com")

def test_04_create_custom_repo():
    '''
        add a custom repo using a custom GPG key
    '''
    RHUIManagerRepo.add_custom_repo(RHUA,
                                    REPO,
                                    redhat_gpg="n",
                                    custom_gpg="/tmp/extra_rhui_files/test_gpg_key")

def test_05_upload_to_custom_repo():
    '''
        upload an unsigned and two differently signed packages to the custom repo
    '''
    avail_rpm_names = [pkg.rsplit('-', 2)[0] for pkg in Util.get_rpms_in_dir(RHUA,
                                                                             CUSTOM_RPMS_DIR)]
    nose.tools.eq_(avail_rpm_names, sorted([SIGNED_PACKAGE, UNSIGNED_PACKAGE, SIGNED_PACKAGE_SIG2]),
                   msg="Failed to find the packages to upload. Got: %s" % avail_rpm_names)
    RHUIManagerRepo.upload_content(RHUA, [REPO], CUSTOM_RPMS_DIR)

def test_06_display_detailed_info():
    '''
        check detailed information on the repo
    '''
    RHUIManagerRepo.check_detailed_information(RHUA,
                                               [REPO, REPO],
                                               [True, True],
                                               [True, "test_gpg_key", False],
                                               3)

def test_07_generate_ent_cert():
    '''
        generate an entitlement certificate
    '''
    RHUIManagerClient.generate_ent_cert(RHUA, [REPO], REPO, "/tmp")

def test_08_create_cli_rpm():
    '''
        create a client configuration RPM
    '''
    RHUIManagerClient.create_conf_rpm(RHUA,
                                      "/tmp",
                                      "/tmp/%s.crt" % REPO,
                                      "/tmp/%s.key" % REPO,
                                      REPO)

def test_09_rm_amazon_rhui_cf_rpm():
    '''
       remove Amazon RHUI configuration from the client
    '''
    Util.remove_amazon_rhui_conf_rpm(CLI)

def test_10_install_conf_rpm():
    '''
       install the client configuration RPM
    '''
    Util.install_pkg_from_rhua(RHUA,
                               CLI,
                               "/tmp/%s-2.0/build/RPMS/noarch/%s-2.0-1.noarch.rpm" % (REPO, REPO))

def test_11_install_signed_pkg():
    '''
       install the signed package from the custom repo (will import the GPG key)
    '''
    Expect.expect_retval(CLI, "yum -y install %s" % SIGNED_PACKAGE)

def test_12_check_gpg_sig():
    '''
       check the signature in the installed package
    '''
    Expect.expect_retval(CLI, "rpm -qi %s | grep ^Signature.*%s$" % (SIGNED_PACKAGE, SIG))

def test_13_check_gpg_pubkey():
    '''
       check if the public GPG key was imported
    '''
    Expect.expect_retval(CLI, "rpm -q gpg-pubkey-%s" % SIG)

def test_14_install_unsigned_pkg():
    '''
       try installing the unsigned package, should not work
    '''
    Expect.ping_pong(CLI,
                     "yum -y install %s" % UNSIGNED_PACKAGE,
                     "Package %s-1-1.noarch.rpm is not signed" % UNSIGNED_PACKAGE)
    Expect.expect_retval(CLI, "rpm -q %s" % UNSIGNED_PACKAGE, 1)

def test_15_install_2nd_signed_pkg():
    '''
       try installing the package signed with the key unknown to the client, should not work
    '''
    rhel = Util.get_rhel_version(CLI)["major"]
    if rhel <= 7:
        output = "The GPG keys.*%s.*are not correct for this package" % REPO
    else:
        output = "Public key for %s-1-1.noarch.rpm is not installed" % SIGNED_PACKAGE_SIG2
    Expect.ping_pong(CLI,
                     "yum -y install %s" % SIGNED_PACKAGE_SIG2,
                     output)
    Expect.expect_retval(CLI, "rpm -q %s" % SIGNED_PACKAGE_SIG2, 1)

def test_99_cleanup():
    '''
       clean up
    '''
    Util.remove_rpm(CLI, [SIGNED_PACKAGE, "gpg-pubkey-%s" % SIG, REPO])
    rhel = Util.get_rhel_version(CLI)["major"]
    if rhel <= 7:
        cache = "/var/cache/yum/x86_64/%sServer/rhui-custom-%s/" % (rhel, REPO)
    else:
        cache = "/var/cache/dnf/rhui-custom-%s*/" % REPO
    Expect.expect_retval(CLI, "rm -rf %s" % cache)
    RHUIManagerRepo.delete_all_repos(RHUA)
    Expect.expect_retval(RHUA, "rm -rf /tmp/%s*" % REPO)
    if not getenv("RHUISKIPSETUP"):
        RHUIManagerInstance.delete(RHUA, "loadbalancers", ["hap01.example.com"])
        RHUIManagerInstance.delete(RHUA, "cds", ["cds01.example.com"])

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
