""" Sos in RHUI """

import nose
from stitches.expect import Expect

class Sos(object):
    '''
        Sos handling for RHUI
    '''
    @staticmethod
    def run(connection):
        '''
            run the sosreport command
        '''
        # first make sure the sos package is installed
        Expect.expect_retval(connection, "yum -y install sos", timeout=30)
        # now run sosreport with only the RHUI plug-in enabled, return the tarball location
        _, stdout, _ = connection.exec_command("sosreport -o rhui --batch | " +
                                               "grep -A1 '^Your sosreport' | " +
                                               "tail -1")
        with stdout as output:
            location = output.read().decode().strip()
        return location

    @staticmethod
    def list_contents(connection, location):
        '''
            list the files in the sosreport tarball stored in the given location (path)
        '''
        _, stdout, _ = connection.exec_command("tar tf " + location)
        with stdout as output:
            filelist = output.read().decode().strip()
        return filelist

    @staticmethod
    def check_file_in_archive(wanted_file, archive):
        '''
            check if the given file is collected in the given archive
        '''
        nose.tools.ok_(wanted_file + "\n" in archive, msg=wanted_file + " was not collected")
