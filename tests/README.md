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
You can include the test stage in a RHUI 3 deployment by providing the address of your TEST machine in the `[TEST]` section and the address of your CLI machine in the `[CLI]` section of the `hosts.cfg` file; see the [RHUI deployment Readme](https://github.com/RedHatQE/rhui3-automation/blob/master/deploy/README.md). Alternatively, you can install and run the tests at any time after a RHUI 3 deployment by adding (or uncommenting) the `[TEST]`section and running `ansible-playbook` again. Either way, the `ansible-playbook` command line must contain the required ZIP file as a parameter of the `--extra-vars` option.

To install and run the test suite as part of the initial deployment or after a completed deployment, use the following command:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso extra_files=~/Path/To/Your/file.zip"`

Provide any other optional variables described in the RHUI deployment Readme as needed.

The framework will be installed in the `/tmp/rhui3-tests` directory on the TEST machine. The output of the tests will be stored in `/tmp/rhui3test.log` on the TEST machine.

If you want to run the test suite again, you have two options. Either use _Ansible_ again as follows:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --tags run_tests`

Or log in to the TEST machine, become root, enter the `/tmp/rhui3-tests/` directory, and use _nose_ as follows:

`nosetests -vs tests/rhui3_tests`

Hint: To run only a single test case, or a subset of the available test cases, speficy the test case(s) on the `nosetests -vs` command line instead of `tests/rhui3_tests`, which is the directory containing all the test cases.
