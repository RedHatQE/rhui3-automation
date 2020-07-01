About
---------------
Setup of the RHUI 3 Test Framework

Requirements
---------------
* Have Python 2 or 3. Tested on Python 2.7 and 3.6.
* Have the latest released RHUI 3 ISO. If you use an older ISO, you will get failures from the test
cases that cover bug fixes or features from newer releases. Alternatively, you can supply Red Hat
CCSP credentials so that RHUI packages can be installed from the Red Hat CDN.

Note: if you supply the credentials to have the systems registered, remember to unregister
the systems before you delete the stack to save available entitlements.
You can do so by running `rhuiunregistersm` on the test machine.
You can also run this anytime while using the stack.
Should you need to register the systems again while the stack is active, run `rhuiregistersm`.

Environment
---------------
Run the [stack creation script](../scripts/README.md) to launch VMs and get an inventory file
with information about the VMs; be sure to include:
* one or more client machines
* an Atomic client machine
* a test machine

Deployment
--------------
Run the [deployment script](../scripts/deploy.py) to deploy RHUI on the VMs.

You need a ZIP file with the following files in the root of the archive:

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
* `NAME/comps.xml` — These must be package group repodata files for both repository NAMEs defined under `comps` in `rhui3_tests/tested_repos.yaml`. In addition, one of the repositories needs a file named `mod-comps.xml` with an additional group as defined in the same YAML file.

The main and Atomic certificates must not be expired. Expiration is first checked for the "empty",
"incompatible", and "partially invalid" certificates, and the tests that use them are skipped if
the given certificate has already expired.

If you're working on changes to rhui3-automation that aren't in the default branch and you'd like to
apply them before installing rhui3-automation and running tests, you can supply a patch file
with the changes.

Lastly, in order for several test to be able to run, you need a file with valid Red Hat CCSP
credentials and Quay.io credentials. The file must look like this:

```
[rh]
username=YOUR_RH_USERNAME
password=YOUR_RH_PASSWORD

[quay]
username=YOUR_QUAY_USERNAME
password=YOUR_QUAY_PASSWORD
```

Usage
--------
To install and test RHUI, run:

```
./scripts/deploy.py hosts_ID.cfg --tests X
```

Where _X_ can be one of:

* `all`: to run all RHUI tests
* `client`: to run RHUI client tests
* _name_: to run test\_name\_.py from the [rhui3\_tests](./rhui3\_tests) directory.

Note that it can take a few hours for all the test cases to run.
If you only want to install the test machine, do not use the `--tests` argument.

The test cases will be installed in the `/usr/share/rhui3_tests_lib/rhui3_tests/` directory
and the libraries in the `/usr/lib/pythonVERSION/site-packages/rhui3_tests_lib/` directory
on the TEST machine.
The output of the tests will be stored in a local report file, which will also be available
on the web. The file name and the URL will be printed by Ansible.

If you now want to run the tests, or if you want to run them again, you have two options.
Either use _Ansible_ again as follows:

```
./scripts/deploy.py hosts_ID.cfg --tests X --tags run_tests
```

Or log in to the TEST machine, become root, and run:

`rhuitests X`
