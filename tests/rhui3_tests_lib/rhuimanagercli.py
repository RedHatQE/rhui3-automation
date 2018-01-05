""" RHUIManagerCLI functions """

import nose, re, time

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
        Expect.ping_pong(connection, "rhui-manager cert upload --cert " + certificate_file, test_string)

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
        Expect.ping_pong(connection, "rhui-manager status", "Entitlement CA certificate expiration date.*OK")

    @staticmethod
    def repo_add(connection, repo):
        '''
        add a repo specified by its product name
        '''
        Expect.ping_pong(connection, "rhui-manager repo add --product_name \"" + repo + "\"", "Successfully added")

    @staticmethod
    def repo_add_by_repo(connection, repo_ids):
        '''
        add a repo specified by its ID
        '''
        Expect.ping_pong(connection, "rhui-manager repo add_by_repo --repo_ids " + ",".join(repo_ids), "Successfully added")

    @staticmethod
    def repo_list(connection, repo_id, repo_name):
        '''
        check if the given repo ID and name are listed
        '''
        Expect.ping_pong(connection, "rhui-manager repo list", repo_id + " *:: " + Util.esc_parentheses(repo_name))

    @staticmethod
    def validate_repo_list(connection, repo_ids):
        '''
        check if only the given repo IDs are listed
        '''
        Expect.expect_retval(connection, "rhui-manager repo list | grep -v 'ID.*Repository Name$' | grep :: | cut -d ' ' -f 1 | sort > /tmp/actual_repo_list && echo \"" + "\n".join(sorted(repo_ids)) + "\" > /tmp/expected_repo_list && cmp /tmp/actual_repo_list /tmp/expected_repo_list")
        Expect.ping_pong(connection, "rm -f /tmp/*_repo_list ; ls /tmp/*_repo_list 2>&1", "No such file or directory")

    @staticmethod
    def get_repo_status(connection, repo_name):
        '''
        (internally used) method to get the status of the given repository
        '''
        Expect.enter(connection, "rhui-manager status")
        status = Expect.match(connection, re.compile(".*" + Util.esc_parentheses(repo_name) + "[^A-Z]*([A-Za-z]*).*", re.DOTALL))[0]
        return status

    @staticmethod
    def repo_sync(connection, repo_id, repo_name):
        '''
        sync a repo
        '''
        Expect.ping_pong(connection, "rhui-manager repo sync --repo_id " + repo_id, "successfully scheduled for the next available timeslot")
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
        Expect.ping_pong(connection, "rhui-manager repo info --repo_id " + repo_id, "Name: *" + Util.esc_parentheses(repo_name))

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
        Expect.ping_pong(connection, "rhui-manager packages upload --repo_id " + repo_id + " --packages " + package, package + " successfully uploaded")

    @staticmethod
    def repo_labels(connection, repo_label):
        '''
        check if the specified repo label is known
        '''
        Expect.ping_pong(connection, "rhui-manager client labels", repo_label)

    @staticmethod
    def client_cert(connection, repo_labels, name, days, dir):
        '''
        generate an entitlement certificate
        '''
        Expect.ping_pong(connection, "rhui-manager client cert --repo_label " + ",".join(repo_labels) + " --name " + name + " --days " + str(days) + " --dir " + dir, "Entitlement certificate created at " + dir + "/" + name + ".crt")

    @staticmethod
    def client_rpm(connection, private_key, entitlement_cert, rpm_version, rpm_name, dir, unprotected_repos=[]):
        '''
        generate a client configuration RPM
        '''
        Expect.ping_pong(connection, "rhui-manager client rpm --private_key " + private_key + " --entitlement_cert " + entitlement_cert + " --rpm_version " + rpm_version + " --rpm_name " + rpm_name + " --dir " + dir + "%s" %(" --unprotected_repos " + ",".join(unprotected_repos) if len(unprotected_repos) > 0 else ""), "RPMs can be found at " + dir)
