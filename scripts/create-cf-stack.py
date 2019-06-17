#! /usr/bin/python -tt

""" Create CloudFormation stack """

from paramiko import SSHClient
from boto import cloudformation
from boto import regioninfo
from boto import ec2
import argparse
import time
import logging
import sys
import random
import string
import json
import tempfile
import paramiko
import yaml
import re

# pylint: disable=W0621


class SyncSSHClient(SSHClient):
    '''
    Special class for sync'ed commands execution over ssh
    '''
    def run_sync(self, command):
        """ Run sync """
        logging.debug("RUN_SYNC '%s'", command)
        stdin, stdout, stderr = self.exec_command(command)
        status = stdout.channel.recv_exit_status()
        if status:
            logging.debug("RUN_SYNC status: %i", status)
        else:
            logging.debug("RUN_SYNC failed!")
        return stdin, stdout, stderr

    def run_with_pty(self, command):
        """ Run with PTY """
        logging.debug("RUN_WITH_PTY '%s'", command)
        chan = self.get_transport().open_session()
        chan.get_pty()
        chan.exec_command(command)
        status = chan.recv_exit_status()
        logging.debug("RUN_WITH_PTY recv: %s", chan.recv(16384))
        logging.debug("RUN_WITH_PTY status: %i", status)
        chan.close()
        return status

instance_types = {"arm64": "a1.large", "x86_64": "m3.large"}

argparser = argparse.ArgumentParser(description='Create CloudFormation stack')
argparser.add_argument('--rhua', help='RHEL version for RHUI setup (RHEL6, RHEL7)', default="RHEL6")

argparser.add_argument('--iso', help='iso version', default="iso")
argparser.add_argument('--cli5', help='number of RHEL5 clients', type=int, default=0)
argparser.add_argument('--cli6', help='number of RHEL6 clients', type=int, default=0)
argparser.add_argument('--cli7', help='number of RHEL7 clients', type=int, default=0)
argparser.add_argument('--cli7-arch', help='RHEL 7 clients\' architectures (comma-separated list)', default='x86_64', metavar='ARCH')
argparser.add_argument('--cli8', help='number of RHEL8 clients', type=int, default=0)
argparser.add_argument('--cli8-arch', help='RHEL 8 clients\' architectures (comma-separated list)', default='x86_64', metavar='ARCH')
argparser.add_argument('--cds', help='number of CDSes instances', type=int, default=1)
argparser.add_argument('--dns', help='DNS', action='store_const', const=True, default=False)
argparser.add_argument('--nfs', help='NFS', action='store_const', const=True, default=False)
argparser.add_argument('--haproxy', help='number of HAProxies', type=int, default=1)
argparser.add_argument('--gluster', help='Gluster', action='store_const', const=True, default=False)
argparser.add_argument('--test', help='test machine', action='store_const', const=True, default=False)
argparser.add_argument('--atomic-cli', help='number of Atomic CLI machines', type=int, default=0)
argparser.add_argument('--input-conf', default="/etc/rhui_ec2.yaml", help='use supplied yaml config file')
argparser.add_argument('--output-conf', help='output file')
argparser.add_argument('--region', default="eu-west-1", help='use specified region')
argparser.add_argument('--debug', action='store_const', const=True,
                       default=False, help='debug mode')
argparser.add_argument('--dry-run', action='store_const', const=True,
                       default=False, help='do not run stack creation, validate only')
argparser.add_argument('--parameters', metavar='<expr>', nargs="*",
                       help="space-separated NAME=VALUE list of parameters")

argparser.add_argument('--timeout', type=int,
                       default=10, help='stack creation timeout')

argparser.add_argument('--vpcid', help='VPCid')
argparser.add_argument('--subnetid', help='Subnet id (for VPC)')

argparser.add_argument('--r3', action='store_const', const=True, default=False,
                        help='use r3.xlarge instances to squeeze out more network and cpu performance (requires vpcid and subnetid)')
argparser.add_argument('--ami-5-override', help='RHEL 5 AMI ID to override the mapping', metavar='ID')
argparser.add_argument('--ami-6-override', help='RHEL 6 AMI ID to override the mapping', metavar='ID')
argparser.add_argument('--ami-7-override', help='RHEL 7 AMI ID to override the mapping', metavar='ID')
argparser.add_argument('--ami-8-override', help='RHEL 8 AMI ID to override the mapping', metavar='ID')
argparser.add_argument('--ami-atomic-override', help='RHEL Atomic host AMI ID to override the mapping', metavar='ID')
argparser.add_argument('--ansible-ssh-extra-args', help='Extra arguments for SSH connections established by Ansible', metavar='ARGS')

args = argparser.parse_args()


fs_type = "rhua"

if args.debug:
    loglevel = logging.DEBUG
else:
    loglevel = logging.INFO

REGION = args.region

logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

if args.debug:
    logging.getLogger("paramiko").setLevel(logging.DEBUG)
else:
    logging.getLogger("paramiko").setLevel(logging.WARNING)

if (args.vpcid and not args.subnetid) or (args.subnetid and not args.vpcid):
    logging.error("vpcid and subnetid parameters should be set together!")
    sys.exit(1)
if (args.r3 and not args.vpcid):
    logging.error("r3 requires setting vpcid and subnetid")
    sys.exit(1)

try:
    with open(args.input_conf, 'r') as confd:
        valid_config = yaml.load(confd)

    (ssh_key_name, ssh_key) = valid_config["ssh"][REGION]
    ec2_key = valid_config["ec2"]["ec2-key"]
    ec2_secret_key = valid_config["ec2"]["ec2-secret-key"]
    ec2_name = re.search("[a-zA-Z]+", ssh_key_name).group(0)

except Exception as e:
    logging.error("got '%s' error processing: %s", e, args.input_conf)
    logging.error("Please, check your config or and try again")
    sys.exit(1)

json_dict = {}

json_dict['AWSTemplateFormatVersion'] = '2010-09-09'


if args.gluster:
    fs_type = "gluster"
    if args.cds < 3:
        args.cds = 3
    if args.nfs:
        logging.error("Can't be NFS and Gluster configuration.")
        sys.exit(1)
if args.nfs:
    fs_type = "nfs"
if args.atomic_cli:
    if args.rhua != "RHEL7":
        logging.error("ATOMIC clients need 'RHEL7' for RHUI setup")
        sys.exit(1)

if args.cli7 == -1:
    args.cli7 = len(instance_types)
    args.cli7_arch = ",".join(instance_types.keys())
if args.cli8 == -1:
    args.cli8 = len(instance_types)
    args.cli8_arch = ",".join(instance_types.keys())

json_dict['Description'] = 'RHUI with %s CDSes' % args.cds
json_dict['Description'] += " %s HAProxy" % args.haproxy
if args.cli5 > 0:
    json_dict['Description'] += " %s RHEL5 clients" % args.cli5
if args.cli6 > 0:
    json_dict['Description'] += " %s RHEL6 clients" % args.cli6
if args.cli7 > 0:
    json_dict['Description'] += " %s RHEL7 clients" % args.cli7
if args.cli8 > 0:
    json_dict['Description'] += " %s RHEL8 clients" % args.cli8
if args.atomic_cli > 0:
    json_dict['Description'] += " %s ATOMIC clients" % args.atomic_cli
if args.gluster:
    json_dict['Description'] += " Gluster"
if args.test:
    json_dict['Description'] += " TEST machine"
if args.dns:
    json_dict['Description'] += " DNS"
if args.nfs:
    json_dict['Description'] += " NFS"


fs_type_f = fs_type

if fs_type_f == "rhua":
    fs_type_f = "nfs"

json_dict['Mappings'] = {u'RHEL5': {args.region: {}},
                         u'RHEL6': {args.region: {}},
                         u'RHEL7': {args.region: {}},
                         u'RHEL8': {args.region: {}},
                         u'ATOMIC': {args.region: {}}}

try:
    if args.ami_5_override:
        json_dict['Mappings']['RHEL5'][args.region]['AMI'] = args.ami_5_override
    else:
        with open("RHEL5mapping.json") as mjson:
            rhel5mapping = json.load(mjson)
            json_dict['Mappings']['RHEL5'] = rhel5mapping

    if args.ami_6_override:
        json_dict['Mappings']['RHEL6'][args.region]['AMI'] = args.ami_6_override
    else:
        with open("RHEL6mapping.json") as mjson:
            rhel6mapping = json.load(mjson)
            json_dict['Mappings']['RHEL6'] = rhel6mapping

    if args.ami_7_override:
        json_dict['Mappings']['RHEL7'][args.region]['AMI'] = args.ami_7_override
    else:
        with open("RHEL7mapping.json") as mjson:
            rhel7mapping = json.load(mjson)
            json_dict['Mappings']['RHEL7'] = rhel7mapping

    if args.ami_8_override:
        json_dict['Mappings']['RHEL8'][args.region]['AMI'] = args.ami_8_override
    else:
        with open("RHEL8mapping.json") as mjson:
            rhel8mapping = json.load(mjson)
            json_dict['Mappings']['RHEL8'] = rhel8mapping

    if args.ami_atomic_override:
        json_dict['Mappings']['ATOMIC'][args.region]['AMI'] = args.ami_atomic_override
    else:
        with open("ATOMICmapping.json") as mjson:
            atomicmapping = json.load(mjson)
            json_dict['Mappings']['ATOMIC'] = atomicmapping

except Exception as e:
    sys.stderr.write("Got '%s' error \n" % e)
    sys.exit(1)

json_dict['Parameters'] = \
{u'KeyName': {u'Description': u'Name of an existing EC2 KeyPair to enable SSH access to the instances',
              u'Type': u'String'}}

json_dict['Resources'] = \
{u'RHUIsecuritygroup': {u'Properties': {u'GroupDescription': u'RHUI security group',
                                        u'SecurityGroupIngress': [{u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'22',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'22'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'443',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'443'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'2049',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'2049'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'5671',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'5671'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'8140',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'8140'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'5000',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'5000'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'24007',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'24007'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'49152',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'49154'},
                                                                   {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'80',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'80'},
                                                                  {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'53',
                                                                   u'IpProtocol': u'tcp',
                                                                   u'ToPort': u'53'},
                                                                  {u'CidrIp': u'0.0.0.0/0',
                                                                   u'FromPort': u'53',
                                                                   u'IpProtocol': u'udp',
                                                                   u'ToPort': u'53'}]},
                        u'Type': u'AWS::EC2::SecurityGroup'}}

# nfs == rhua
# add a 100 GB volume for RHUI repos if using NFS
# add a 50 GB volume for MongoDB either way; MongoDB can be greedy
if (fs_type == "rhua"):
    json_dict['Resources']["rhua"] = \
     {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                               u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                               u'KeyName': {u'Ref': u'KeyName'},
                               u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                                 u'BlockDeviceMappings' : [
                                            {
                                              "DeviceName" : "/dev/sdb",
                                              "Ebs" : {"VolumeSize" : "100"}
                                            },
                                            {
                                              "DeviceName" : "/dev/sdm",
                                              "Ebs" : {"VolumeSize" : "50"}
                                            },
                                 ],
                               u'Tags': [{u'Key': u'Name',
                                          u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'rhua']]}},
                                         {u'Key': u'Role', u'Value': u'RHUA'},
                                         ]},
               u'Type': u'AWS::EC2::Instance'}

else:
    json_dict['Resources']["rhua"] = \
     {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                               u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                               u'KeyName': {u'Ref': u'KeyName'},
                               u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                                 u'BlockDeviceMappings' : [
                                            {
                                              "DeviceName" : "/dev/sdm",
                                              "Ebs" : {"VolumeSize" : "50"}
                                            },
                                 ],
                               u'Tags': [{u'Key': u'Name',
                                          u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'rhua']]}},
                                         {u'Key': u'Role', u'Value': u'RHUA'},
                                         ]},
               u'Type': u'AWS::EC2::Instance'}


# gluster
if (fs_type == "gluster"):
    for i in range(1, args.cds + 1):
        json_dict['Resources']["cds%i" % i] = \
            {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                                   u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                                   u'BlockDeviceMappings' : [
                                              {
                                                "DeviceName" : "/dev/sdf",
                                                "Ebs" : {"VolumeSize" : "100"}
                                              },
                                     ],
                                   u'KeyName': {u'Ref': u'KeyName'},
                                   u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                                   u'Tags': [{u'Key': u'Name',
                                              u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'cds%i' % i]]}},
                                             {u'Key': u'Role', u'Value': u'CDS'},
                                             ]},
                   u'Type': u'AWS::EC2::Instance'}

else:
    for i in range(1, args.cds + 1):
        json_dict['Resources']["cds%i" % i] = \
            {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                                   u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                                   u'KeyName': {u'Ref': u'KeyName'},
                                   u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                                   u'Tags': [{u'Key': u'Name',
                                              u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'cds%i' % i]]}},
                                             {u'Key': u'Role', u'Value': u'CDS'},
                                             ]},
                   u'Type': u'AWS::EC2::Instance'}

# clients
os_dict = {5: "RHEL5", 6: "RHEL6", 7: "RHEL7", 8: "RHEL8"}
for i in (5, 6, 7, 8):
    num_cli_ver = args.__getattribute__("cli%i" % i)
    if num_cli_ver:
        os = os_dict[i]
        for j in range(1, num_cli_ver + 1):
            try:
                cli_arch = args.__getattribute__("cli%i_arch" % i).split(",")[j-1]
                if not cli_arch:
                    cli_arch = "x86_64"
            except (AttributeError, IndexError):
                cli_arch = "x86_64"
            try:
                instance_type = instance_types[cli_arch]
            except KeyError:
                logging.error("Unknown architecture: %s" % cli_arch)
                sys.exit(1)
            if cli_arch == "x86_64":
                image_id = {u'Fn::FindInMap': [os, {u'Ref': u'AWS::Region'}, u'AMI']}
            else:
                with open("RHEL%smapping_%s.json" % (i, cli_arch)) as mjson:
                   image_ids =  json.load(mjson)
                   image_id = image_ids[args.region]["AMI"]
            json_dict['Resources']["cli%inr%i" % (i, j)] = \
                {u'Properties': {u'ImageId': image_id,
                                   u'InstanceType': instance_type,
                                   u'KeyName': {u'Ref': u'KeyName'},
                                   u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                                   u'Tags': [{u'Key': u'Name',
                                              u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'cli%i_%i' % (i, j)]]}},
                                             {u'Key': u'Role', u'Value': u'CLI'},
                                             {u'Key': u'OS', u'Value': u'%s' % os[:5]}]},
                   u'Type': u'AWS::EC2::Instance'}
                   
# atomic clients
for i in range(1, args.atomic_cli + 1):
    json_dict['Resources']["atomiccli%i" % i] = \
        {u'Properties': {u'ImageId': {u'Fn::FindInMap': ["ATOMIC", {u'Ref': u'AWS::Region'}, u'AMI']},
                               u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                               u'KeyName': {u'Ref': u'KeyName'},
                               u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                               u'Tags': [{u'Key': u'Name',
                                          u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'atomic_cli%i' % i]]}},
                                         {u'Key': u'Role', u'Value': u'ATOMIC_CLI'},
                                         ]},
               u'Type': u'AWS::EC2::Instance'}

# nfs
if (fs_type == "nfs"):
    json_dict['Resources']["nfs"] = \
     {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                               u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                               u'KeyName': {u'Ref': u'KeyName'},
                               u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                                 u'BlockDeviceMappings' : [
                                            {
                                              "DeviceName" : "/dev/sdb",
                                              "Ebs" : {"VolumeSize" : "100"}
                                            },
                                 ],
                               u'Tags': [{u'Key': u'Name',
                                          u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'nfs']]}},
                                         {u'Key': u'Role', u'Value': u'NFS'},
                                         ]},
               u'Type': u'AWS::EC2::Instance'}

# dns
if args.dns:
    json_dict['Resources']["dns"] = \
     {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                               u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                               u'KeyName': {u'Ref': u'KeyName'},
                               u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                               u'Tags': [{u'Key': u'Name',
                                          u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'dns']]}},
                                         {u'Key': u'Role', u'Value': u'DNS'},
                                         ]},
               u'Type': u'AWS::EC2::Instance'}

# test
if args.test:
    json_dict['Resources']["test"] = \
     {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                               u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                               u'KeyName': {u'Ref': u'KeyName'},
                               u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                               u'Tags': [{u'Key': u'Name',
                                          u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'test']]}},
                                         {u'Key': u'Role', u'Value': u'TEST'},
                                         ]},
               u'Type': u'AWS::EC2::Instance'}

# HAProxy
for i in range(1, args.haproxy + 1):
    json_dict['Resources']["haproxy%i" % i] = \
        {u'Properties': {u'ImageId': {u'Fn::FindInMap': [args.rhua, {u'Ref': u'AWS::Region'}, u'AMI']},
                               u'InstanceType': args.r3 and u'r3.xlarge' or u'm3.large',
                               u'KeyName': {u'Ref': u'KeyName'},
                               u'SecurityGroups': [{u'Ref': u'RHUIsecuritygroup'}],
                               u'Tags': [{u'Key': u'Name',
                                          u'Value': {u'Fn::Join': [u'_', [ec2_name, args.rhua, fs_type_f, args.iso, u'haproxy%i' % i]]}},
                                         {u'Key': u'Role', u'Value': u'HAProxy'},
                                         ]},
                   u'Type': u'AWS::EC2::Instance'}

if args.vpcid and args.subnetid:
    # Setting VpcId and SubnetId
    json_dict['Outputs'] = {}
    for key in json_dict['Resources'].keys():
        # We'll be changing dictionary so .keys() is required here!
        if json_dict['Resources'][key]['Type'] == 'AWS::EC2::SecurityGroup':
            json_dict['Resources'][key]['Properties']['VpcId'] = args.vpcid
        elif json_dict['Resources'][key]['Type'] == 'AWS::EC2::Instance':
            json_dict['Resources'][key]['Properties']['SubnetId'] = args.subnetid
            json_dict['Resources'][key]['Properties']['SecurityGroupIds'] = json_dict['Resources'][key]['Properties'].pop('SecurityGroups')
            json_dict['Resources']["%sEIP" % key] = \
            {
                "Type" : "AWS::EC2::EIP",
                "Properties" : {"Domain" : "vpc",
                                "InstanceId" : {"Ref" : key}
                               }
            }


json_dict['Outputs'] = {}

json_body = json.dumps(json_dict, indent=4)

region = regioninfo.RegionInfo(name=args.region,
                               endpoint="cloudformation." + args.region + ".amazonaws.com")

if not region:
    logging.error("Unable to connect to region: " + args.region)
    sys.exit(1)

con_cf = cloudformation.connection.CloudFormationConnection(aws_access_key_id=ec2_key,
                                                            aws_secret_access_key=ec2_secret_key,
                                                            region=region)

con_ec2 = ec2.connect_to_region(args.region,
                                aws_access_key_id=ec2_key,
                                aws_secret_access_key=ec2_secret_key)

if not con_cf or not con_ec2:
    logging.error("Create CF/EC2 connections: " + args.region)
    sys.exit(1)

STACK_ID = "STACK" + "-" + ec2_name + "-" + ''.join(random.choice(string.ascii_lowercase) for x in range(10))
logging.info("Creating stack with ID " + STACK_ID)

parameters = []
try:
    if args.parameters:
        for param in args.parameters:
            parameters.append(tuple(param.split('=')))
except:
    logging.error("Wrong parameters format")
    sys.exit(1)

parameters.append(("KeyName", ssh_key_name))

if args.dry_run:
    sys.exit(0)

con_cf.create_stack(STACK_ID, template_body=json_body,
                    parameters=parameters, timeout_in_minutes=args.timeout)

is_complete = False
result = False
while not is_complete:
    time.sleep(10)
    try:
        for event in con_cf.describe_stack_events(STACK_ID):
            if event.resource_type == "AWS::CloudFormation::Stack" and event.resource_status == "CREATE_COMPLETE":
                logging.info("Stack creation completed")
                is_complete = True
                result = True
                break
            if event.resource_type == "AWS::CloudFormation::Stack" and event.resource_status == "ROLLBACK_COMPLETE":
                logging.info("Stack creation failed")
                is_complete = True
                break
    except:
        # Sometimes 'Rate exceeded' happens
        pass

if not result:
    sys.exit(1)

instances = []
for res in con_cf.describe_stack_resources(STACK_ID):
    # we do care about instances only
    if res.resource_type == 'AWS::EC2::Instance' and res.physical_resource_id:
        logging.debug("Instance " + res.physical_resource_id + " created")
        instances.append(res.physical_resource_id)

instances_detail = []
hostsfile = tempfile.NamedTemporaryFile(delete=False)
logging.debug("Created temporary file for /etc/hosts " + hostsfile.name)
yamlfile = tempfile.NamedTemporaryFile(delete=False)
logging.debug("Created temporary YAML config " + yamlfile.name)
for i in con_ec2.get_all_instances():
    for ii in  i.instances:
        if ii.id in instances:
            try:
                public_hostname = ii.tags["PublicHostname"]
            except KeyError:
                public_hostname = ii.public_dns_name
            try:
                private_hostname = ii.tags["PrivateHostname"]
            except KeyError:
                private_hostname = ii.private_dns_name
            try:
                role = ii.tags["Role"]
            except KeyError:
                role = None

            if ii.ip_address:
                public_ip = ii.ip_address
            else:
                public_ip = ii.private_ip_address
            private_ip = ii.private_ip_address

            details_dict = {"id": ii.id,
                            "public_hostname": public_hostname,
                            "private_hostname": private_hostname,
                            "role": role,
                            "public_ip": public_ip,
                            "private_ip": private_ip}

            for tag_key in ii.tags.keys():
                if tag_key not in ["PublicHostname", "PrivateHostname", "Role"]:
                    details_dict[tag_key] = ii.tags[tag_key]

            instances_detail.append(details_dict)

            if private_hostname and private_ip:
                hostsfile.write(private_ip + "\t" + private_hostname + "\n")
            if public_hostname and public_ip:
                hostsfile.write(public_ip + "\t" + public_hostname + "\n")
yamlconfig = {'Instances': sorted(instances_detail[:], lambda x, y: cmp(str(x['Name']), str(y['Name'])), reverse=True)}
yamlfile.write(yaml.safe_dump(yamlconfig))
yamlfile.close()
hostsfile.close()
logging.debug(instances_detail)
master_keys = []
result = []
for instance in instances_detail:
    if instance["public_ip"]:
        ip = instance["public_ip"]
        result_item = dict(role=str(instance['role']), hostname=str(instance['public_hostname']), ip=str(ip))
        logging.info("Instance with public ip created: %s", result_item)
    else:
        ip = instance["private_ip"]
        result_item = dict(role=str(instance['role']), hostname=str(instance['private_hostname']), ip=str(ip))
        logging.info("Instance with private ip created: %s", result_item)
    result.append(result_item)


for instance in instances_detail:
    if instance["private_hostname"]:
        hostname = instance["private_hostname"]
    else:
        hostname = instance["public_hostname"]
    instance['hostname'] = hostname


# output file

if args.output_conf:
    outfile = args.output_conf
else:
    outfile = "hosts_" + args.rhua + "_" + fs_type_f + "_" + args.iso + ".cfg"

try:
    with open(outfile, 'w') as f:
        f.write('[RHUA]\n')
        for instance in instances_detail:
            if instance["role"] == "RHUA":
                f.write(str(instance['public_hostname']))
                f.write(' ')
                f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                f.write(ssh_key)
                if args.ansible_ssh_extra_args:
                    f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                f.write('\n')
        # rhua as nfs
        if fs_type == "rhua":
            f.write('\n[NFS]\n')
            for instance in instances_detail:
                if instance["role"] == "RHUA":
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        # nfs
        elif fs_type == "nfs":
            f.write('\n[NFS]\n')
            for instance in instances_detail:
                if instance["role"] == "NFS":
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        # gluster
        else:
            f.write('\n[GLUSTER]\n')
            for instance in instances_detail:
                if instance["role"] == "CDS":
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        # cdses
        f.write('\n[CDS]\n')
        for instance in instances_detail:
            if instance["role"] == "CDS":
                f.write(str(instance['public_hostname']))
                f.write(' ')
                f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                f.write(ssh_key)
                if args.ansible_ssh_extra_args:
                    f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                f.write('\n')
        # dns
        f.write('\n[DNS]\n')
        if args.dns:
            for instance in instances_detail:
                if instance["role"] == "DNS":
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        else:
            for instance in instances_detail:
                if instance["role"] == "RHUA":
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        # cli
        if args.cli5 or args.cli6 or args.cli7 or args.cli8:
            f.write('\n[CLI]\n')
            for instance in instances_detail:
                if instance["role"] == "CLI":
                    # RHEL 5 can't be set up using ansible 2.4+
                    # write the data anyway so the user can see it, but comment it out
                    if instance["OS"] == "RHEL5":
                        f.write('#')
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    # only RHEL >= 6 has ec2-user, RHEL 5 has just root
                    if instance["OS"] == "RHEL5":
                        f.write('ansible_ssh_user=root ')
                    else:
                        f.write('ansible_ssh_user=ec2-user ansible_become=True ')
                    f.write('ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    # https://docs.ansible.com/ansible/latest/porting_guides/porting_guide_2.8.html#python-interpreter-discovery
                    # uncomment if using Ansible older than 2.8
                    #if instance["OS"] == "RHEL8":
                    #    f.write(' ansible_python_interpreter=/usr/libexec/platform-python')
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        # atomic_cli
        if args.atomic_cli:
            f.write('\n[ATOMIC_CLI]\n')
            for instance in instances_detail:
                if instance["role"] == "ATOMIC_CLI":
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    f.write('atomic=True ansible_ssh_user=cloud-user ansible_become=True ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        # test
        if args.test:
            f.write('\n[TEST]\n')
            for instance in instances_detail:
                if instance["role"] == "TEST":
                    f.write(str(instance['public_hostname']))
                    f.write(' ')
                    f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                    f.write(ssh_key)
                    if args.ansible_ssh_extra_args:
                        f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                    f.write('\n')
        # haproxy
        f.write('\n[HAPROXY]\n')
        for instance in instances_detail:
            if instance["role"] == "HAProxy":
                f.write(str(instance['public_hostname']))
                f.write(' ')
                f.write('ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=')
                f.write(ssh_key)
                if args.ansible_ssh_extra_args:
                    f.write(' ansible_ssh_extra_args="%s"' % args.ansible_ssh_extra_args)
                f.write('\n')


except Exception as e:
    logging.error("got '%s' error processing: %s", e, args.output_conf)
    sys.exit(1)


# --- close the channels
for instance in instances_detail:
    logging.debug('closing instance %s channel', instance['hostname'])
    try:
        instance['client'].close()
    except Exception as e:
        logging.warning('closing %s client channel: %s', instance['hostname'], e)
    finally:
        logging.debug('client %s channel closed', instance['hostname'])
    logging.debug('closing client %s sftp channel', instance['hostname'])
    try:
        instance['sftp'].close()
    except Exception as e:
        logging.warning('closing %s sftp channel: %s', instance['hostname'], e)
    finally:
        logging.debug('client %s sftp channel closed', instance['hostname'])

# --- dump the result
print '# --- instances created ---'
yaml.dump(result, sys.stdout)
# miserable hack --- cannot make paramiko not hang upon exit
# [revised in February 2017] not necessary anymore
#import os
#os.system('kill %d' % os.getpid())

