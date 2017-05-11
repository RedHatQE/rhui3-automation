#!/bin/bash
#
# This is an auxiliary script that can be used to get a list of AMIs which are used in create-cf-stack.py script.
# These AMIs do not change very often, but it's still handy to get them all at once instead of copy&pasting them from Amazon UI.
# Requires a working aws client
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


regions=(us-east-1 ap-southeast-2 eu-west-1 us-west-1 ap-northeast-1 ap-southeast-1 sa-east-1 us-west-2 eu-central-1)

ami_description="RHEL-6.9_HVM_GA-20170309-x86_64-1-Hourly2-GP"

for i in "${regions[@]}"
do
	echo "u'"$i"': {u'AMI': u'"`aws ec2 describe-images --filters "Name=name,Values=*$ami_description*" --query 'Images[*].[{ID:ImageId}]' --region=$i`"'},"
	sleep 5
done

