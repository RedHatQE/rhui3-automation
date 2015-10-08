#!/bin/bash
#feeds gluster peer probe with a relevant number of hosts given in hosts.cfg

hosts_given=$@
hosts_string=$(tr -d '[,]' <<< $hosts_given)
hosts_array=($hosts_string)
counter=2
for i in "${hosts_array[@]:1}"; do
    gluster peer probe "cds0"$counter".example.com"
    counter=$[$counter+1]
done

