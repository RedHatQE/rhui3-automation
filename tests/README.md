About
---------------
Setup of RHUI3 test framework

Requirements
---------------
* [Ansible](http://docs.ansible.com/ansible/intro_installation.html#latest-release-via-yum) version 2.2.0 and higher. (It's possible that you will get older version using standard distro repositories. Try using "pip install -U ansible" instead. You might need to install easy_install first.)
* RHUI3 set up.

Usage
--------
  To include testing stage in RHUI3 deployment see [RHUI deployment Readme](https://github.com/RedHatQE/rhui3-automation/blob/master/deploy/README.md).
  
  Tests can be run any time after RHUI3 deployment. 
  * Update/create your hosts.cfg file with addresse of MASTER machine in [TESTS] section.
  * To install tests framework be in deploy/ directory and run:
  
  `ansible-playbook -i ~/pathto/hosts.cfg site.yml --tags tests`

It will be installed in /tmp/rhui3-tests directory on MASTER machine.

Optional variables:

`extra_files`=~/Path/To/Your/file.zip - This will upload auxiliary files that might be required by some tests (custom RPMs, certificates, etc.) to the RHUA machine.
  
  * To run tests
    * update file `/tmp/rhui3-tests/tests/rhui3_tests/rhui_manager.yaml` on MASTER machine with a relevant rhui password (default is 'admin') and iso version. 
    * be in deploy/ directory and run:
  
      `ansible-playbook -i ~/pathto/hosts.cfg site.yml --tags run_tests`

