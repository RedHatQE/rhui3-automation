Requirements
---------------
* Ansible version 1.9.2 and higher. (It's possible that you will get older version using standard distro repositories. Try using "pip install -U ansible" instead. You might need to install easy_install first.)
* Have enough machines ready - check the rest of Read Me for details on various RHUI setups.
* Have RHUI3 ISO.

Usage
--------

* Update/create your hosts.cfg file with adreses of your machines.
* Be in deploy/ directory and run:
```
ansible-playbook -i ~/pathto/hosts.cfg site.yml  --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso"
```

Mind the mandatory extra variable `rhui_iso`

This is RHUI3.x [Ansible](www.ansible.com) deployment automation.
Managed roles:
- Dns
- Rhua
- Cdses
- HAProxy (load balancer)
- Nfs server

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
Edit `hosts.cfg` to meet your preference:
```ini
# Rhua+Dns+Nfs, 2*(Cds+HAProxy)
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
10.0.0.5
10.0.0.6
```

Configuration Limitations
-------------------------
Even though one can apply multiple roles to a single node, some combinations are restricted or make no sense:
- singleton roles --- only one instance per site: Rhua, Nfs, Dns, Master, Proxy
- mutually exclusive roles --- can't be applied to the same node: Rhua, Cds, HAProxy, Proxy (all listen on port 443)
- site-wide mutually exclusive roles --- chose either Nfs or Gluster
- optional roles --- may be absent in one's site: Dns, HAProxy, Master, Proxy, Cli
- multi-roles --- usually multiple instances per site: CDS, Gluster, HAProxy, Cli
