Usage
--------

```
ansible-playbook -i hosts.cfg site.yml  --extra-vars "rhui_iso=~/Downloads/RHUI-3.0-RHEL-7-20150807.n.0-RHUI-x86_64-dvd1.iso"
```
Mind the mandatory extra variable `rhui_iso`

This is RHUI3.x [Ansible](www.ansible.com) deployment automation.
Managed nodes:
- DNS
- RHUA
- CDSes
