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
# Usage: you need to change the ami_description variable and run it


regions=(ap-northeast-1 ap-northeast-2 ap-south-1 ap-southeast-1 ap-southeast-2 ca-central-1 eu-central-1 eu-west-1 eu-west-2 sa-east-1 us-east-1 us-east-2 us-west-1 us-west-2)

ami_description="RHEL-7.3_HVM-20170424-x86_64-1-Hourly2-GP2"

for i in "${regions[@]}"
do
	echo "u'"$i"': {u'AMI': u'"`aws ec2 describe-images --filters "Name=name,Values=*$ami_description*" --query 'Images[*].ImageId' --region=$i`"'}," | sed -re 's/\[.*?\"(.+?)\".*\]/\1/'
	sleep 5
done

