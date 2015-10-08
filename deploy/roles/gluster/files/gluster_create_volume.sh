#!/bin/bash
#runs command: gluster volume create $volume_name replica $bricks_number $bricks_list

hosts_given=${@:2}
hosts_string=$(tr -d '[,]' <<< $hosts_given)
hosts_array=($hosts_string)
bricks_number=${#hosts_array[@]}
volume_name=$1
bricks_list=''

counter=1
for i in "${hosts_array[@]}"; do
    brick="cds0"$counter".example.com:/export/volume/brick"$volume_name
    counter=$[$counter+1]
    bricks_list=$bricks_list' '$brick
done

gluster volume create 'rhui_content_'$volume_name replica $bricks_number $bricks_list

