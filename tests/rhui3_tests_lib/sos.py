"""Sos in RHUI"""

import re

import nose
from stitches.expect import Expect

class Sos(object):
    """Sos handling for RHUI"""
    @staticmethod
    def check_rhui_sos_script(connection):
        '''
            check if the RHUI sosreport script is available
        '''
        Expect.expect_retval(connection, "test -f /usr/share/rh-rhua/rhui-debug.py")

    @staticmethod
    def run(connection):
        """run the sosreport command"""
        # first make sure the sos package is installed
        Expect.expect_retval(connection, "yum -y install sos", timeout=30)
        # now run sosreport with only the RHUI plug-in enabled, return the tarball location
        _, stdout, _ = connection.exec_command("sosreport -o rhui --batch | " +
                                               "grep -A1 '^Your sosreport' | " +
                                               "tail -1")
        location = stdout.read().decode().strip()
        return location

    @staticmethod
    def check_files_in_archive(connection, filelist, archive):
        """check if the files in the given filelist are collected in the given archive"""
        # make sure the archive exists
        if connection.recv_exit_status("test -f %s" % archive):
            raise OSError("%s does not exist" % archive)
        # read the contents of the archive, and check if each file from the filelist is there
        # must strip the path in front of the real root directory; the archive contains files like:
        # sosreport-HOST-DATE-HASH/sos_commands/rhui/rhui-debug-DATE-TIME/etc/pulp/repo_auth.conf
        # while the given filelist contains actual paths like /etc/pulp/repo_auth.conf
        pattern = "^.*/rhui-debug[^/]+"
        _, stdout, _ = connection.exec_command("tar tf %s" % archive)
        archive_filelist_raw = stdout.read().decode().splitlines()
        archive_filelist = [re.sub(pattern, "", path) for path in archive_filelist_raw]
        missing_files = [f for f in filelist if f not in archive_filelist]
        nose.tools.ok_(not missing_files,
                       msg="Not found in the archive: %s" % missing_files)
