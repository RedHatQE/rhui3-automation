"""Functions for Yum Commands and Repodata Handling"""

from stitches.expect import Expect
import xmltodict

from rhui3_tests_lib.rhuimanager_cmdline import RHUIManagerCLI

class Yummy():
    """various functions to test yum commands and repodata"""
    @staticmethod
    def repodata_location(connection, repo, datatype):
        """return the path to the repository file (on the RHUA) of the given data type"""
        # data types are : filelists, group, primary, updateinfo etc.
        base_path = "/var/lib/rhui/remote_share/published/yum/https/repos"
        relative_path = RHUIManagerCLI.repo_info(connection, repo)["relativepath"]
        repodata_file = "%s/%s/repodata/repomd.xml" % (base_path, relative_path)
        _, stdout, _ = connection.exec_command("cat %s " % repodata_file)
        repodata = xmltodict.parse(stdout.read())
        location_list = [data["location"]["@href"] for data in repodata["repomd"]["data"] \
                         if data["@type"] == datatype]
        if location_list:
            location = location_list[0]
            wanted_file = "%s/%s/%s" % (base_path, relative_path, location)
            return wanted_file
        return None

    @staticmethod
    def comps_xml_grouplist(connection, comps_xml, uservisible_only=True):
        """return a sorted list of yum groups in the given comps.xml file"""
        # by default, only groups with <uservisible>true</uservisible> are taken into account,
        # but those "invisible" can be included too, if requested
        _, stdout, _ = connection.exec_command("cat %s" % comps_xml)
        comps = xmltodict.parse(stdout.read())
        # in a multi-group comps.xml file, the groups are in a list,
        # whereas in a single-group file, the group is just a string
        if isinstance(comps["comps"]["group"], list):
            # get a list of name-visibility pairs first
            group_info = [[group["name"][0], group["uservisible"].lower() == "true"] \
                          for group in comps["comps"]["group"]]
            if uservisible_only:
                grouplist = [group[0] for group in group_info if group[1]]
            else:
                grouplist = [group[0] for group in group_info]
            return sorted(grouplist)
        if uservisible_only:
            if comps["comps"]["group"]["uservisible"].lower() == "true":
                return [comps["comps"]["group"]["name"][0]]
            return []
        return [comps["comps"]["group"]["name"][0]]

    @staticmethod
    def comps_xml_langpacks(connection, comps_xml):
        """return a list of name, package tuples for the langpacks from the given comps.xml file"""
        # or None if there are no langpacks
        _, stdout, _ = connection.exec_command("cat %s" % comps_xml)
        comps = xmltodict.parse(stdout.read())
        if comps["comps"]["langpacks"]:
            names_pkgs = [(match["@name"], match["@install"]) \
                          for match in comps["comps"]["langpacks"]["match"]]
            return names_pkgs
        return None

    @staticmethod
    def yum_grouplist(connection):
        """return a sorted list of yum groups available to the client"""
        # first clean metadata, which may contain outdated information
        Expect.expect_retval(connection, "yum clean all")
        # fetch the complete output from the command
        _, stdout, _ = connection.exec_command("yum grouplist")
        all_lines = stdout.read().decode().splitlines()
        # yum groups are on lines that start with three spaces
        grouplist = [line.strip() for line in all_lines if line.startswith("   ")]
        return sorted(grouplist)

    @staticmethod
    def yum_group_packages(connection, group):
        """return a sorted list of packages available to the client in the given yum group"""
        # fetch the complete output from the command
        _, stdout, _ = connection.exec_command("yum groupinfo '%s'" % group)
        all_lines = stdout.read().decode().splitlines()
        # packages are on lines that start with three spaces
        packagelist = [line.strip() for line in all_lines if line.startswith("   ")]
        # in addition, the package names can start with +, -, or = depending on the status
        # (see man yum -> groups)
        # so, let's remove such signs if they're present
        packagelist = [pkg[1:] if pkg[0] in ["+", "-", "="] else pkg for pkg in packagelist]
        return sorted(packagelist)
