#! /usr/bin/python -tt

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
argparser.add_argument('rhel', help='Description of the ami (f.e. RHEL-7.5_HVM_GA-20180322-x86_64-1-Hourly2-GP2)', metavar='AMI', nargs='?')

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

regions = ["ap-northeast-1",
           "ap-northeast-2",
           "ap-south-1", 
           "ap-southeast-1",
           "ap-southeast-2",
           "ca-central-1",
           "eu-central-1",
           "eu-north-1",
           "eu-west-1",
           "eu-west-2",
           "eu-west-3",
           "sa-east-1",
           "us-east-1",
           "us-east-2",
           "us-west-1",
           "us-west-2"
           ]

cmd = "aws ec2 describe-images " \
      "--filters Name=name,Values=*{0}* " \
      "--query Images[*].ImageId --region {1}"

out_dict = {}

for i in regions:
    ami = subprocess.Popen(cmd.format(args.rhel, i).split(), stdout=subprocess.PIPE)
    out,err = ami.communicate()
    js = json.loads(out)
    try:
        ami_id = js[0]
    except IndexError as e:
        sys.stderr.write("Got '%s' error \n" % e)
        sys.stderr.write("Missing AMI ID for '%s' region \n \n" % i)
        ami_id = ""
    out_dict[i] = {}
    out_dict[i]["AMI"] = ami_id
    
try:
    with open(mapping, 'w') as f:
        json.dump(out_dict, f, indent=4)

except Exception as e:
    sys.stderr.write("Got '%s' error" % e)
    sys.exit(1)
