""" RHUIManagerCLI functions """

import re
import time

import nose

from stitches.expect import Expect
from rhui3_tests_lib.util import Util

def _get_repo_status(connection, repo_name):
    '''
    get the status of the given repository
    '''
    Expect.enter(connection, "rhui-manager status")
    status = Expect.match(connection,
                          re.compile(".*" + Util.esc_parentheses(repo_name) +
                                     "[^A-Z]*([A-Za-z]*).*", re.DOTALL))[0]
    return status

class CustomRepoAlreadyExists(Exception):
    '''
    Raised if a custom repo with this ID already exists
    '''

class CustomRepoGpgKeyNotFound(Exception):
    '''
    Raised if the GPG key path to use with a custom repo is invalid
    '''

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
                         "Successfully added",
                         timeout=300)

    @staticmethod
    def repo_list(connection, ids_only=False, redhat_only=False, delimiter=""):
        '''
        show repos; can show IDs only, RH repos only, and accepts a delimiter
        '''
        cmd = "rhui-manager repo list"
        if ids_only:
            cmd += " --ids_only"
        if redhat_only:
            cmd += " --redhat_only"
        if delimiter:
            cmd += " --delimiter %s" % delimiter
        _, stdout, _ = connection.exec_command(cmd)
        with stdout as output:
            response = output.read().decode().strip()
        return response

    @staticmethod
    def repo_sync(connection, repo_id, repo_name):
        '''
        sync a repo
        '''
        Expect.ping_pong(connection,
                         "rhui-manager repo sync --repo_id " + repo_id,
                         "successfully scheduled for the next available timeslot")
        repo_status = _get_repo_status(connection, repo_name)
        while repo_status in ["Never", "Running", "Unknown"]:
            time.sleep(10)
            repo_status = _get_repo_status(connection, repo_name)
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
    def repo_create_custom(connection,
                           repo_id,
                           path="",
                           display_name="",
                           entitlement="",
                           legacy_md=False,
                           redhat_content=False,
                           protected=False,
                           gpg_public_keys=""):
        '''
        create a custom repo
        '''
        # compose the command
        cmd = "rhui-manager repo create_custom --repo_id %s" % repo_id
        if path:
            cmd += " --path %s" % path
        if display_name:
            cmd += " --display_name '%s'" % display_name
        if entitlement:
            cmd += " --entitlement %s" % entitlement
        if legacy_md:
            cmd += " --legacy_md"
        if redhat_content:
            cmd += " --redhat_content"
        if protected:
            cmd += " --protected"
        if gpg_public_keys:
            cmd += " --gpg_public_keys %s" % gpg_public_keys
        # get a list of invalid GPG key files (will be implicitly empty if that option isn't used)
        key_list = gpg_public_keys.split(",")
        bad_keys = [key for key in key_list if connection.recv_exit_status("test -f %s" % key)]
        # possible output (more or less specific):
        out = {"missing_options": "Usage:",
               "invalid_id": "Only.*valid in a repository ID",
               "repo_exists": "A repository with ID \"%s\" already exists" % repo_id,
               "bad_gpg": "The following files are unreadable:\r\n\r\n%s" % "\r\n".join(bad_keys),
               "success": "Successfully created repository \"%s\"" % (display_name or repo_id)}
        # run the command and see what happens
        Expect.enter(connection, cmd)
        state = Expect.expect_list(connection,
                                   [(re.compile(".*%s.*" % out["missing_options"], re.DOTALL), 1),
                                    (re.compile(".*%s.*" % out["invalid_id"], re.DOTALL), 2),
                                    (re.compile(".*%s.*" % out["repo_exists"], re.DOTALL), 3),
                                    (re.compile(".*%s.*" % out["bad_gpg"], re.DOTALL), 4),
                                    (re.compile(".*%s.*" % out["success"], re.DOTALL), 5)])
        if state == 1 or state == 2:
            raise ValueError("the given repo ID is unusable")
        if state == 3:
            raise CustomRepoAlreadyExists()
        if state == 4:
            raise CustomRepoGpgKeyNotFound()
        # make sure rhui-manager reported success
        nose.tools.assert_equal(state, 5)

    @staticmethod
    def repo_delete(connection, repo_id):
        '''
        delete the given repo
        '''
        Expect.expect_retval(connection, "rhui-manager repo delete --repo_id %s" % repo_id)

    @staticmethod
    def repo_add_errata(connection, repo_id, updateinfo):
        '''
        associate errata metadata with a repo
        '''
        Expect.expect_retval(connection,
                             "rhui-manager repo add_errata " +
                             "--repo_id %s --updateinfo %s" % (repo_id, updateinfo),
                             timeout=120)

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
    def repo_labels(connection):
        '''
        view repo labels in the RHUA; returns a list of the labels
        '''
        _, stdout, _ = connection.exec_command("rhui-manager client labels")
        with stdout as output:
            labels = output.read().decode().splitlines()
        return labels

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
    def client_rpm(connection, certdata, rpmdata, directory, unprotected_repos=None, proxy=""):
        '''
        generate a client configuration RPM
        The certdata argument must be a list, and two kinds of data are supported:
          * key path and cert path (full paths, starting with "/"), or
          * one or more repo labels and optionally an integer denoting the number of days the cert
            will be valid for; if unspecified, rhui-manager will use 365. In this case,
            a certificate will be generated on the fly.
        The rpmdata argument must be a list with one, two or three strings:
          * package name: the name for the RPM
          * package version: string denoting the version; if unspecified, rhui-manager will use 2.0
          * package release: string denoting the release; if unspecified, rhui-manager will use 1
        '''
        cmd = "rhui-manager client rpm"
        if certdata[0].startswith("/"):
            cmd += " --private_key %s --entitlement_cert %s" % (certdata[0], certdata[1])
        else:
            cmd += " --cert"
            if isinstance(certdata[-1], int):
                cmd += " --days %s" % certdata.pop()
            cmd += " --repo_label %s" % ",".join(certdata)
        cmd += " --rpm_name %s" % rpmdata[0]
        if len(rpmdata) > 1:
            cmd += " --rpm_version %s" % rpmdata[1]
            if len(rpmdata) > 2:
                cmd += " --rpm_release %s" % rpmdata[2]
            else:
                rpmdata.append("1")
        else:
            rpmdata.append("2.0")
            rpmdata.append("1")
        cmd += " --dir %s" % directory
        if unprotected_repos:
            cmd += " --unprotected_repos %s" % ",".join(unprotected_repos)
        if proxy:
            cmd += " --proxy %s" % proxy
        Expect.ping_pong(connection,
                         cmd,
                         "Location: %s/%s-%s/build/RPMS/noarch/%s-%s-%s.noarch.rpm" % \
                         (directory, rpmdata[0], rpmdata[1], rpmdata[0], rpmdata[1], rpmdata[2]))

    @staticmethod
    def client_content_source(connection, certdata, rpmdata, directory):
        '''
        generate an alternate source config rpm
        (very similar to client_rpm() -- see the usage described there)
        '''
        cmd = "rhui-manager client content_source"
        if certdata[0].startswith("/"):
            cmd += " --private_key %s --entitlement_cert %s" % (certdata[0], certdata[1])
        else:
            cmd += " --cert"
            if isinstance(certdata[-1], int):
                cmd += " --days %s" % certdata.pop()
            cmd += " --repo_label %s" % ",".join(certdata)
        cmd += " --rpm_name %s" % rpmdata[0]
        if len(rpmdata) > 1:
            cmd += " --rpm_version %s" % rpmdata[1]
        else:
            rpmdata.append("2.0")
        cmd += " --dir %s" % directory
        Expect.ping_pong(connection,
                         cmd,
                         "Location: %s/%s-%s/build/RPMS/noarch/%s-%s-1.noarch.rpm" % \
                         (directory, rpmdata[0], rpmdata[1], rpmdata[0], rpmdata[1]))

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
