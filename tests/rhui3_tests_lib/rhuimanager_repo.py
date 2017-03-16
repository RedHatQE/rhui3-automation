""" RHUIManager Repo functions """

import re
from os.path import basename

from stitches.expect import Expect, ExpectFailed
from rhui3_tests_lib.rhuimanager import RHUIManager


class RHUIManagerRepo(object):
    '''
    Represents -= Repository Management =- RHUI screen
    '''
    @staticmethod
    def add_custom_repo(connection, reponame, displayname="", path="", checksum_alg="1", entitlement="y", entitlement_path="", redhat_gpg="y", custom_gpg=None):
        '''
        create a new custom repository
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "c")
        Expect.expect(connection, "Unique ID for the custom repository.*:")
        Expect.enter(connection, reponame)
        checklist = ["ID: " + reponame]
        state = Expect.expect_list(connection, [(re.compile(".*Display name for the custom repository.*:", re.DOTALL), 1),\
                                               (re.compile(".*Unique ID for the custom repository.*:", re.DOTALL), 2)])
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
            Expect.expect(connection, "Should the repository require an entitlement certificate to access\? \(y/n\)")
            Expect.enter(connection, entitlement)
            if entitlement == "y":
                Expect.expect(connection, "Path that should be used when granting an entitlement for this repository.*:")
                Expect.enter(connection, entitlement_path)
                if entitlement_path != "":
                    checklist.append("Entitlement: " + entitlement_path)
                else:       
                    educated_guess, replace_count = re.subn("(i386|x86_64)", "$basearch", path_real)
                    if replace_count > 1:
                        # bug 815975
                        educated_guess = path_real
                    checklist.append("Entitlement: " + educated_guess)
            Expect.expect(connection, "packages are signed by a GPG key\? \(y/n\)")
            if redhat_gpg == "y" or custom_gpg:
                Expect.enter(connection, "y")
                checklist.append("GPG Check Yes")
                Expect.expect(connection, "Will the repository be used to host any Red Hat GPG signed content\? \(y/n\)")
                Expect.enter(connection, redhat_gpg)
                if redhat_gpg == "y":
                    checklist.append("Red Hat GPG Key: Yes")
                else:       
                    checklist.append("Red Hat GPG Key: No")
                Expect.expect(connection, "Will the repository be used to host any custom GPG signed content\? \(y/n\)")
                if custom_gpg:
                    Expect.enter(connection, "y")
                    Expect.expect(connection, "Enter the absolute path to the public key of the GPG keypair:")
                    Expect.enter(connection, custom_gpg)
                    Expect.expect(connection, "Would you like to enter another public key\? \(y/n\)")
                    Expect.enter(connection, "n")
                    checklist.append("Custom GPG Keys: '" + custom_gpg + "'")
                else:       
                    Expect.enter(connection, "n")
                    checklist.append("Custom GPG Keys: \(None\)")
            else:           
                Expect.enter(connection, "n")
                checklist.append("GPG Check No") 
                checklist.append("Red Hat GPG Key: No")
    
            RHUIManager.proceed_with_check(connection, "The following repository will be created:", checklist)
            RHUIManager.quit(connection, "Successfully created repository *")
        else:      
            Expect.enter(connection, '\x03')
            RHUIManager.quit(connection)

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
        RHUIManager.proceed_with_check(connection, "The following products will be deployed:", productlist)
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
            repolist_mod.append(re.sub(" \\\\\([a-zA-Z0-9_-]*\\\\\) \\\\\(Yum\\\\\)", "", repo))
        RHUIManager.proceed_with_check(connection, "The following product repositories will be deployed:", repolist_mod)
        RHUIManager.quit(connection)

    @staticmethod
    def add_docker_container(connection, containername, containerid="", displayname=""):
        '''
        add a new Red Hat docker container
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "ad")
        Expect.expect(connection, "Name of the container in the registry:")
        Expect.enter(connection, containername)
        Expect.expect(connection, "Unique ID for the container .*]", 60)
        Expect.enter(connection, containerid)
        Expect.expect(connection, "Display name for the container.*]:")
        Expect.enter(connection, displayname)
        RHUIManager.proceed_with_check(connection, "The following container will be added:",
        ["Container Id: " + containername.replace("/","_").replace(".","_"),
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
        pattern = re.compile('l\r\n(.*)\r\n-+\r\nrhui\s* \(repo\)\s* =>',
                re.DOTALL)
        ret = Expect.match(connection, pattern, grouplist=[1])[0]
        reslist = map(lambda x: x.strip(), ret.split("\r\n"))
        repolist = []
        for line in reslist:
            if line in ["", "Custom Repositories", "Red Hat Repositories", "OSTree", "Docker", "Yum", "No repositories are currently managed by the RHUI"]:
                continue
            repolist.append(line)
        Expect.enter(connection, 'q')
        return repolist

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
        RHUIManager.quit(connection, "", 360)

    @staticmethod
    def upload_content(connection, repolist, path):
        '''
        upload content to a custom repository
        '''
        # Temporarily quit rhui-manager and check whether "path" is a file or a directory.
        # If it is a directory, get a list of *.rpm files in it.
        Expect.enter(connection, 'q')
        Expect.enter(connection, "stat -c %F " + path)
        path_type = Expect.expect_list(connection, [(re.compile(".*regular file.*", re.DOTALL), 1), (re.compile(".*directory.*", re.DOTALL), 2)])
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
            # This should not happen. Getting here means that "path" is neither a file nor a directory.
            # Anyway, going on with no content, leaving it up to proceed_with_check() to handle this situation.
            content = []
        # Start rhui-manager again and continue.
        RHUIManager.initial_run(connection)
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "u")
        RHUIManager.select(connection, repolist)
        Expect.expect(connection, "will be uploaded:")
        Expect.enter(connection, path)
        RHUIManager.proceed_with_check(connection, "The following RPMs will be uploaded:", content)
        RHUIManager.quit(connection)

    @staticmethod
    def check_for_package(connection, reponame, package):
        '''
        list packages in a repository
        '''
        RHUIManager.screen(connection, "repo")
        Expect.enter(connection, "p")

        RHUIManager.select_one(connection, reponame)
        Expect.expect(connection, "\(blank line for no filter\):")
        Expect.enter(connection, package)

        pattern = re.compile('.*only\.\r\n(.*)\r\n-+\r\nrhui\s* \(repo\)\s* =>',
                             re.DOTALL)
        ret = Expect.match(connection, pattern, grouplist=[1])[0]
        reslist = map(lambda x: x.strip(), ret.split("\r\n"))
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

