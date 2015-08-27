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
Managed nodes:
- DNS
- RHUA
- CDSes
