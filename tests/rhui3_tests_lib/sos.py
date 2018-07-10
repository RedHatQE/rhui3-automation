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
    def check_files_in_archive(filelist, archive):
        '''
            check if the files in the given filelist are collected in the given archive
        '''
        missing_files = []
        for wanted_file in filelist:
            if wanted_file + "\n" not in archive:
                missing_files.append(wanted_file)
        nose.tools.ok_(not missing_files,
                       msg="Not found in the archive: " + ", ".join(missing_files))
