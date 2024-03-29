""" RHUIManager Client functions """

from stitches.expect import Expect

from rhui3_tests_lib.rhuimanager import RHUIManager


class RHUIManagerClient():
    '''
    Represents -= Client Entitlement Management =- RHUI screen
    '''
    @staticmethod
    def generate_ent_cert(connection, repolist, certname, dirname, validity_days=""):
        '''
        generate an entitlement certificate
        '''
        RHUIManager.screen(connection, "client")
        Expect.enter(connection, "e")
        RHUIManager.select(connection, repolist)
        Expect.expect(connection, "Name of the certificate.*contained with it:")
        Expect.enter(connection, certname)
        Expect.expect(connection, "Local directory in which to save the generated certificate.*:")
        Expect.enter(connection, dirname)
        Expect.expect(connection, "Number of days the certificate should be valid.*:")
        Expect.enter(connection, validity_days)
        RHUIManager.proceed_without_check(connection)
        RHUIManager.quit(connection)

    @staticmethod
    def create_conf_rpm(connection, dirname, certpath, certkey, rpmname, rpmversion="",
                        rpmrelease="", unprotected_repos=None):
        '''
        create a client configuration RPM from an entitlement certificate
        '''
        RHUIManager.screen(connection, "client")
        Expect.enter(connection, "c")
        Expect.expect(connection, "Full path to local directory.*:")
        Expect.enter(connection, dirname)
        Expect.expect(connection, "Name of the RPM:")
        Expect.enter(connection, rpmname)
        Expect.expect(connection, "Version of the configuration RPM.*:")
        Expect.enter(connection, rpmversion)
        Expect.expect(connection, "Release of the configuration RPM.*:")
        Expect.enter(connection, rpmrelease)
        Expect.expect(connection, "Full path to the entitlement certificate.*:")
        Expect.enter(connection, certpath)
        Expect.expect(connection,
                      "Full path to the private key for the above entitlement certificate:")
        Expect.enter(connection, certkey)
        if unprotected_repos:
            RHUIManager.select(connection, unprotected_repos)
        if not rpmversion:
            rpmversion = "2.0"
        if not rpmrelease:
            rpmrelease = "1"
        Expect.expect(connection,
                      "Location: %s/%s-%s/build/RPMS/noarch/%s-%s-%s.noarch.rpm" % \
                      (dirname, rpmname, rpmversion, rpmname, rpmversion, rpmrelease))
        Expect.enter(connection, "q")

    @staticmethod
    def create_container_conf_rpm(connection, dirname, rpmname, rpmversion="", rpmrelease="",
                                  port=""):
        '''
        create a container client configuration RPM
        '''
        RHUIManager.screen(connection, "client")
        Expect.enter(connection, "d")
        Expect.expect(connection, "Full path to local directory.*:")
        Expect.enter(connection, dirname)
        Expect.expect(connection, "Name of the RPM:")
        Expect.enter(connection, rpmname)
        Expect.expect(connection, "Version of the configuration RPM.*:")
        Expect.enter(connection, rpmversion)
        Expect.expect(connection, "Release of the configuration RPM.*:")
        Expect.enter(connection, rpmrelease)
        Expect.expect(connection, "Port to serve Docker content on .*:")
        Expect.enter(connection, port)
        if not rpmversion:
            rpmversion = "2.0"
        if not rpmrelease:
            rpmrelease = "1"
        Expect.expect(connection,
                      "Location: %s/%s-%s/build/RPMS/noarch/%s-%s-%s.noarch.rpm" % \
                      (dirname, rpmname, rpmversion, rpmname, rpmversion, rpmrelease))
        Expect.enter(connection, "q")

    @staticmethod
    def create_atomic_conf_pkg(connection, dirname, tarname, certpath, certkey, port=""):
        '''
        create an atomic client configuration package (RHEL 7 only)
        '''
        RHUIManager.screen(connection, "client")
        Expect.enter(connection, "o")
        Expect.expect(connection, "Full path to local directory.*:")
        Expect.enter(connection, dirname)
        Expect.expect(connection, "Name of the tar file.*:")
        Expect.enter(connection, tarname)
        Expect.expect(connection, "Full path to the entitlement certificate.*:")
        Expect.enter(connection, certpath)
        Expect.expect(connection, "Full path to the private key.*:")
        Expect.enter(connection, certkey)
        Expect.expect(connection, "Port to serve Docker content on .*:")
        Expect.enter(connection, port)
        Expect.expect(connection,
                      "Location: %s/%s.tar.gz" % \
                      (dirname, tarname))
        Expect.enter(connection, "q")
