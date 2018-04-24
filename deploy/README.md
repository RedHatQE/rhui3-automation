Requirements
---------------
* [Ansible](http://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#latest-release-via-dnf-or-yum) version 2.5.0 and later.
* Have enough machines ready - check the rest of Read Me for details on various RHUI setups.
* Have RHUI3 ISO.

Usage
--------

* Create a copy of the `hosts.cfg` file and put the addresses of your machines to it. (See [Configuration Samples](#configuration-samples).) Do _not_ edit the `hosts.cfg` file directly as that would prevent you from updating your git clone of rhui3-automation.
* Run:
```
ansible-playbook -i pathto/your_hosts.cfg deploy/site.yml  --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso"
```

Mind the mandatory extra variable `rhui_iso`

Optional variables:

- `common_custom_rpm`=~/Path/To/Your/rh-amazon-rhui-client-rhs30.rpm to setup Gluster
- `haproxy_rpm`=~/Path/To/Your/haproxy.rpm to setup HAProxy on RHEL6
- `upgrade_all_pkg`=yes|no|True|TRUE|false to update ALL packages (taking obsoletes into account) prior to RHUI installation. Mind that it might take more than several minutes.

This is RHUI3.x [Ansible](https://www.ansible.com) deployment automation.
Managed roles:
- Dns
- Rhua
- Cdses
- HAProxy (load balancer)
- Nfs server
- Cli and Atomic Cli (optional)
- [Tests](https://github.com/RedHatQE/rhui3-automation/blob/master/tests/README.md) (optional)

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
# Rhua, Dns, 2*(Cds+Gluster), HAProxy
[RHUA]
ec2-10.0.0.1.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[DNS]
ec2-10.0.0.2.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[GLUSTER]
ec2-10.0.0.3.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
ec2-10.0.0.4.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[CDS]
ec2-10.0.0.3.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
ec2-10.0.0.4.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem

[HAPROXY]
ec2-10.0.0.5.eu-west-1.compute.amazonaws.com ansible_ssh_user=ec2-user ansible_become=True ansible_ssh_private_key_file=/home/USER/.ssh/USER-eu-west-1.pem
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

Important Note: GlusterFS Configuration
---------------------------------------
The machines that are used for Gluster need to have EC2 Volumes of minimum size of 100GB connected to them!
- Go to EC2 Dashboard > Volumes > Create Volume
- Select volume, right click and do Attach

Network Ports:
---------------------------------------

* RHUA to cdn.redhat.com 443/TCP
* RHUA to CDSes 22/TCP for initial SSH configuration
* RHUA to HAProxies 22/TCP for initial SSH configuration
* CDS to RHUA 8140/TCP for puppet
* HAProxy to RHUA 8140/TCP for puppet
* clients to CDS or HAProxy 443/TCP
* clients to CDS or HAProxy 5000/TCP for docker
* HAProxy to CDS 443/TCP
* HAProxy to CDS 5000/TCP for docker
* NFS port 2049/TCP on the NFS server
* glusterfs ports 24007/TCP, 49152-4/TCP
