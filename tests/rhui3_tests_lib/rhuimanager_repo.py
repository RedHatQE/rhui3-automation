""" RHUIManager Repo functions """

from os.path import basename
import re
import time

import nose

from stitches.expect import CTRL_C, Expect

from rhui3_tests_lib.rhuimanager import RHUIManager


class AlreadyExistsError(Exception):
    '''
    To be raised if a custom repo already exists with this name.
    '''
    pass

class RHUIManagerRepo(object):
    '''
    Represents -= Repository Management =- RHUI screen
    '''
    @staticmethod
    def add_custom_repo(connection,
                        reponame,
                        displayname="",
                        path="",
                        checksum_alg="1",
                        entitlement="y",
                        entitlement_path="",
                        redhat_gpg="y",
                        custom_gpg=None):
        '''
        create a new custom repository
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "c")
        Expect.expect(connection, "Unique ID for the custom repository.*:")
        Expect.enter(connection, reponame)
        checklist = ["ID: " + reponame]
        state = Expect.expect_list(connection,
                                   [(re.compile(".*Display name for the custom repository.*:",
                                                re.DOTALL),
                                     1),
                                    (re.compile(".*repository.*already exists.*Unique ID.*:",
                                                re.DOTALL),
                                     2)])
        if state == 1:
            Expect.enter(connection, displayname)
            if displayname != "":
                checklist.append("Name: " + displayname)
            else:
                checklist.append("Name: " + reponame)
            Expect.expect(connection, "Unique path at which the repository will be served.*:")
            Expect.enter(connection, path)
            if path != "":
                path_real = path
            else:
                path_real = reponame
            checklist.append("Path: " + path_real)
            Expect.expect(connection, "Enter value.*:")
            Expect.enter(connection, checksum_alg)
            Expect.expect(connection,
                          "Should the repository require an entitlement certificate " +
                          r"to access\? \(y/n\)")
            Expect.enter(connection, entitlement)
            if entitlement == "y":
                Expect.expect(connection,
                              "Path that should be used when granting an entitlement " +
                              "for this repository.*:")
                Expect.enter(connection, entitlement_path)
                if entitlement_path != "":
                    checklist.append("Entitlement: " + entitlement_path)
                else:
                    educated_guess, replace_count = re.subn("(i386|x86_64)", "$basearch", path_real)
                    if replace_count > 1:
                        # bug 815975
                        educated_guess = path_real
                    checklist.append("Entitlement: " + educated_guess)
            Expect.expect(connection, r"packages are signed by a GPG key\? \(y/n\)")
            if redhat_gpg == "y" or custom_gpg:
                Expect.enter(connection, "y")
                checklist.append("GPG Check Yes")
                Expect.expect(connection,
                              "Will the repository be used to host any " +
                              r"Red Hat GPG signed content\? \(y/n\)")
                Expect.enter(connection, redhat_gpg)
                if redhat_gpg == "y":
                    checklist.append("Red Hat GPG Key: Yes")
                else:
                    checklist.append("Red Hat GPG Key: No")
                Expect.expect(connection,
                              "Will the repository be used to host any " +
                              r"custom GPG signed content\? \(y/n\)")
                if custom_gpg:
                    Expect.enter(connection, "y")
                    Expect.expect(connection,
                                  "Enter the absolute path to the public key of the GPG keypair:")
                    Expect.enter(connection, custom_gpg)
                    Expect.expect(connection,
                                  r"Would you like to enter another public key\? \(y/n\)")
                    Expect.enter(connection, "n")
                    checklist.append("Custom GPG Keys: '" + custom_gpg + "'")
                else:
                    Expect.enter(connection, "n")
                    checklist.append("Custom GPG Keys: (None)")
            else:
                Expect.enter(connection, "n")
                checklist.append("GPG Check No")
                checklist.append("Red Hat GPG Key: No")

            RHUIManager.proceed_with_check(connection,
                                           "The following repository will be created:",
                                           checklist)
            RHUIManager.quit(connection, "Successfully created repository *")
        else:
            Expect.enter(connection, CTRL_C)
            RHUIManager.quit(connection)
            raise AlreadyExistsError()

    @staticmethod
    def add_rh_repo_all(connection):
        '''
        add a new Red Hat content repository (All in Certificate)
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "a")
        Expect.expect(connection, "Import Repositories:.*to abort:", 660)
        Expect.enter(connection, "1")
        RHUIManager.proceed_without_check(connection)
        RHUIManager.quit(connection, "", 180)

    @staticmethod
    def add_rh_repo_by_product(connection, productlist):
        '''
        add a new Red Hat content repository (By Product)
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "a")
        Expect.expect(connection, "Import Repositories:.*to abort:", 660)
        Expect.enter(connection, "2")
        RHUIManager.select(connection, productlist)
        RHUIManager.proceed_with_check(connection,
                                       "The following products will be deployed:",
                                       productlist)
        RHUIManager.quit(connection)

    @staticmethod
    def add_rh_repo_by_repo(connection, repolist):
        '''
        add a new Red Hat content repository (By Repository)
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "a")
        Expect.expect(connection, "Import Repositories:.*to abort:", 660)
        Expect.enter(connection, "3")
        RHUIManager.select(connection, repolist)
        repolist_mod = list(repolist)
        for repo in repolist:
            # strip " (kind)"
            repo_stripped = re.sub(r" \([a-zA-Z]*\)$", "", repo)
            # strip " (version)" if present (if "(RPMs)" isn't there instead)
            repo_stripped = re.sub(r" \((?!RPMs)[a-zA-Z0-9_-]*\)$", "", repo_stripped)
            repolist_mod.append(repo_stripped)
        RHUIManager.proceed_with_check(connection,
                                       "The following product repositories will be deployed:",
                                       repolist_mod)
        RHUIManager.quit(connection)

    @staticmethod
    def add_container(connection, containername, containerid="", displayname=""):
        '''
        add a new Red Hat container
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "ad")
        Expect.expect(connection, "Name of the container in the registry:")
        Expect.enter(connection, containername)
        Expect.expect(connection, "Unique ID for the container .*]", 60)
        Expect.enter(connection, containerid)
        Expect.expect(connection, "Display name for the container.*]:")
        Expect.enter(connection, displayname)
        if not containerid:
            containerid = containername.replace("/", "_").replace(".", "_")
        if not displayname:
            displayname = containername.replace("/", "_").replace(".", "_")
        RHUIManager.proceed_with_check(connection,
                                       "The following container will be added:",
                                       ["Container Id: " + containerid,
                                        "Display Name: " + displayname,
                                        "Upstream Container Name: " + containername])
        RHUIManager.quit(connection)

    @staticmethod
    def list(connection):
        '''
        list repositories
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "l")
        # eating prompt!!
        pattern = re.compile(r'l\r\n(.*)\r\n-+\r\nrhui\s* \(repo\)\s* =>',
                             re.DOTALL)
        ret = Expect.match(connection, pattern, grouplist=[1])[0]
        reslist = map(str.strip, str(ret).splitlines())
        repolist = []
        for line in reslist:
            if line in ["",
                        "Custom Repositories",
                        "Red Hat Repositories",
                        "OSTree",
                        "Docker",
                        "Yum",
                        "No repositories are currently managed by the RHUI"]:
                continue
            repolist.append(line)
        Expect.enter(connection, 'q')
        return repolist

    @staticmethod
    def get_repo_version(connection, reponame):
        '''
        get repo version
        '''
        repolist = RHUIManagerRepo.list(connection)
        # delete escape back slash from the reponame
        reponame = reponame.replace("\\", "")
        # get full repo name with its version from the list of all repos
        full_reponame = next((s for s in repolist if reponame in s), None)
        #return full_reponame
        # get its version
        repo_version = re.sub(r'^.*\((.*?)\)[^\(]*$', r'\g<1>', full_reponame)

        return repo_version

    @staticmethod
    def delete_repo(connection, repolist):
        '''
        delete a repository from the RHUI
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "d")
        RHUIManager.select(connection, repolist)
        RHUIManager.proceed_without_check(connection)
        RHUIManager.quit(connection)

    @staticmethod
    def delete_all_repos(connection):
        '''
        delete all repositories from the RHUI
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "d")
        Expect.expect(connection, "Enter value .*:", 360)
        Expect.enter(connection, "a")
        Expect.expect(connection, "Enter value .*:")
        Expect.enter(connection, "c")
        RHUIManager.proceed_without_check(connection)
        # Wait until all repos are deleted
        RHUIManager.quit(connection, "", 360)
        while RHUIManagerRepo.list(connection):
            time.sleep(10)

    @staticmethod
    def upload_content(connection, repolist, path):
        '''
        upload content to a custom repository
        '''
        # Check whether "path" is a file or a directory.
        # If it is a directory, get a list of *.rpm files in it.
        Expect.enter(connection, "stat -c %F " + path)
        path_type = Expect.expect_list(connection,
                                       [(re.compile(".*regular file.*", re.DOTALL), 1),
                                        (re.compile(".*directory.*", re.DOTALL), 2)])
        if path_type == 1:
            content = [basename(path)]
        elif path_type == 2:
            Expect.enter(connection, "echo " + path + "/*.rpm")
            output = Expect.match(connection, re.compile("(.*)", re.DOTALL))[0]
            rpm_files = output.splitlines()[1]
            content = []
            for rpm_file in rpm_files.split():
                content.append(basename(rpm_file))
        else:
            # This should not happen. Getting here means that "path" is neither a file
            # nor a directory.
            # Anyway, going on with no content,
            # leaving it up to proceed_with_check() to handle this situation.
            content = []
        # Continue in rhui-manager.
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "u")
        RHUIManager.select(connection, repolist)
        Expect.expect(connection, "will be uploaded:")
        Expect.enter(connection, path)
        RHUIManager.proceed_with_check(connection, "The following RPMs will be uploaded:", content)
        RHUIManager.quit(connection, timeout=60)

    @staticmethod
    def check_for_package(connection, reponame, package):
        '''
        list packages in a repository
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "p")

        RHUIManager.select_one(connection, reponame)
        Expect.expect(connection, r"\(blank line for no filter\):")
        Expect.enter(connection, package)

        pattern = re.compile(r'.*only\.\r\n(.*)\r\n-+\r\nrhui\s* \(repo\)\s* =>',
                             re.DOTALL)
        ret = Expect.match(connection, pattern, grouplist=[1])[0]
        reslist = map(str.strip, str(ret).splitlines())
        packagelist = []
        for line in reslist:
            if line == '':
                continue
            if line == 'Packages:':
                continue
            if line == 'No packages found that match the given filter.':
                continue
            if line == 'No packages in the repository.':
                continue
            packagelist.append(line)
        Expect.enter(connection, 'q')
        return packagelist

    @staticmethod
    def check_detailed_information(connection, repo_data, type_data, gpg_data, package_count):
        '''
        verify that a repository has the expected properties

        repo_data: [string, string]
                   [0]: repo name
                   [1]: relative path
        type_data: [bool, bool]
                   [0]: True? Custom. False? Red Hat.
                   [1]: True? Protected. False? Unprotected. (Only checked with a Custom repo.)
        gpg_data:  [bool, string, bool]
                   [0]: True? GPG Check Yes. False? GPG Check No.
                   [1]: Custom GPG Keys (comma-separated names), or None.
                   [2]: True? Red Hat GPG Key Yes. False? Red Hat GPG Key No.
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "i")
        RHUIManager.select(connection, [repo_data[0]])
        pattern = re.compile(r".*(Name:.*)\r\n\r\n-+\r\nrhui\s* \(repo\)\s* =>", re.DOTALL)
        actual_responses = Expect.match(connection, pattern)[0].splitlines()
        Expect.enter(connection, "q")
        expected_responses = ["Name:                " + repo_data[0]]
        if type_data[0]:
            repo_type = "Custom"
            if type_data[1]:
                relative_path = "protected/" + repo_data[1]
            else:
                relative_path = "unprotected/" + repo_data[1]
        else:
            repo_type = "Red Hat"
            relative_path = repo_data[1]
        expected_responses.append("Type:                " + repo_type)
        expected_responses.append("Relative Path:       " + relative_path)
        if gpg_data[0]:
            expected_responses.append("GPG Check:           Yes")
            if gpg_data[1]:
                expected_responses.append("Custom GPG Keys:     " + gpg_data[1])
            else:
                expected_responses.append("Custom GPG Keys:     (None)")
            if gpg_data[2]:
                expected_responses.append("Red Hat GPG Key:     Yes")
            else:
                expected_responses.append("Red Hat GPG Key:     No")
        else:
            expected_responses.append("GPG Check:           No")
        expected_responses.append("Package Count:       " + str(package_count))
        if repo_type == "Red Hat":
            sync_data = actual_responses.pop()
            nose.tools.ok_("Next Sync:" in sync_data)
            sync_data = actual_responses.pop()
            nose.tools.ok_("Last Sync:" in sync_data)
        nose.tools.eq_(actual_responses, expected_responses)
