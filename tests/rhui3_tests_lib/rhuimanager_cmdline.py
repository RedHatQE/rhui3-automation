""" RHUIManagerCLI functions """

from os.path import basename, join
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
    status = Expect.match(connection, re.compile(".*%s[^A-Z]*([A-Za-z]*).*" % re.escape(repo_name),
                                                 re.DOTALL))[0]
    return status

def _ent_list(stdout):
    '''
    return a list of entitlements based on the given output (produced by cert upload/info)
    '''
    response = stdout.read().decode()
    lines = list(map(str.lstrip, str(response).splitlines()))
    # there should be a header in the output, with status
    try:
        status = Util.uncolorify(lines[2])
    except IndexError:
        raise RuntimeError("Unexpected output: %s" % response)
    if status == "Valid":
        # only pay attention to lines containing products
        # (which are non-empty lines below the header, without expriration and file name info)
        entitlements = [line for line in lines[3:] if line and not line.startswith("Expiration")]
        return entitlements
    if status in ("Expired", "No Red Hat entitlements found."):
        # return an empty list
        return []
    # if we're here, there's another problem with the entitlements/output
    raise RuntimeError("An error occurred: %s" % response)

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
    def cert_upload(connection, cert="/tmp/extra_rhui_files/rhcert.pem"):
        '''
        upload a new or updated Red Hat content certificate and return a list of valid entitlements
        '''
        # get the complete output and split it into (left-stripped) lines
        _, stdout, _ = connection.exec_command("rhui-manager cert upload --cert %s" % cert)
        return _ent_list(stdout)

    @staticmethod
    def cert_info(connection):
        '''
        return a list of valid entitlements (if any)
        '''
        _, stdout, _ = connection.exec_command("rhui-manager cert info")
        return _ent_list(stdout)

    @staticmethod
    def repo_unused(connection, by_repo_id=False):
        '''
        return a list of repos that are entitled but not added to RHUI
        '''
        # beware: if using by_repo_id, products will be followed by one or more repo IDs
        # on separate lines that start with two spaces
        cmd = "rhui-manager repo unused"
        if by_repo_id:
            cmd += " --by_repo_id"
        _, stdout, _ = connection.exec_command(cmd)
        response = stdout.read().decode().splitlines()
        # return everything but the first four lines, which contain headers
        return response[4:]

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
        response = stdout.read().decode().strip()
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
    def repo_info(connection, repo_id):
        '''
        return a dictionary containing information about the given repo
        '''
        _, stdout, _ = connection.exec_command("rhui-manager repo info --repo_id %s" % repo_id)
        all_lines = stdout.read().decode().splitlines()
        if all_lines[0] == "repository %s was not found" % repo_id:
            raise RuntimeError("Invalid repository ID.")
        info_pair_list = [line.split(":", 1) for line in all_lines]
        info_dict = {i[0].replace(" ", "").lower(): i[1].lstrip() for i in info_pair_list}
        return info_dict

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
        if state in (1, 2):
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
    def repo_add_comps(connection, repo_id, comps):
        '''
        associate comps metadata with a repo
        '''
        Expect.expect_retval(connection,
                             "rhui-manager repo add_comps " +
                             "--repo_id %s --comps %s" % (repo_id, comps),
                             timeout=120)

    @staticmethod
    def packages_list(connection, repo_id):
        '''
        return a list of packages present in the repo
        '''
        _, stdout, _ = connection.exec_command("rhui-manager packages list --repo_id %s" % repo_id)
        return stdout.read().decode().splitlines()

    @staticmethod
    def packages_remote(connection, repo_id, url):
        '''
        upload packages from a remote URL to a custom repository
        '''
        cmd = "rhui-manager packages remote --repo_id %s --url %s" % (repo_id, url)
        _, stdout, _ = connection.exec_command(cmd)
        output = stdout.read().decode().splitlines()
        successfully_uploaded_packages = [basename(line.split()[0]) for line in output \
                                          if line.endswith("successfully uploaded")]
        if not successfully_uploaded_packages:
            raise RuntimeError("\n".join(output) or "no output from '%s'" % cmd)
        successfully_uploaded_packages.sort()
        expected_packages = [basename(url)] if url.endswith(".rpm") else Util.get_rpm_links(url)
        expected_packages.sort()
        nose.tools.eq_(successfully_uploaded_packages, expected_packages)

    @staticmethod
    def packages_upload(connection, repo_id, path):
        '''
        upload a package or a directory with packages to the custom repo
        '''
        cmd = "rhui-manager packages upload --repo_id %s --packages %s" % (repo_id, path)
        _, stdout, _ = connection.exec_command(cmd)
        output = stdout.read().decode().splitlines()
        successfully_uploaded_packages = [line.split()[0] for line in output \
                                          if line.endswith("successfully uploaded")]
        if not successfully_uploaded_packages:
            raise RuntimeError("\n".join(output) or "no output from '%s'" % cmd)
        successfully_uploaded_packages.sort()
        path_type = Util.get_file_type(connection, path)
        if path_type == "regular file":
            expected_packages = [path]
        elif path_type == "directory":
            expected_packages = [join(path, rpm) for rpm in Util.get_rpms_in_dir(connection, path)]
        else:
            expected_packages = []
        nose.tools.eq_(successfully_uploaded_packages, expected_packages)

    @staticmethod
    def client_labels(connection):
        '''
        view repo labels in the RHUA; returns a list of the labels
        '''
        _, stdout, _ = connection.exec_command("rhui-manager client labels")
        labels = stdout.read().decode().splitlines()
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
        list registered or available subscriptions, {labels: pool IDs} or [pool IDs]
        '''
        allowed_lists = ["registered", "available"]
        if what not in allowed_lists:
            raise ValueError("Unsupported list: '%s'. Use one of: %s." % (what, allowed_lists))
        cmd = "rhui-manager subscriptions list --%s" % what
        if poolonly:
            cmd += " --pool-only"
        _, stdout, _ = connection.exec_command(cmd)
        subs = stdout.read().decode().splitlines()
        # if "ESC" and some control characters are included, then RHBZ#1577052 has regressed
        # if only pool IDs are requested, return their list as read from the output;
        # otherwise, create and return a dict with subscription names and corresponding pool IDs
        if poolonly:
            return subs
        labels = [l.replace("  Label: ", "") for l in subs if l.startswith("  Label")]
        poolids = [p.replace("  Pool ID: ", "") for p in subs if p.startswith("  Pool")]
        sub_dict = dict(zip(labels, poolids))
        return sub_dict

    @staticmethod
    def subscriptions_register(connection, pool):
        '''
        register the subscription to RHUI
        '''
        Expect.expect_retval(connection, "rhui-manager subscriptions register --pool %s" % pool)

    @staticmethod
    def subscriptions_unregister(connection, pool):
        '''
        remove the subscription from RHUI
        '''
        Expect.expect_retval(connection, "rhui-manager subscriptions unregister --pool %s " % pool)
