import nose, stitches, logging
from stitches.expect import Expect

from os.path import basename

logging.basicConfig(level=logging.DEBUG)

connection=stitches.connection.Connection("rhua.example.com", "root", "/root/.ssh/id_rsa_test")

def setUp():
    print "*** Running %s: *** " % basename(__file__)

def test_01_install_wget():
    '''
        Make sure wget is installed on the RHUA
    '''
    Expect.expect_retval(connection, "yum -y install wget")

def test_02_rhui_3_for_rhel_6_check():
    '''
        Check if the RHUI 3 packages for RHEL 6 are available
    '''
    Expect.expect_retval(connection, "test $(wget -q -O - --certificate /tmp/extra_rhui_files/rhcert.pem --ca-certificate /etc/rhsm/ca/redhat-uep.pem https://cdn.redhat.com/content/dist/rhel/rhui/server/6/6Server/x86_64/rhui/3/os/Packages/ | grep -c \"A HREF.*\.rpm\") -gt 90")

def test_03_rhui_3_for_rhel_7_check():
    '''
        Check if the RHUI 3 packages for RHEL 7 are available
    '''
    Expect.expect_retval(connection, "test $(wget -q -O - --certificate /tmp/extra_rhui_files/rhcert.pem --ca-certificate /etc/rhsm/ca/redhat-uep.pem https://cdn.redhat.com/content/dist/rhel/rhui/server/7/7Server/x86_64/rhui/3/os/Packages/ | grep -c \"A HREF.*\.rpm\") -gt 90")

def tearDown():
    print "*** Finished running %s. *** " % basename(__file__)
