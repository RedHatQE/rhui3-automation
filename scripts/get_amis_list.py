#! /usr/bin/python -tt
"""Regenerate a list of AMI IDs based on the given AMI description."""

import sys
import subprocess
import json
import argparse

if subprocess.call("which aws &> /dev/null", shell=True):
    sys.stderr.write("The aws client is not available. Please install package awscli.\n")
    sys.exit(1)

if subprocess.call("aws configure get aws_access_key_id &> /dev/null", shell=True):
    sys.stderr.write("The aws client is not configured. Please run `aws configure'.\n")
    sys.exit(1)

argparser = argparse.ArgumentParser(description='Get list of AMIs')
argparser.add_argument('rhel',
                       help='Description of the ami \
                       (e.g. RHEL-7.5_HVM_GA-20180322-x86_64-1-Hourly2-GP2)',
                       metavar='AMI',
                       nargs='?')

args = argparser.parse_args()

if not args.rhel:
    argparser.print_help()
    sys.exit(1)

if args.rhel.startswith("RHEL-8"):
    mapping = "RHEL8mapping.json"
elif args.rhel.startswith("RHEL-7"):
    mapping = "RHEL7mapping.json"
elif args.rhel.startswith("RHEL-6"):
    mapping = "RHEL6mapping.json"
elif args.rhel.startswith("RHEL-5"):
    mapping = "RHEL5mapping.json"
elif args.rhel.startswith("RHEL-Atomic") or args.rhel.startswith("Atomic"):
    mapping = "ATOMICmapping.json"
else:
    sys.stderr.write("Wrong parameters")
    sys.exit(1)

ami_properties = args.rhel.split("-")
if ami_properties[3] != "x86_64":
    mapping = mapping.replace(".", "_%s." % ami_properties[3])

cmd = "aws ec2 describe-regions " \
      "--all-regions " \
      "--query 'Regions[].{Name:RegionName}' " \
      "--output text"
cmd_out = subprocess.check_output(cmd, shell=True)
regions = cmd_out.decode().splitlines()

cmd = "aws ec2 describe-images " \
      "--filters Name=name,Values=*{0}* " \
      "--query Images[*].ImageId --region {1}"

out_dict = {}

for i in regions:
    ami = subprocess.Popen(cmd.format(args.rhel, i).split(), stdout=subprocess.PIPE)
    out, err = ami.communicate()
    js = json.loads(out)
    try:
        ami_id = js[0]
    except IndexError as err:
        sys.stderr.write("Got '%s' error \n" % err)
        sys.stderr.write("Missing AMI ID for '%s' region \n \n" % i)
        ami_id = ""
    out_dict[i] = {}
    out_dict[i]["AMI"] = ami_id
try:
    with open(mapping, 'w') as f:
        json.dump(out_dict, f, indent=4, sort_keys=True)

except Exception as err:
    sys.stderr.write("Got '%s' error" % err)
    sys.exit(1)
