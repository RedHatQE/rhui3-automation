""" Test case for sosreport usage in RHUI """
# for RHBZ#1591027 and RHBZ#1578678

import logging
from os.path import basename, join
from shutil import rmtree
from tempfile import mkdtemp

import stitches
from stitches.expect import Expect

from rhui3_tests_lib.helpers import Helpers
from rhui3_tests_lib.rhuimanager import RHUIManager
from rhui3_tests_lib.rhuimanager_instance import RHUIManagerInstance
from rhui3_tests_lib.sos import Sos

logging.basicConfig(level=logging.DEBUG)

TMPDIR = mkdtemp()
SOSREPORT_LOCATION_RHUA = join(TMPDIR, "sosreport_location_rhua")
SOSREPORT_LOCATION_CDS = join(TMPDIR, "sosreport_location_cds")

CONNECTION_RHUA = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
CONNECTION_CDS = stitches.Connection("cds01.example.com", "root", "/root/.ssh/id_rsa_test")

WANTED_FILES_RHUA = ["/etc/rhui-installer/answers.yaml",
                     "/etc/rhui/rhui-tools.conf",
                     "/root/.rhui/rhui.log",
                     "/var/log/kafo/configuration.log",
                     "/var/log/rhui-subscription-sync.log"]
WANTED_FILES_CDS = ["/etc/httpd/conf.d/03-crane.conf",
                    "/etc/httpd/conf.d/25-cds.example.com.conf",
                    "/etc/pulp/",
                    "/var/log/httpd/cds.example.com_access_ssl.log",
                    "/var/log/httpd/cds.example.com_error_ssl.log"]

CMD_RHUA = "rhui-manager status"
CMD_CDS = "ls -lR /var/lib/rhui/remote_share"
WANTED_FILES_RHUA.append(Helpers.encode_sos_command(CMD_RHUA))
WANTED_FILES_CDS.append(Helpers.encode_sos_command(CMD_CDS))

def setup():
    '''
        announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_00_rhui_init():
    '''
        add a CDS and run rhui-subscription-sync to ensure their log files exist
    '''
    #  use initial_run first to ensure we're logged in to rhui-manager
    RHUIManager.initial_run(CONNECTION_RHUA)
    RHUIManagerInstance.add_instance(CONNECTION_RHUA, "cds", "cds01.example.com")
    # can't use expect_retval as the exit code can be 0 or 1 (sync is configured or unconfigured)
    Expect.ping_pong(CONNECTION_RHUA,
                     "rhui-subscription-sync ; echo ACK",
                     "ACK")

def test_01_rhua_check_sos_script():
    '''
        check if the RHUI sosreport script is available on the RHUA node
    '''
    Sos.check_rhui_sos_script(CONNECTION_RHUA)

def test_02_rhua_sosreport_run():
    '''
        run sosreport on the RHUA node
    '''
    sosreport_location = Sos.run(CONNECTION_RHUA)
    with open(SOSREPORT_LOCATION_RHUA, "w") as location:
        location.write(sosreport_location)

def test_03_rhua_sosreport_check():
    '''
        check if the sosreport archive from the RHUA node contains the desired files
    '''
    with open(SOSREPORT_LOCATION_RHUA) as location:
        sosreport_location = location.read()
    Sos.check_files_in_archive(CONNECTION_RHUA, WANTED_FILES_RHUA, sosreport_location)

def test_04_cds_check_sos_script():
    '''
        check if the RHUI sosreport script is available on the CDS node
    '''
    # for RHBZ#1596296
    Sos.check_rhui_sos_script(CONNECTION_CDS)

def test_05_cds_sosreport_run():
    '''
        run sosreport on the CDS node
    '''
    sosreport_location = Sos.run(CONNECTION_CDS)
    with open(SOSREPORT_LOCATION_CDS, "w") as location:
        location.write(sosreport_location)

def test_06_cds_sosreport_check():
    '''
        check if the sosreport archive from the CDS node contains the desired files
    '''
    with open(SOSREPORT_LOCATION_CDS) as location:
        sosreport_location = location.read()
    Sos.check_files_in_archive(CONNECTION_CDS, WANTED_FILES_CDS, sosreport_location)

def test_99_cleanup():
    '''
        delete the archives and their checksum files, local caches; remove CDS
    '''
    with open(SOSREPORT_LOCATION_RHUA) as location:
        sosreport_file = location.read()
    Expect.ping_pong(CONNECTION_RHUA,
                     "rm -f " + sosreport_file + "* ; " +
                     "ls " + sosreport_file + "* 2>&1",
                     "No such file or directory")
    with open(SOSREPORT_LOCATION_CDS) as location:
        sosreport_file = location.read()
    Expect.ping_pong(CONNECTION_CDS,
                     "rm -f " + sosreport_file + "* ; " +
                     "ls " + sosreport_file + "* 2>&1",
                     "No such file or directory")
    rmtree(TMPDIR)
    RHUIManagerInstance.delete(CONNECTION_RHUA, "cds", ["cds01.example.com"])

def teardown():
    '''
        announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
