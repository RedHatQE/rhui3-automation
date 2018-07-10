""" Test case for sosreport usage in RHUI """
# for RHBZ#1591027 and RHBZ#1578678

import logging
from os.path import basename, join
from shutil import rmtree
from tempfile import mkdtemp

import stitches
from stitches.expect import Expect

from rhui3_tests_lib.sos import Sos

logging.basicConfig(level=logging.DEBUG)

TMPDIR = mkdtemp()
SOSREPORT_FILELIST = join(TMPDIR, "sosreport_filelist")
SOSREPORT_LOCATION = join(TMPDIR, "sosreport_location")

CONNECTION_RHUA = stitches.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")
WANTED_FILES_RHUA = ["/etc/rhui-installer/answers.yaml",
                     "/etc/rhui/rhui-tools.conf",
                     "/root/.rhui/rhui.log",
                     "/var/log/kafo/configuration.log",
                     "/var/log/rhui-subscription-sync.log"]

def setup():
    '''
        announce the beginning of the test run
    '''
    print("*** Running %s: *** " % basename(__file__))

def test_00_rhui_subscription_sync():
    '''
        run the rhui-subscription-sync command on the RHUA node to ensure its log file exists
    '''
    # can't use expect_retval as the exit code can be 0 or 1 (sync is configured or unconfigured)
    Expect.ping_pong(CONNECTION_RHUA,
                     "rhui-subscription-sync ; echo ACK",
                     "ACK")

def test_01_rhua_sosreport_run():
    '''
        run sosreport on the RHUA node
    '''
    sosreport_location = Sos.run(CONNECTION_RHUA)
    with open(SOSREPORT_LOCATION, "w") as location:
        location.write(sosreport_location)

def test_02_rhua_fetch_filelist():
    '''
       fetch a list of files collected in the sosreport archive
    '''
    with open(SOSREPORT_LOCATION) as location:
        sosreport_file = location.read()
    sosreport_filelist = Sos.list_contents(CONNECTION_RHUA, sosreport_file)
    with open(SOSREPORT_FILELIST, "w") as filelist:
        filelist.write(sosreport_filelist)

def test_03_rhua_sosreport_check():
    '''
        check if the sosreport archive from the RHUA node contains the desired files
    '''
    with open(SOSREPORT_FILELIST) as filelist:
        sosreport_filelist = filelist.read()
    Sos.check_files_in_archive(WANTED_FILES_RHUA, sosreport_filelist)

def test_99_cleanup():
    '''
        clean up temporary files (the archive and its checksum file from the RHUA, local caches)
    '''
    with open(SOSREPORT_LOCATION) as location:
        sosreport_file = location.read()
    Expect.ping_pong(CONNECTION_RHUA,
                     "rm -f " + sosreport_file + "* ; " +
                     "ls " + sosreport_file + "* 2>&1",
                     "No such file or directory")
    rmtree(TMPDIR)

def teardown():
    '''
        announce the end of the test run
    '''
    print("*** Finished running %s. *** " % basename(__file__))
