""" RHUIManagerCLI functions """

import re
import time

import nose

from stitches.expect import Expect
from rhui3_tests_lib.util import Util

class RHUIManagerCLI(object):
    '''
    The RHUI manager command-line interface (shell commands to control the RHUA).
    '''
    @staticmethod
    def cert_upload(connection, certificate_file, test_string):
        '''
        upload a new or updated Red Hat content certificate
        '''
        Expect.ping_pong(connection,
                         "rhui-manager cert upload --cert " + certificate_file,
                         test_string)

    @staticmethod
    def cert_info(connection):
        '''
        check the validity of the certificate
        '''
        Expect.ping_pong(connection, "rhui-manager cert info", "Valid")

    @staticmethod
    def repo_unused(connection, repo):
        '''
        check if a repo specified by its product name is available
        '''
        Expect.ping_pong(connection, "rhui-manager repo unused", Util.esc_parentheses(repo))

    @staticmethod
    def cert_expiration(connection):
        '''
        check if the certificate expiration date is OK
        '''
        Expect.ping_pong(connection,
                         "rhui-manager status",
                         "Entitlement CA certificate expiration date.*OK")

    @staticmethod
    def repo_add(connection, repo):
        '''
        add a repo specified by its product name
        '''
        Expect.ping_pong(connection,
                         "rhui-manager repo add --product_name \"" + repo + "\"",
                         "Successfully added")

    @staticmethod
    def repo_add_by_repo(connection, repo_ids):
        '''
        add a repo specified by its ID
        '''
        Expect.ping_pong(connection,
                         "rhui-manager repo add_by_repo --repo_ids " + ",".join(repo_ids),
                         "Successfully added")

    @staticmethod
    def repo_list(connection, repo_id, repo_name):
        '''
        check if the given repo ID and name are listed
        '''
        Expect.ping_pong(connection,
                         "rhui-manager repo list",
                         repo_id + " *:: " + Util.esc_parentheses(repo_name))

    @staticmethod
    def get_repo_lists(connection):
        '''
        get repo lists; dict with two lists: Red Hat and custom, with nested [id, name] lists
        '''
        _, stdout, _ = connection.exec_command("rhui-manager repo list")
        with stdout as output:
            rawlist = output.read().decode().splitlines()

        # the first RH repo is on the 5th line (if there's a RH repo at all)
        first_rh_repo_index = 4
        # find the position of the last RH repo
        for index in range(first_rh_repo_index, len(rawlist) - 3):
            if rawlist[index] == "":
                last_rh_repo_index = index - 1
                break
        # the first custom repo is 4 lines below the last RH repo
        first_custom_repo_index = last_rh_repo_index + 4
        # the last custom repo is 2 lines above the end of the output
        last_custom_repo_index = len(rawlist) - 2

        # parse the repo IDs and names
        rhrepos = []
        for index in range(first_rh_repo_index, last_rh_repo_index + 1):
            tmplist = rawlist[index].split("::")
            rhrepos.append([tmplist[0].strip(), tmplist[1].strip()])
        customrepos = []
        for index in range(first_custom_repo_index, last_custom_repo_index + 1):
            tmplist = rawlist[index].split("::")
            customrepos.append([tmplist[0].strip(), tmplist[1].strip()])

        repodict = {"redhat": rhrepos, "custom": customrepos}
        return repodict

    @staticmethod
    def validate_repo_list(connection, repo_ids):
        '''
        check if only the given repo IDs are listed
        '''
        Expect.expect_retval(connection,
                             "rhui-manager repo list | " +
                             "grep -v 'ID.*Repository Name$' | grep :: | cut -d ' ' -f 1 | " +
                             "sort > /tmp/actual_repo_list && "
                             "echo \"" + "\n".join(sorted(repo_ids)) + "\" > "
                             "/tmp/expected_repo_list && " +
                             "cmp /tmp/actual_repo_list /tmp/expected_repo_list")
        Expect.ping_pong(connection,
                         "rm -f /tmp/*_repo_list ; ls /tmp/*_repo_list 2>&1",
                         "No such file or directory")

    @staticmethod
    def get_repo_status(connection, repo_name):
        '''
        (internally used) method to get the status of the given repository
        '''
        Expect.enter(connection, "rhui-manager status")
        status = Expect.match(connection,
                              re.compile(".*" + Util.esc_parentheses(repo_name) +
                                         "[^A-Z]*([A-Za-z]*).*", re.DOTALL))[0]
        return status

    @staticmethod
    def repo_sync(connection, repo_id, repo_name):
        '''
        sync a repo
        '''
        Expect.ping_pong(connection,
                         "rhui-manager repo sync --repo_id " + repo_id,
                         "successfully scheduled for the next available timeslot")
        repo_status = RHUIManagerCLI.get_repo_status(connection, repo_name)
        while repo_status in ["Never", "Running", "Unknown"]:
            time.sleep(10)
            repo_status = RHUIManagerCLI.get_repo_status(connection, repo_name)
        nose.tools.assert_equal(repo_status, "Success")

    @staticmethod
    def repo_info(connection, repo_id, repo_name):
        '''
        check if information about the given repo can be displayed
        '''
        Expect.ping_pong(connection,
                         "rhui-manager repo info --repo_id " + repo_id,
                         "Name: *" + Util.esc_parentheses(repo_name))

    @staticmethod
    def packages_list(connection, repo_id, package):
        '''
        check if a package is present in the repo
        '''
        Expect.ping_pong(connection, "rhui-manager packages list --repo_id " + repo_id, package)

    @staticmethod
    def packages_upload(connection, repo_id, package):
        '''
        upload a package to the custom repo
        '''
        Expect.ping_pong(connection,
                         "rhui-manager packages upload " +
                         "--repo_id %s --packages %s" % (repo_id, package),
                         package + " successfully uploaded")

    @staticmethod
    def repo_labels(connection, repo_label):
        '''
        check if the specified repo label is known
        '''
        Expect.ping_pong(connection, "rhui-manager client labels", repo_label)

    @staticmethod
    def client_cert(connection, repo_labels, name, days, directory):
        '''
        generate an entitlement certificate
        '''
        Expect.ping_pong(connection,
                         "rhui-manager client cert --repo_label %s " % ",".join(repo_labels) +
                         "--name %s --days %s --dir %s" % (name, str(days), directory),
                         "Entitlement certificate created at %s/%s.crt" % (directory, name))

    @staticmethod
    def client_rpm(connection, certdata, rpmdata, directory, unprotected_repos=""):
        '''
        generate a client configuration RPM
        '''
        cmd = "rhui-manager client rpm " + \
              "--private_key %s --entitlement_cert %s " % (certdata[0], certdata[1]) + \
              "--rpm_version %s --rpm_name %s " % (rpmdata[0], rpmdata[1]) + \
              "--dir %s" % (directory)
        if unprotected_repos:
            cmd += " --unprotected_repos " + ",".join(unprotected_repos)
        Expect.ping_pong(connection,
                         cmd,
                         "Location: %s/%s-%s/build/RPMS/noarch/%s-%s-1.noarch.rpm" % \
                         (directory, rpmdata[1], rpmdata[0], rpmdata[1], rpmdata[0]))

    @staticmethod
    def subscriptions_list(connection, what="registered", poolonly=False):
        '''
        list registered or available subscriptions, complete information or the pool ID only
        '''
        if what not in ["registered", "available"]:
            raise ValueError("Unsupported list: " + what)
        if poolonly:
            poolswitch = " --pool-only"
        else:
            poolswitch = ""
        _, stdout, _ = connection.exec_command("rhui-manager subscriptions list --" + what +
                                               poolswitch)
        with stdout as output:
            sub_list = output.read().decode().strip()
        # return the (decoded and stripped) output as is;
        # if "ESC" and some control characters are included, then RHBZ#1577052 has regressed
        return sub_list

    @staticmethod
    def subscriptions_register(connection, pool):
        '''
        register the subscription to RHUI
        '''
        Expect.expect_retval(connection, "rhui-manager subscriptions register --pool " + pool)

    @staticmethod
    def subscriptions_unregister(connection, pool):
        '''
        remove the subscription from RHUI
        '''
        Expect.expect_retval(connection, "rhui-manager subscriptions unregister --pool " + pool)
