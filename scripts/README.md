# RHUI3 automation - scripts

## Create Stack script

Script creates ec2 instance machines (m3.large) according to specification.

Instances are named `$user_name_$RHELrelease_$filesystem_type$iso_date_$role` (*user_RHEL7_nfs_20160809_rhua*)

The script produces an output config file suitable for the RHUI3 ansible installation. [Example](#output-configuration-file) of the output file. Default
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

1. yaml config file with ec2 credentials - default path is `/etc/rhui_ec2.yaml` [(example)](#input-configuration-file)
2. list of AMI in the script needs to be updated (section `json_dict['Mappings']` in the code)

### Usage

Run `scripts/create-cf-stack.py [optional parameters]` [(example)](#usage-example)

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
If there is a separate NFS machine, an extra 100 GB volume is attached to this machine. If not, an extra 100 GB volume is attached to the RHUA machine.

<img src="https://github.com/RedHatQE/rhui3-automation/blob/stack_script/scripts/img/rhui-storage-nfs.png" width="350">

#### Gluster filesystem

Configuration with Gluster filesystem needs at least 2 CDS, 1 HAProxy and RHUA machine. <br />
There is an extra 100 GB volume attached to each CDS machine.

<img src="https://github.com/RedHatQE/rhui3-automation/blob/stack_script/scripts/img/rhui-storage-gluster.png" width="350">

### Examples

#### Usage example

* `scripts/create-cf-stack.py --iso 20160809`
  * basic RHEL6 NFS configuration
  * 1xRHUA=DNS=NFS, 1xCDS, 1xHAProxy
* `scripts/create-cf-stack.py --rhua RHEL7 --tests --gluster --cds 3 --iso 20160809`
  * RHEL7 Gluster configuration
  * 1xRHUA=DNS, 3xCDS, 1xHAProxy, 1xtest_machine
* `scripts/create-cf-stack.py --region eu-central-1 --nfs cli6 2 --haproxy 2 --iso 20160809`
  * RHEL6 NFS configuration on eu-central-1 region
  * 1xRHUA=DNS, 1xNFS, 2xCLI6, 2xHAProxy
* `scripts/create-cf-stack.py --rhua RHEL7 --dns --cds 2 --cli6 1 --cli7 1 --input-conf /etc/rhui_amazon.yaml --output-conf my_new_hosts_config_file.cfg --iso 20160809`
  * RHEL7 NFS configuration
  * 1xRHUA=NFS, 1xDNS, 2xCDS, 1xCLI6, 1xCLI7, 1xHAProxy

#### Input configuration file

Change `ec2-key` and `ec2-secret-key` values to your keys. Change `user` to your username and update path to your pem keys. If region is missing, add it according to the pattern.

```
ec2: {ec2-key: AAAAAAAAAAAAAAAAAAAA, ec2-secret-key: B0B0B0B0B0B0B0B0B0B0a1a1a1a1a1a1a1a1a1a1}
ssh:
  ap-northeast-1: [user-ap-northeast-1, /home/user/.pem/user-ap-northeast-1.pem]
  ap-southeast-1: [user-ap-southeast-1, /home/user/.pem/user-ap-southeast-1.pem]
  ap-southeast-2: [user-ap-southeast-2, /home/user/.pem/user-ap-southeast-2.pem]
  eu-central-1: [user-eu-central-1, /home/user/.pem/user-eu-central-1.pem]
  eu-west-1: [user-eu-west-1, /home/user/.pem/user-eu-west-1.pem]
  sa-east-1: [user-sa-east-1, /home/user/.pem/user-sa-east-1.pem]
  us-east-1: [user-us-east-1, /home/user/.pem/user-us-east-1.pem]
  us-west-1: [user-us-west-1, /home/user/.pem/user-us-west-1.pem]
  us-west-2: [user-us-west-2, /home/user/.pem/user-us-west-2.pem]

```

#### Output configuration file

The output configuration file is needed for the rhui3 ansible installation.

Example of an output file with Gluster configuration (1xRHUA=DNS, 3xCDS, 2xCLI, 1xtest_machine, 1xHAProxy):

```
[RHUA]
ec2-54-170-205-98.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem

[GLUSTER]
ec2-54-78-213-201.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem
ec2-54-78-165-67.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem
ec2-54-155-142-185.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem

[CDS]
ec2-54-78-213-201.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem
ec2-54-78-165-67.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem
ec2-54-155-142-185.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem

[DNS]
ec2-54-170-205-98.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem

[CLI]
ec2-54-155-178-68.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem
ec2-54-228-24-150.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem

[TESTS]
ec2-54-73-34-96.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem

[HAPROXY]
ec2-54-73-134-159.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/user/.ssh/user-eu-west-1.pem

```

### How to delete stack

Stack can be deleted "all in one" with CloudFormation. On the AWS amazon web page go to the CloudFormation service, mark the stack -> Actions -> Delete stack.

Stack is deleted with all its instances, volumes and the security group.

