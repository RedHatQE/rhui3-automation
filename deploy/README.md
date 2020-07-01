Requirements
---------------
* [Ansible](http://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#latest-release-via-dnf-or-yum) version 2.8 and later.
* Have enough machines running RHEL 7 ready - check the rest of Read Me for details on various RHUI setups.
* Have the latest RHUI 3 ISO or Red Hat CCSP credentials.

Usage
--------

* Run the [stack creation script](../scripts/README.md) to launch VMs and get an inventory file with information about the VMs.
* Run the [deployment script](../scripts/deploy.py) to deploy RHUI on the VMs.

Note that if you use `--rhel7b`, all RHEL 7 systems will get rebooted after the update
to the given compose. Ditto for `--rhel8b`.
This will allow a new kernel to boot, apps to load with a new glibc, etc.

If you want to use Red Hat CCSP credentials instead of the ISO, the credentials file must look
like this:

```
[rh]
username=YOUR_RH_USERNAME
password=YOUR_RH_PASSWORD
````

The deployment script can also read templates for RHEL 7 or 8 Beta URLs
from `~/.rhui3-automation.cfg`; the expected format is as follows:

```
[beta]
rhel7_template=http://host/path/%s/path/
rhel8_template=http://host/path/%s/path/
```

Managed roles
-------------
- Dns
- Rhua
- Cdses
- HAProxy (load balancer)
- Nfs server
- Cli and Atomic Cli (optional)
- [Tests](../tests/README.md) (optional)

Supported configurations
------------------------
The rule of thumb is multiple roles can be applied to a single node.
This allows various deployment configurations, just to outline few:
- Rhua+Dns+Nfs, n\*Cds, m\*HAProxy
- Rhua+Dns, n\*(Cds+Gluster), m\*HAProxy

Please, bare in mind that role application sets node `hostname` such as hap01.example.com, nfs.example.com overriding any hostname previously set (by other role application).
Although all the role hostnames are properly resolvable (through /etc/hosts and optionaly the name server), the last applied hostname will stick to the node.

Configuration Samples
---------------------
Edit your copy of the `hosts.cfg` to meet your preferences:
* example 1:
```ini
# Rhua+Dns+Nfs, 2*Cds, 2*HAProxy
[DNS]
ec2-10.0.0.2.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[NFS]
ec2-10.0.0.2.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[RHUA]
ec2-10.0.0.2.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[CDS]
ec2-10.0.0.3.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
ec2-10.0.0.4.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[HAPROXY]
ec2-10.0.0.5.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[CLI]
ec2-10.0.0.6.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

#[ATOMIC_CLI]
#ec2-10.0.0.7.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

#[TEST]
#ec2-10.0.0.8.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
```

* example 2:
```ini
# Rhua, Dns, 3*(Cds+Gluster), HAProxy
[RHUA]
ec2-10.0.0.1.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[DNS]
ec2-10.0.0.2.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[GLUSTER]
ec2-10.0.0.3.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
ec2-10.0.0.4.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
ec2-10.0.0.5.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[CDS]
ec2-10.0.0.3.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
ec2-10.0.0.4.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
ec2-10.0.0.5.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[HAPROXY]
ec2-10.0.0.6.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
```
Replace _USER_ with the actual local user name and make sure the .pem file has this name.

Check the [hosts.cfg](../hosts.cfg) file for more combinations.


Configuration Limitations
-------------------------
Even though one can apply multiple roles to a single node, some combinations are restricted or make no sense:
- singleton roles --- only one instance per site: Rhua, Nfs, Dns, Proxy, Test
- mutually exclusive roles --- can't be applied to the same node: Rhua, Cds, HAProxy, Proxy (all listen on port 443)
- site-wide mutually exclusive roles --- chose either Nfs or Gluster
- optional roles --- may be absent in one's site: Dns, HAProxy, Proxy, Cli, Atomic Cli, Test
- multi-roles --- usually multiple instances per site: CDS, Gluster, HAProxy, Cli

Important Notes: GlusterFS Configuration
---------------------------------------
The machines that are used for Gluster need to have EC2 Volumes of minimum size of 100GB connected to them!
- Go to EC2 Dashboard > Volumes > Create Volume
- Select volume, right click and do Attach

As of Red Hat Gluster Storage 3.4 at least three Gluster nodes are required, which is why the example above shows three addresses.

Network Ports:
---------------------------------------

* RHUA to cdn.redhat.com 443/TCP
* RHUA to CDSes 22/TCP for initial SSH configuration
* RHUA to HAProxies 22/TCP for initial SSH configuration
* RHUA to itself 5671/TCP for Qpid
* CDS to RHUA 8140/TCP for puppet
* HAProxy to RHUA 8140/TCP for puppet
* clients to CDS or HAProxy 443/TCP
* clients to CDS or HAProxy 5000/TCP for containers
* HAProxy to CDS 443/TCP
* HAProxy to CDS 5000/TCP for containers
* NFS port 2049/TCP on the NFS server
* glusterfs ports 24007/TCP, 49152-4/TCP
