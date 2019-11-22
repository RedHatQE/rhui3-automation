#!/usr/bin/python
"""RHUI 3 Automation Deployment Made Easy"""

from __future__ import print_function

from os import system
from os.path import exists, expanduser
import sys

import argparse
try:
    from configparser import RawConfigParser # Python 3+
except ImportError:
    from ConfigParser import RawConfigParser # Python 2

# there can be configuration to complement some options
CFG_FILE = "~/.rhui3-automation.cfg"
R3A_CFG = RawConfigParser()
R3A_CFG.read(expanduser(CFG_FILE))

PRS = argparse.ArgumentParser(description="Run the RHUI 3 Automation playbook to deploy RHUI.",
                              formatter_class=argparse.ArgumentDefaultsHelpFormatter)
PRS.add_argument("inventory",
                 help="inventory file; typically hosts_*.cfg created by create-cf-stack.py",
                 nargs="?")
PRS.add_argument("--iso",
                 help="RHUI ISO file",
                 default="~/RHUI/RHUI.iso",
                 metavar="file")
PRS.add_argument("--gluster-rpm",
                 help="rh-amazon-rhui-client-rhs30 RPM (if using GlusterFS)",
                 metavar="file")
PRS.add_argument("--upgrade",
                 help="upgrade all packages before running the deployment",
                 action="store_true")
PRS.add_argument("--extra-files",
                 help="ZIP file with extra files",
                 default="~/RHUI/extra_files.zip",
                 metavar="file")
PRS.add_argument("--creds",
                 help="configuration file with credentials",
                 default="~/RHUI/credentials.conf",
                 metavar="file")
PRS.add_argument("--tests",
                 help="RHUI test to run",
                 metavar="test name or category")
PRS.add_argument("--patch",
                 help="patch to apply to rhui3-automation",
                 metavar="file")
PRS.add_argument("--rhel7b",
                 help="RHEL 7 Beta baseurl or compose",
                 metavar="URL/compose")
PRS.add_argument("--rhel8b",
                 help="RHEL 8 Beta baseurl or compose",
                 metavar="URL/compose")
PRS.add_argument("--tags",
                 help="run only tasks tagged this way",
                 metavar="tags")
PRS.add_argument("--skip-tags",
                 help="skip tasks tagged this way",
                 metavar="tags")

ARGS = PRS.parse_args()

if not ARGS.inventory:
    PRS.print_help()
    sys.exit(1)

if not exists(ARGS.inventory):
    print("%s does not exist." % ARGS.inventory)
    sys.exit(1)

if not ARGS.iso or not exists(expanduser(ARGS.iso)):
    print("You must supply a valid RHUI ISO file.")
    sys.exit(1)

# start building the command
CMD = "ansible-playbook -i %s deploy/site.yml --extra-vars '" % ARGS.inventory

# start building the extra variables
EVARS = "rhui_iso=%s" % ARGS.iso

if ARGS.gluster_rpm:
    if exists(expanduser(ARGS.gluster_rpm)):
        EVARS += " common_custom_rpm=%s" % ARGS.gluster_rpm
    else:
        print("--gluster-rpm was specified but %s does not exist, exiting." % ARGS.gluster_rpm)
        sys.exit(1)

if ARGS.upgrade:
    EVARS += " upgrade_all_pkg=True"

if exists(expanduser(ARGS.extra_files)):
    EVARS += " extra_files=%s" % ARGS.extra_files
else:
    print("%s does not exist, ignoring" % ARGS.extra_files)

if exists(expanduser(ARGS.creds)):
    EVARS += " credentials=%s" % ARGS.creds
else:
    print("%s does not exist, ignoring" % ARGS.creds)

# see if the configuration contains templates for RHEL Beta baseurls;
# if so, expand them
# if not, use the arguments verbatim
if ARGS.rhel7b:
    if R3A_CFG.has_section("beta") and R3A_CFG.has_option("beta", "rhel7_template"):
        ARGS.rhel7b = R3A_CFG.get("beta", "rhel7_template") % ARGS.rhel7b
    EVARS += " rhel7_beta_baseurl=%s" % ARGS.rhel7b

if ARGS.rhel8b:
    if R3A_CFG.has_section("beta") and R3A_CFG.has_option("beta", "rhel8_template"):
        ARGS.rhel8b = R3A_CFG.get("beta", "rhel8_template") % ARGS.rhel8b
    EVARS += " rhel8_beta_baseurl=%s" % ARGS.rhel8b

if ARGS.tests:
    EVARS += " tests=%s" % ARGS.tests

if ARGS.patch:
    if exists(expanduser(ARGS.patch)):
        EVARS += " patch=%s" % ARGS.patch
    else:
        print("--patch was specified but %s does not exist, exiting." % ARGS.patch)
        sys.exit(1)

# join the command and the extra variables
CMD += EVARS + "'"

# use/skip specific tags if requested
if ARGS.tags:
    CMD += " --tags %s" % ARGS.tags

if ARGS.skip_tags:
    CMD += " --skip-tags %s" % ARGS.skip_tags

# the command is now built; print it and then run it
print("Running: %s" % CMD)
system(CMD)
