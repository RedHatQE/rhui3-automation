# RHUI3 automation - scripts

## Create Stack script

Script creates ec2 instance machines (m3.large) according to specification.

Instances are named `$ROLE_$RHELrelease_$filesystem_type$iso_date_$user_key_name` (*RHUA_RHEL7_nfs_20160809_pbartiko-eu-west-1*)

The script produce output config file suitable for the RHUI3 ansible installation. [Example](/examples/) of the output file. Default
name of the file is `hosts_$RHEL_release_$filesystem_type_$iso.cfg` (*hosts_RHEL7_nfs_20160809.cfg*)

New security group is created. Its name contains stack id. <br />
Inbound rules:

  ```
  22 TCP (SSH)
  53 TCP (DNS)
  53 UDP (DNS)
  80 TCP (HTTP)
  443 TCP (HTTPS)
  2049 TCP (NFS)
  5000 TCP (docker)
  5674 TCP
  8140 TCP (puppet)
  24007 TCP (gluster)
  49152-49154 (gluster)
```

### Requirements

1. yaml config file with ec2 credentials - default path is `/etc/rhui_ec2.yaml` [(example)](/examples/)
2. AMI needs to be updated (section `json_dict['Mappings']` in the code)

### Usage

Run `scripts/create-cf-stack.py [optional parameters]`

Default configuration: 
  * NFS filesystem
  * RHEL6 instances
  * eu-west-1 region
  * instances: 1xRHUA (NFS, DNS), 1xCDS, 1xHAProxy

#### Parameters

  * **--rhua [rhel_version]** - rhel version for rhui setup, `default = RHEL6`
  * **--iso [iso_date]** - iso version to title the instance (as in $user_nick_$RHELrelease_$ROLE_*$iso_date)*
  * **--dns** - if specified, a separate machine for dns, `default = the same as RHUA`
  * **--cds [number]** - amount of CDS machines, `default = 1` (if Gluster filesystem, `default = 2`)
  * **--haproxy [number]** - amount of HAProxies, `default = 1`
  * **--input-conf [name]** - the name of input conf file, `default = "/etc/rhui_ec2.yaml"`
  * **--output-conf [name]** - the name of output conf file, `default = "hosts_$RHELrelease_$iso.cfg"`
  * **--cli5/6/7 [number]** - amount of CLI machines, `default = 0`
  * **--tests** - if specified, TEST/MASTER machine, `default = 0`
  * **--region [name]** - `default = eu-west-1`
  
Mutually exclusive options: 

  * **--nfs** - if specified, nfs filesystem with separate machine and NFS volume (100 GB) attached to this machine
  * **--gluster** - if specified, gluster filesystem with an extra volume attached to each CDS (100 GB)
  
Other options:
  * **--debug** - debug info

### Configuration possibilities

#### NFS filesystem

Configuration with NFS filesystem needs at least 1 CDS, 1 HAProxy and RHUA machine. <br />
If there is separate NFS machine, an extra 100 GB volume is attached to this machine. If not, an extra 100 GB volume is attached to RHUA machine.

<img src="https://github.com/RedHatQE/rhui3-automation/blob/stack_script/scripts/img/rhui-storage-nfs.png" width="350">

#### Gluster filesystem

Configuration with Gluster filesystem needs at least 2 CDS, 1 HAProxy and RHUA machine. <br />
There is an extra 100 GB volume attached to each CDS machine.

<img src="https://github.com/RedHatQE/rhui3-automation/blob/stack_script/scripts/img/rhui-storage-gluster.png" width="350">

### Examples

#### Usage example

* `scripts/create-cf-stack.py --iso 20160809` - basic RHEL6 NFS configuration (1xRHUA=DNS=NFS, 1xCDS, 1xHAProxy)
* `scripts/create-cf-stack.py --rhua RHEL7 --tests --gluster --cds 3 --iso 20160809` - RHEL7 gluster conf. (1xRHUA=DNS, 3xCDS, 1xHAProxy, 1xtest_machine)
* `scripts/create-cf-stack.py --region eu-central-1 --nfs cli6 2 --haproxy 2 --iso 20160809` - RHEL6 NFS conf. on eu-central-1 region (1xRHUA=DNS, 1xNFS, 2xCLI6, 2xHAProxy)
* `scripts/create-cf-stack.py --rhua RHEL7 --dns --cds 2 --cli6 1 --cli7 1 --input-conf /etc/rhui_amazon.yaml --output-conf my_new_hosts_config_file.cfg --iso 20160809` - RHEL7 NFS conf. (1xRHUA=NFS, 1xDNS, 2xCDS, 1xCLI6, 1xCLI7, 1xHAProxy)

#### Input configuration file

#### Output configuration file

### How to delete stack

Stack can be deleted "all in one" with CloudFormation. On the AWS amazon web page go to the CloudFormation service, mark the stack -> Actions -> Delete stack.

Stack is deleted with all its instances, volumes and the security group.

