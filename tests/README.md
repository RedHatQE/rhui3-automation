About
---------------
Setup of the RHUI 3 Test Framework

Requirements
---------------
* [Ansible](http://docs.ansible.com/ansible/intro_installation.html#latest-release-via-yum) version 2.2.0 or later. (It's possible that you will get an older version using standard distro repositories. Try using `pip install -U ansible` instead. You might need to install `easy_install` first.)
* RHUI 3 installed and configured.

Usage
--------
  To include the test stage in a RHUI 3 deployment, see the [RHUI deployment Readme](https://github.com/RedHatQE/rhui3-automation/blob/master/deploy/README.md).
  
  Tests can be run at any time after a RHUI 3 deployment. To run them:

  * Update or create your `hosts.cfg` file with the address of the TEST machine in the `[TEST]` section.
  * To install the tests framework, run:
  
  `ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --tags tests`

It will be installed in the `/tmp/rhui3-tests` directory on the TEST machine.

Optional variables:

`extra_files`=~/Path/To/Your/file.zip - This will upload auxiliary files that are required by some tests to the RHUA machine. At present, in order for the `test_entitlements.py` and `test_repo_managment.py` test cases to be able to run as expected, you must supply a ZIP file with the following files in the root of the archive:

  * `rhcert.pem` — This must be a valid Red Hat content certificate allowing access to the *Red Hat Update Infrastructure 2.0* repository.
  * `rhui-rpm-upload-test-1-1.noarch.rpm` — This package will be uploaded to a custom repository.

To run the tests:

    * Update file `/tmp/rhui3-tests/tests/rhui3_tests/rhui_manager.yaml` on the TEST machine with a relevant RHUI password (default is 'admin') and ISO version.
    * Execute the following command:
  
      `ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --tags run_tests`

