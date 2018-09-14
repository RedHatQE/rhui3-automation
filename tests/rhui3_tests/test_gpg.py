'''Tests for working with a custom GPG key in a custom repo'''

from os.path import basename

import logging
import stitches
from stitches.expect import Expect

from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_client import RHUIManagerClient
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.rhuimanager_repo import RHUIManagerRepo
from rhui3_tests_lib.util import Util

logging.basicConfig(level=logging.DEBUG)

RHUA = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
CLI = stitches.Connection("cli01.example.com", "root", "/root/.ssh/id_rsa_test")

REPO = "custom_gpg"
SIG = "9f6e93a2"
SIGNED_PACKAGE = "rhui-rpm-upload-trial"
UNSIGNED_PACKAGE = "rhui-rpm-upload-test"

def setup():
    '''
       announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_01_initial_run():
    '''
        log in to RHUI
    '''
    RHUIManager.initial_run(RHUA)

def test_02_add_cds():
    '''
        add a CDS
    '''
    RHUIManagerInstance.add_instance(RHUA, "cds", "cds01.example.com")

def test_03_add_hap():
    '''
        add an HAProxy Load-balancer
    '''
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
        upload a signed and an unsigned package to the custom repo
    '''
    RHUIManagerRepo.upload_content(RHUA,
                                   [REPO],
                                   "/tmp/extra_rhui_files/%s-1-1.noarch.rpm" % SIGNED_PACKAGE)
    RHUIManagerRepo.upload_content(RHUA,
                                   [REPO],
                                   "/tmp/extra_rhui_files/%s-1-1.noarch.rpm" % UNSIGNED_PACKAGE)

def test_06_display_detailed_info():
    '''
        check detailed information on the repo
    '''
    RHUIManagerRepo.check_detailed_information(RHUA,
                                               [REPO, REPO],
                                               [True, True],
                                               [True, "test_gpg_key", False],
                                               2)

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
    Expect.expect_retval(CLI, "rpm -qi %s | grep -q ^Signature.*%s$" % (SIGNED_PACKAGE, SIG))

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

def test_99_cleanup():
    '''
       clean up
    '''
    RHUIManagerRepo.delete_all_repos(RHUA)
    RHUIManagerInstance.delete(RHUA, "loadbalancers", ["hap01.example.com"])
    RHUIManagerInstance.delete(RHUA, "cds", ["cds01.example.com"])
    Expect.expect_retval(RHUA, "rm -rf /tmp/%s*" % REPO)
    Util.remove_rpm(CLI, [SIGNED_PACKAGE, "gpg-pubkey-%s" % SIG, REPO])

def teardown():
    '''
       announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
