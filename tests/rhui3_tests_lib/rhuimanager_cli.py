""" RHUIManager Client functions """

from stitches.expect import Expect
from rhui3_tests_lib.rhuimanager import RHUIManager


class RHUIManagerClient(object):
    '''
    Represents -= Client Entitlement Management =- RHUI screen
    '''
    @staticmethod
    def generate_ent_cert(connection, repolist, certname, dirname, validity_days="", cert_pw=None):
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
        Expect.expect(connection, ".*rhui \(" + "client" + "\) =>")

    @staticmethod
    def create_conf_rpm(connection, dirname, certpath, certkey, rpmname, rpmversion="", unprotected_repos=None):
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
        Expect.expect(connection, "Full path to the entitlement certificate.*:")
        Expect.enter(connection, certpath)
        Expect.expect(connection, "Full path to the private key for the above entitlement certificate:")
        Expect.enter(connection, certkey)
        if unprotected_repos:
            RHUIManager.select(connection, unprotected_repos)
        Expect.expect(connection, ".*rhui \(" + "client" + "\) =>")

    @staticmethod
    def create_docker_conf_rpm(connection, dirname, rpmname, rpmversion="", dockerport=""):
        '''
        create a docker client configuration RPM
        '''
        RHUIManager.screen(connection, "client")
        Expect.enter(connection, "d")
        Expect.expect(connection, "Full path to local directory.*:")
        Expect.enter(connection, dirname)
        Expect.expect(connection, "Name of the RPM:")
        Expect.enter(connection, rpmname)
        Expect.expect(connection, "Version of the configuration RPM.*:")
        Expect.enter(connection, rpmversion)
        Expect.expect(connection, "Port to serve Docker content on .*:")
        Expect.enter(connection, dockerport)
        Expect.expect(connection, ".*rhui \(" + "client" + "\) =>")
