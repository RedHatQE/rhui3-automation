About
---------------
Setup of the RHUI 3 Test Framework

Requirements
---------------
RHUI deployment with the following hosts:

* one RHUA instance
* two CDS instances
* one HAProxy instance
* one client instance
* one atomic client instance
* one test instance

See the [RHUI deployment readme file ](https://github.com/RedHatQE/rhui3-automation/blob/master/deploy/README.md) for details. Also, if you use Gluster instead of NFS, note that you need two more hosts serving as Gluster instances.

In addition, you need a ZIP file with the following files in the root of the archive:

* `rhcert.pem` — This must be a valid Red Hat content certificate allowing access to the following products:
  * _Red Hat Update Infrastructure 2 (RPMs)_
  * _Red Hat Enterprise Linux for SAP (RHEL 7 Server) (RPMs) from RHUI_
* `rhcert_atomic.pem` — This must be a valid Red Hat content certificate allowing access to the following products:
  * _Red Hat Enterprise Linux Atomic Host (Trees) from RHUI_
  * _Red Hat Enterprise Linux Atomic Host (Debug RPMs) from RHUI_
  * _Red Hat Enterprise Linux Atomic Host (RPMs) from RHUI_
* `rhcert_expired.pem` — This must be an expired Red Hat content certificate.
* `rhcert_incompatible.pem` — This must be a Red Hat content certificate containing one or more entitlements that are not compatible with RHUI (containing a non-RHUI repository path).
* `rhui-rpm-upload-test-1-1.noarch.rpm` — This package will be uploaded to a custom repository.
* `rhui-rpm-upload-trial-1-1.noarch.rpm` — This package will also be uploaded to a custom repository.

Usage
--------
You can include the test stage in a RHUI 3 deployment by providing the address of your test instance in the `[TEST]` section and the address of your client instances in the `[CLI]` and `[ATOMIC_CLI]` sections of the `hosts.cfg` file. Alternatively, you can install and run the tests at any time after a RHUI 3 deployment by adding (or uncommenting) the `[TEST]`section and running `ansible-playbook` again. Either way, the `ansible-playbook` command line must contain the required ZIP file as a parameter of the `--extra-vars` option.

To install _and run the whole test suite_ as part of the initial deployment or after a completed deployment, use the following command:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso extra_files=~/Path/To/Your/file.zip"`

Provide any other optional variables described in the RHUI deployment Readme as needed.

Note that it can take 30 to 60 minutes for all the test cases to run. If you only want to install the test machine, add `--skip-tags run_tests` on the command line.

The framework will be installed in the `/tmp/rhui3-tests` directory on the TEST machine. The output of the tests will be stored in `/tmp/rhui3test.log` on the TEST machine.

If you now want to run the whole test suite, or if you want to run it again, you have two options. Either use _Ansible_ again as follows:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --tags run_tests`

Or log in to the TEST machine, become root, enter the `/tmp/rhui3-tests/` directory, and use _nose_ as follows:

`nosetests -vs tests/rhui3_tests`

To run only a single test case, or a subset of the available test cases, speficy the test case(s) as the corresponding `test_XYZ.py` file name(s) on the `nosetests -vs` command line instead of `tests/rhui3_tests`, which is the directory containing all the test cases. For example:

`nosetests -vs tests/rhui3_tests/test_client_management.py`

