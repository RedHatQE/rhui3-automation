#!/bin/bash
#
# This is an auxiliary script that can be used to get a list of AMIs which are used in create-cf-stack.py script.
# These AMIs do not change very often, but it's still handy to get them all at once instead of copy&pasting them from Amazon UI.
# Requires a working aws client
#
which aws &> /dev/null
if [ $? -gt 0 ]; then
  echo "The aws client is not available. Please install package awscli."
  exit 1
fi
if [ ! -s ~/.aws/credentials ]; then
  echo "The aws client is not configured. Please run \`aws configure'."
  exit 1
fi
#
# Sample output of this script:
#
#u'us-east-1': {u'AMI': u'ami-9df7548b'},
#u'ap-southeast-2': {u'AMI': u'ami-6b6c6008'},
#u'eu-west-1': {u'AMI': u'ami-75625713'},
#u'us-west-1': {u'AMI': u'ami-3984dd59'},
#u'ap-northeast-1': {u'AMI': u'ami-d4a6f6b3'},
#u'ap-southeast-1': {u'AMI': u'ami-c770c3a4'},
#u'sa-east-1': {u'AMI': u'ami-d24d2cbe'},
#u'us-west-2': {u'AMI': u'ami-e8b93688'},
#u'eu-central-1': {u'AMI': u'ami-3867b357'},
#

regions=$(aws ec2 describe-regions --all-regions --query 'Regions[].{Name:RegionName}' --output text | sort)

if [[ $1 =~ ^RHEL ]]; then
  ami_description=$1
else
  echo "Usage: $0 ami_description"
  exit
fi

for i in $regions
do
	echo "u'"$i"': {u'AMI': u'"`aws ec2 describe-images --filters "Name=name,Values=*$ami_description*" --query 'Images[*].ImageId' --region=$i`"'}," | sed -re 's/\[.*?\"(.+?)\".*\]/\1/'
	sleep 5
done

