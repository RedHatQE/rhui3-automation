About
---------------
Setup of the RHUI 3 Test Framework

Requirements
---------------
Python 2 or 3. Tested on Python 2.7, and 3.6.

The latest released RHUI 3 ISO. If you use an older ISO, you will get failures from the test cases that cover bug fixes or features from newer releases.

RHUI deployment with the following hosts running RHEL 7:

* one RHUA instance
* at least one CDS instance if using NFS, at least three if using Gluster
* one HAProxy instance
* one client instance; it can be running RHEL 6, 7, or 8, regadless of the RHEL version on the RHUA
* one atomic client instance
* one test instance

See the [RHUI deployment readme file ](https://github.com/RedHatQE/rhui3-automation/blob/master/deploy/README.md) for details.

In addition, you need a ZIP file with the following files in the root of the archive:

* `rhcert.pem`, `rhcert_atomic.pem` — These must be valid Red Hat content certificates allowing access to the products that provide the repositories configured in `rhui3_tests/tested_repos.yaml`.
* `rhcert_empty.pem` — This must be a Red Hat content certificate containing no entitlement.
* `rhcert_expired.pem` — This must be an expired Red Hat content certificate.
* `rhcert_incompatible.pem` — This must be a Red Hat content certificate containing one or more entitlements that are not compatible with RHUI (containing a non-RHUI repository path) and no compatible entitlement at all.
* `rhcert_partially_invalid.pem` — This must be a Red Hat content certificate containing one or more entitlements that are not compatible with RHUI (containing a non-RHUI repository path) but also at least one compatible entitlement.
* `rhui-rpm-upload-test-1-1.noarch.rpm` — This package will be uploaded to a custom repository.
* `rhui-rpm-upload-trial-1-1.noarch.rpm` — This package will also be uploaded to a custom repository. It must be signed with the RHUI QE GPG key.
* `rhui-rpm-upload-tryout-1-1.noarch.rpm` — This package will also be uploaded to a custom repository. It must be signed with a key different from RHUI QE.
* `test_gpg_key` — This is the RHUI QE public GPG key (0x9F6E93A2).
* `ANYTHING.tar` — These must be tarballs containing some packages and their `updateinfo.xml.gz` files. The contents will be used for updateinfo testing. Exact names are to be specified in `rhui3_tests/tested_repos.yaml`. One of them must also contain an uncompressed updateinfo file.
* `legacy_ca.crt` — This must be a CA certificate taken from a different RHUI environment; ie. `/etc/pki/rhui/certs/entitlement-ca.crt`. The file will be used in legacy CA testing.

The main and Atomic certificates must not be expired. Expiration is first checked for the "empty", "incompatible", and "partially invalid" certificates, and the tests that use them are skipped if the given certificate has already expired.

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
You can include the test stage in a RHUI 3 deployment by providing the address of your test instance in the `[TEST]` section and the address of your client instances in the `[CLI]` and `[ATOMIC_CLI]` sections of the `hosts.cfg` file. Alternatively, you can install and run the tests at any time after a RHUI 3 deployment by adding (or uncommenting) the `[TEST]`section and running `ansible-playbook` again. Either way, the `ansible-playbook` command line must contain the `--extra-vars` switch with the required ZIP file as a parameter of the `extra-files` option, the required credentials file as a parameter of the `rhaccount` option, and the `tests` variable with `all`, `client`, or a test name as its parameter; the test name is the part of the file name in the `rhui3_tests` directory between `test` and the extension. If the credentials file is encrypted, you will have to either provide the encryption password interactively or store it in a separate file (however, if someone reads that file, they will be able to read your Red Hat credentials, too, so be careful where you store the file).

To install _and run the whole test suite_ as part of the initial deployment or after a completed deployment, use either the following command if you would like to enter the encryption password by hand:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso extra_files=~/Path/To/Your/file.zip rhaccount=~/Path/To/rhaccount.sh tests=all" --ask-vault-pass`

Or the following command if you have stored the encryption password in a separate file and you only want to run the client tests:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --extra-vars "rhui_iso=~/Path/To/Your/RHUI.iso extra_files=~/Path/To/Your/file.zip rhaccount=~/Path/To/rhaccount.sh tests=client" --vault-password-file ~/Path/To/The/File/With/The/password`

Beware, regardless of the command you use, the credentials file will be stored on the RHUA node, _unencrypted_, as `/tmp/extra_rhui_files/rhaccount.sh`.

Provide any other optional variables described in the RHUI deployment Readme as needed.

Note that it can take a few hours for all the test cases to run. If you only want to install the test machine, do not use the `tests` parameter among the extra variables on the command line.

The test cases will be installed in the `/usr/share/rhui3_tests_lib/rhui3_tests/` directory and the libraries in the `/usr/lib/pythonVERSION/site-packages/rhui3_tests_lib/` directory on the TEST machine. The output of the tests will be stored in a local report file, which will also be available on the web. The file name and the URL will be printed by Ansible.

If you now want to run the tests, or if you want to run them again, you have two options. Either use _Ansible_ again as follows:

`ansible-playbook -i ~/pathto/hosts.cfg deploy/site.yml --tags run_tests --extra-vars tests=all`

Or log in to the TEST machine, become root, and run:

`rhuitests all`

Alternatively, you can run only the client tests while logged in to the system:

`rhuitests client`

Lastly, to run only a single test case, e.g. `test_XYZ.py`:

`rhuitests XYZ`
