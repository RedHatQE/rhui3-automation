""" Cds container """
import re
from rhui3_tests_lib import screenitem
from rhui3_tests_lib import lineparser

class Instance(screenitem.ScreenItem):
    """A CDS and HAProxy attributes container"""
    parser = lineparser.Parser(mapping=[
            ('host_name', re.compile("^  Hostname:\s*(.*)$")),
            ('user_name', re.compile("^  SSH Username:\s*(.*)$")),
            ('ssh_key_path', re.compile("^  SSH Private Key:\s*(.*)$")),
    ])

    def __init__(self,
            host_name=None,
            user_name="ec2-user",
            ssh_key_path="/root/.ssh/id_rsa_rhua",
        ):
        self.host_name = host_name
        self.user_name = user_name
        self.ssh_key_path = ssh_key_path

    def __repr__(self):
        return  "Instance(" + \
                "host_name=%r, " % self.host_name + \
                "user_name=%r, " % self.user_name + \
                "ssh_key_path=%r)" % self.ssh_key_path

    def __eq__(self, other):
        ret = True
        ret &= self.host_name == other.host_name
        ret &= self.user_name == other.user_name
        ret &= self.ssh_key_path == other.ssh_key_path
        return ret

# looks unused
#    def __cmp__(self, other):
#        """for comparison of sorted lists to work as expected"""
#        if self == other:
#            return 0
#        # hack that in other cases
#        #return cmp(repr(self), repr(other))
#        return (repr(self) > repr(other)) - (repr(self) < repr(other))
#
# just in case we need to compare instances in the future
#    __lt__ = __cmp__
