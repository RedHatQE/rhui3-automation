About
---------------
Setup of the RHUI 3 Test Framework

Requirements
---------------
Same as the [general RHUI deployment](https://github.com/RedHatQE/rhui3-automation/blob/master/deploy/README.md), plus a ZIP file with the following files in the root of the archive:
* `rhcert.pem` — This must be a valid Red Hat content certificate allowing access to the following products:
  * _Red Hat Update Infrastructure 2.0 (RPMs)_
  * _RHEL RHUI Atomic 7 Ostree Repo_
  * _RHEL RHUI Server 7 Rhgs-server-nfs 3.1 OS_
* `rhui-rpm-upload-test-1-1.noarch.rpm` — This package will be uploaded to a custom repository.
* `rhui-rpm-upload-trial-1-1.noarch.rpm` — This package will also be uploaded to a custom repository.

Usage
--------
You can include the test stage in a RHUI 3 deployment by providing the address of your TEST machine in the `[TEST]` section of the your `hosts.cfg` file; see the [RHUI deployment Readme](https://github.com/RedHatQE/rhui3-automation/blob/master/deploy/README.md). Alternatively, you can install and run the tests at any time after a RHUI 3 deployment by adding (or uncommenting) the `[TEST]`section and running `ansible-playbook` again. Either way, the `ansible-playbook` command line must contain the required ZIP file as a parameter of the `--extra-vars` option.

To install and run the test suite as part of the initial deployment, use the following command:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso extra_files=~/Path/To/Your/file.zip"`

Provide any other optional variables described in the RHUI deployment Readme as needed.

To install the test suite after a completed deployment, use this command instead:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "extra_files=~/Path/To/Your/file.zip" --tags tests`

And then, to run the tests, execute the following command:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --tags run_tests`

The framework will be installed in the `/tmp/rhui3-tests` directory on the TEST machine. The output of the tests will be stored in `/tmp/rhui3test.log` on the TEST machine.
