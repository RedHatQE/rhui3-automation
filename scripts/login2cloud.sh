#!/bin/bash
# Use this script to log in to all (non-Atomic) hosts that comprise a RHUI cloud formation.
#
# The only mandatory argument is supposed to be the host_*.cfg file created by create-cf-stack.py.
# If the hosts file contains extra SSH arguments for Ansible, this script will reuse them.
#
# The `cssh' utility is required.
if ! which cssh &> /dev/null; then
  echo "Install cssh first"
  exit 1
fi
if [ "$1" ]; then
  if [ -f $1 ]; then
    file=$1
    hosts=$(egrep -v 'cloud-user|root' $file | awk '/amazonaws/ { print $1 }' | sort -u)
    key=$(grep -m 1 -o 'ansible_ssh_private_key_file=[^ ]*' $file | cut -d = -f 2)
    if [[ ! $key ]]; then
        key=$(ssh -G $(echo "$hosts" | head -1) | awk '/^identityfile/ { print $2 }' | head -1)
    fi
    ssh_extra_args=$(grep -m 1 -o 'ansible_ssh_extra_args="[^"]*"' $file | cut -d = -f 2 | sed 's/"//g')
  else
    echo "$1 is not a (hosts) file."
    exit 1
  fi
  cssh -o "-i $key -l ec2-user $ssh_extra_args" $hosts
else
  echo "Usage: $0 hosts_file"
  exit 1
fi
