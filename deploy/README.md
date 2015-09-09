Requirements
---------------
* Ansible version 1.9.2 and higher. (It's possible that you will get older version using standard distro repositories. Try using "pip install -U ansible" instead. You might need to install easy_install first.)
* Have 4 machines ready - one for RHUA, one for DNS, two for CDSes.
* Have RHUI3 ISO.

Usage
--------

* Update/create your hosts.cfg file with adreses of your machines.
* Be in deploy/ directory and run:
```
ansible-playbook -i ~/pathto/hosts.cfg site.yml  --extra-vars "rhui_iso=~/Downloads/RHUI-3.0-RHEL-7-20150807.n.0-RHUI-x86_64-dvd1.iso"
```

Mind the mandatory extra variable `rhui_iso`

This is RHUI3.x [Ansible](www.ansible.com) deployment automation.
Managed roles:
- DNS
- RHUA
- CDSes
- HAProxy
- NFS server

Supported configurations
------------------------
The rule of thumb is multiple roles can be applied to a single node.
This allows various deployment configurations, just to outline few:
- RHUA+DNS+NFS, n\*(CDS+HAPROXY)
- RHUA+DNS, n\*(CDS), m\*(HAPROXY+GLUSTER)
- RHUA+DNS, n\*(CDS+HAPROXY+GLUSTER)


Please, bare in mind that role application sets node `hostname` such as hap01.example.com, nfs.example.com overriding any hostname previously set (by other role application).
Although all the role hostnames are properly resolvable (through /etc/hosts and optionaly the name server), the last applied hostname will stick to the node.

Configuration Samples
---------------------
Edit `hosts.cfg` to meet your preference:
```ini
# RHUA+DNS+NFS, 2*(CDS+HAPROXY)
[DNS]
10.0.0.2

[NFS]
10.0.0.2

[RHUA]
10.0.0.2

[CDS]
10.0.0.3
10.0.0.4

[HAPROXY]
10.0.0.3
10.0.0.4
```
