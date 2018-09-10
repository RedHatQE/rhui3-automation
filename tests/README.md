About
---------------
Setup of the RHUI 3 Test Framework

Requirements
---------------
Python 2 or 3. Tested on Python 2.6, 2.7, and 3.6.

The latest released RHUI 3 ISO. If you use an older ISO, you will get failures from the test cases that cover bug fixes or features from newer releases.

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
  * _Red Hat Enterprise Linux for SAP (RHEL 6 Server) (RPMs) from RHUI_
  * _Red Hat Enterprise Linux for SAP (RHEL 7 Server) (RPMs) from RHUI_
* `rhcert_atomic.pem` — This must be a valid Red Hat content certificate allowing access to the following products:
  * _Red Hat Enterprise Linux Atomic Host (Trees) from RHUI_
  * _Red Hat Enterprise Linux Atomic Host Beta (Source RPMs) from RHUI_
  * _Red Hat Enterprise Linux Atomic Host (RPMs) from RHUI_
* `rhcert_expired.pem` — This must be an expired Red Hat content certificate.
* `rhcert_incompatible.pem` — This must be a Red Hat content certificate containing one or more entitlements that are not compatible with RHUI (containing a non-RHUI repository path) and no compatible entitlement at all.
* `rhcert_partially_invalid.pem` — This must be a Red Hat content certificate containing one or more entitlements that are not compatible with RHUI (containing a non-RHUI repository path) but also at least one compatible entitlement.
* `rhui-rpm-upload-test-1-1.noarch.rpm` — This package will be uploaded to a custom repository.
* `rhui-rpm-upload-trial-1-1.noarch.rpm` — This package will also be uploaded to a custom repository. It must be signed with the RHUI QE GPG key.
* `test_gpg_key` — This is the RHUI QE public GPG key (0x9F6E93A2).

Lastly, in order for the subscription test to be able to run, you need a file with valid Red Hat credentials allowing access to RHUI. The file must look like this:

```
SM_USERNAME=login
SM_PASSWORD=password
```

Replace `login` with your Red Hat login and `password` with your Red Hat password. Save the file in an appropriate location and give it an appropriate name; for example, `rhaccount.sh`. You can then keep the file this way if you are not worried that someone else could read it, or you can encrypt it using Ansible. To encrypt the file, use the following command in the directory holding the file:

`ansible-vault encrypt rhaccount.sh`

Enter an appropriate encryption password when prompted.

Usage
--------
You can include the test stage in a RHUI 3 deployment by providing the address of your test instance in the `[TEST]` section and the address of your client instances in the `[CLI]` and `[ATOMIC_CLI]` sections of the `hosts.cfg` file. Alternatively, you can install and run the tests at any time after a RHUI 3 deployment by adding (or uncommenting) the `[TEST]`section and running `ansible-playbook` again. Either way, the `ansible-playbook` command line must contain the `--extra-vars` switch with the required ZIP file as a parameter of the `extra-files` option and also the required credentials file as a parameter of the `rhaccount` option. If the credentials file is encrypted, you will have to either provide the encryption password interactively or store it in a separate file (however, if someone reads that file, they will be able to read your Red Hat credentials, too, so be careful where you store the file).

To install _and run the whole test suite_ as part of the initial deployment or after a completed deployment, use either the following command if you would like to enter the encryption password by hand:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso extra_files=~/Path/To/Your/file.zip rhaccount=~/Path/To/rhaccount.sh" --ask-vault-pass`

Or the following command if you have stored the encryption password in a separate file:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso extra_files=~/Path/To/Your/file.zip rhaccount=~/Path/To/rhaccount.sh" --vault-password-file ~/Path/To/The/File/With/The/password`

Beware, regardless of the command you use, the credentials file will be stored on the RHUA node, _unencrypted_, as `/tmp/extra_rhui_files/rhaccount.sh`.

Provide any other optional variables described in the RHUI deployment Readme as needed.

Note that it can take a few hours for all the test cases to run. If you only want to install the test machine, add `--skip-tags run_tests` on the command line.

The test cases will be installed in the `/usr/share/rhui3_tests_lib/rhui3_tests/` directory and the libraries in the `/usr/lib/python*/site-packages/rhui3_tests_lib/` directory on the TEST machine. The output of the tests will be stored in `/tmp/rhui3test.log` on the TEST machine.

If you now want to run the whole test suite, or if you want to run it again, you have two options. Either use _Ansible_ again as follows:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --tags run_tests`

Or log in to the TEST machine, become root, and use _nose_ as follows:

`nosetests -vs /usr/share/rhui3_tests_lib/rhui3-tests`

To run only a single test case, or a subset of the available test cases, specify the test case(s) as the corresponding `test_XYZ.py` file name(s) on the `nosetests -vs` command line instead of the directory containing all the test cases. For example:

`nosetests -vs /usr/share/rhui3_tests_lib/rhui3-tests/test_client_management.py`

