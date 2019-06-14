#!/bin/bash
# Use this script to log in to all (non-Atomic) hosts that comprise a RHUI cloud formation.
#
# The mandatory first argument is supposed to be the host_*.cfg file created by create-cf-stack.py.
# The optional second argument can contain extra SSH arguments; typically a reverse tunnel
# to a web server in a VPN where an unreleased RHEL Beta compose is available and is needed
# while installing CDS and HAProxy nodes as part of RHUI tests. IOW, if these nodes are running
# an unreleased RHEL version, you need to be logged in to them with the reverse port for the RHUI
# tests to be able to install additional packages on them.
#
# The `cssh' utility is required.
if ! which cssh &> /dev/null; then
  echo "Install cssh first"
  exit 1
fi
if [ "$1" ]; then
  if [ -f $1 ]; then
    file=$1
    hosts=$(awk '/ansible_ssh_user=ec2-user/ { print $1 }' $file | sort -u)
    key=$(grep -m 1 -o 'ansible_ssh_private_key_file=[^ ]*' $file | cut -d = -f 2)
  else
    echo "$1 is not a (hosts) file."
    exit 1
  fi
  cssh -o "-i $key -l ec2-user $2" $hosts
else
  echo "Usage: $0 hosts_file [extra_ssh_arguments, e.g. '-R local_port:server_in_your_vpn:port']"
  exit 1
fi
