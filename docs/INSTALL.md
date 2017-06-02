[Back to top-level README](../README.md)

Installation Instructions
===============================================================================

The `setup/` directory contains a set of scripts that assist in setting up a SPARTA Ubuntu environment capable of running the SPARTA framework. This includes test case generators, test harnesses, baseline comparison software configuration, and test data analysis tools.
 
Setup Instructions
===============================================================================

Prerequisites
-------------------------------------------------------------------------------
The following requirements must be met before continuing:
- **`EXTERNAL DEPENDENCY`** Run on at least Ubuntu 12.04 LTS (this document was last verified to work on Ubuntu 14.04 LTS)
- Use an account with `sudo` privileges
- Clone the SPARTA repository on your system
  - **`WARNING`** Many scripts assume that the SPARTA repository is cloned to ~/spar-testing/sparta; if this is not the case, some scripts may not work as expected with the default command-line parameters.
- Establish network connectivity for apt-get and pip package installations (pip, a Python package manager, will be installed for you if it isn't already)
- If necessary, set up your proxy information
- Change to the `setup/` directory of the repository (most instructions will be
relative to this directory, unless otherwise specified)

Installing dependencies
-------------------------------------------------------------------------------
The following script Installs the base set of Ubuntu packages. This may take a long time, and will request a password for sudo access.
```
# From within setup/ directory
./apt-install.sh
```

Setting up a SPARTA Python virtualenv
-------------------------------------------------------------------------------
It is recommended to create a Python virtualenv for all SPARTA dependencies. This establishes a Python environment specifically for SPARTA that will not conflict with your currently installed Python modules. If you are not familiar with virtualenvs, please consult the [virtualenv](https://virtualenv.pypa.io/en/latest) and [virtualenvwrapper](virtualenvwrapper.readthedocs.org/en/latest) documentation.

If you are not familiar with virtualenvs and/or do not care what virtualenvs are created on your system, then you should use our setup script.
```
# From within setup/ directory
./ubuntu-virtualenv-setup.sh
```

Next, set the `$WORKON_HOME` environment variable (in your `~/.bashrc` file, or whereever you prefer to initialize environment variables) to a directory that will contain all the virtualenvs you ever create. You can set this to `~/.virtualenvs`, which is what `ubuntu-virtualenv-setup.sh` temporarily uses by default. You may want to set `$WORKON_HOME` to a value of your choice, and modify `ubuntu-virtualenv-setup.sh` accordingly. Note that you cannot just move the contents of `~/.virtualenvs` to another location, as many symlinks and such would need to be udpated to reflect the new location.

If you are already using Python virtualenvs on your system:
- `base-virtualenv-setup.sh` creates a virtualenv named `base` that contains the `virtualenv` module. When other virtualenvs are created with this as a base, they are guaranteed to be using a stable version of the `pip` and `distribute` modules. See this [Stack Overflow question](stackoverflow.com/questions/4324558/whats-the-proper-way-to-install-pip-virtualenv-and-distribute-for-python) for details.
- `sparta-virtualenv-setup.sh` creates a `sparta` virtualenv based on the `base` virtualenv. This virtualenv will contain all the Python modules needed for the SPARTA framework. 

If you don't like the idea of having a `base` virtualenv and/or want to customize your own virtualenv for use with SPARTA, you can look at the contents of `sparta-virtualenv-setup.sh`.

Activating and deactivating the SPARTA virtualenv
-------------------------------------------------------------------------------
Once you have successfully set up the `sparta` virtualenv (or whatever you chose to call it, if you set it up yourself), you simply type the following to activate the virtualenv and gain access to all its modules:

```
workon sparta
```

You will see the prefix `(sparta)` appear on your command line to indicate that you are inside a virtualenv.

When you wish to leave the virtualenv, type the following:

```
deactivate
```

Building SPARTA binaries and libraries
-------------------------------------------------------------------------------
**`EXTERNAL DEPENDENCY`** Building C++ SPARTA code was last verified to compile with g++ 4.8.2. Future versions of g++ may not cleanly compile.

To build the framework, first activate the `sparta` virtualenv. This is required to build some Cython objects for synthetic database generation.

```
workon sparta
```

Navigate to the repository's root and clean any previous build artifacts.

```
# From root of repository
scons --clean
```

Make an optimized build...
```
# From root of repository
scons --opt
```
...or a debug build (slower performance, but will include additional internal checks and debug print statements).
```
# From root of repository
scons
```

A successful build should result in the following command-line output:
```
scons: done building targets.
```

**`KNOWN ISSUE`** There are some quirks with the current build, and building may fail the first time due to some improper working directory changes. Running the `scons --opt` or `scons` command again should fix the problem. You will see errors similar to the following:
```
os.chdir('/home/njhwang/repos/sparta') 
scons: building terminated because of errors.
```

Installing SPARTA binaries and scripts
-------------------------------------------------------------------------------
To install the primary binaries and scripts used for testing, from the root of the repository, the following command will install them to the `bin/` directory (relative to the root of the repository). Remove the `--opt` to install the debug versions of the binaries and scripts.
```
# From root of repository
scons --opt install
```

Running SPARTA unit tests
-------------------------------------------------------------------------------
To confirm that the framework is fully compatible with your setup, it is a good idea to run our suite of unit tests.

From the root of the repository, the following command will run all C++, Java, and Python unit tests (remove the `--opt` to run the debug versions of the unit tests).
```
# From root of repository
scons --opt test
```

**`KNOWN ISSUE`** Many unit tests are probabilistic in nature in that they check whether random test samples behave according to various probability distributions (within reasonable tolerances). The active unit tests of this nature may fail on very rare occassions; we generally only activate tests that fail less than 1 out of 100 times.

**`KNOWN ISSUE`** Some unit tests have been commented out of the unit test suite since they have known issues and fail consistently. To run these, you will either need to uncomment these unit tests from the relevant `SConscript` files (in the case of C++ unit tests) or instruct the `unittest` module not to skip them (in the case of Python unit tests). As of August 2014, the following unit tests are commented out:
- `cpp/common/check_test.cc`
- `cpp/common/object_threads_test.cc`
- `cpp/test-harness/ta3/pub-sub-gen/low-match-rate-pub-sub-gen_test.cc`
- `cpp/test-harness/ta3/scripts/setup-master-harness-scripts_test.cc`
- `spar_python/analytics/ta1/parse_server_harness_log_test.py`
- `spar_python/common/distributions/bespoke_distributions_test.py`
- `spar_python/query_generation/fill_matching_record_hashes_test.py`
- `spar_python/query_generation/generators/keyword_query_generator_test.py`
- `spar_python/query_generation/generators/equality_query_generator_test.py`
- `spar_python/query_generation/generators/xml_query_generator_test.py`
- `spar_python/query_generation/generators/foo_query_generator_test.py`
- `spar_python/remote_runner/remote_runner_test.py`
- `spar_python/report_generation/common/graphing_test.py`

Setting up a comparison database system (MariaDB)
-------------------------------------------------------------------------------
If you wish to install a MariaDB comparison baseline, you must additionally install the MariaDB server on your workstation of choice. The MariaDB client was already installed when you ran `apt-install.sh`.

To install the MariaDB server, you may use our setup script.

```
# From within setup/ directory
./mariadb-server-setup.sh
```

For the `root` user, it is recommended you set the password to `SP@RTEST` (you may choose otherwise, but many scripts may no longer work as expected with the default parameters).

Note that the script will also update your `/etc/mysql/my.cnf` file to our recommended settings. You can view more information on these settings by exploring the `setup/mariadb_cf/` directory. We leave the fine-tuning of MariaDB settings (such as setting `datadir` and `tmpdir` to a different location for high performance storage solutions) to the user.

You should then allow your users to remotely access the MariaDB server. The command below shows how to allow the `root` user (with password `SP@RTEST`) to do this. 

```
mysql -u root -p -e "GRANT ALL ON *.* TO 'root'@'%' IDENTIFIED BY 'SP@RTEST'"
```

If you have trouble conducting remote tests, it is possible that you will have to specify an IP address to enable access for. The command below shows how to do this for 192.168.1.10.

```
mysql -u root -p -e "GRANT ALL ON *.* TO 'root'@'192.168.1.10' IDENTIFIED BY 'SP@RTEST'"
```

Additionally, if you plan on running "m-of-n" queries (i.e., `M_OF_N(2, 3, fname="Homer", lname="Simpson", city="Springfield")` would return all rows for which at least two of the listed clauses are true), you must do the following:

```
# From root of repository
sudo cp bin/m_of_n.so `mysql_config --variable=plugindir`
mysql -u root -p < scripts-config/ta1/scripts/m_of_n.sql
```

<!-- TODO add M_OF_N sanity check for user to perform and make sure the above steps worked correctly (e.g., command line invocation of an M_OF_N command on a MariaDB database that is guaranteed to already exist) -->

If you performed any additional MariaDB configuration outside of mariadb-server-setup.sh, you must do the following before continuing:

```
sudo service mysql restart
```

Fetching training data for test data generation
-------------------------------------------------------------------------------
To generate test data, you must download several sets of training data for our data generation tools to use. This dataset is about 6.5 GB, so make sure you have sufficient space and time to complete the download. This will fetch data from the URLs listed in `spar_python/data_generation/learning/url_dict.py`.

```
# Replace <YOUR_DATA_DIRECTORY> with a directory of your choice on a partition with at least 6.5 GB of space
mkdir <YOUR_DATA_DIRECTORY>

# From within spar_python/data_generation/learning/ directory
python get_data.py -d <YOUR_DATA_DIRECTORY>
```

**`WARNING`** Note that there are safeguards built into `get_dict.py` that compare hashes of each item downloaded with the values listed in `url_dict.py`. This was originally to help our team detect whether any items in the source data changed, so that we would know if one dataset we generated would be different from another due to a difference in training data. If you encounter errors similar to "Bad hash for file," this likely means the `url_dict.py` hashes are out of date. If you would like the full intended data set to be used as training data, please update the relevant value in `url_dict.py` after running `hashlib.sha1(file_text).hexdigest()` from a Python shell (after reading the contents of the file in question to the variable `file_text`).

**`KNOWN ISSUE`** Note that there aren't any retries built-in for events such as network outages or timeouts. The script is smart enough to not re-download files that already exist and are uncorrupted, so you could consider running it in a loop if your network seems to be causing stability issues.

Miscellaneous notes and other included setup scripts
-------------------------------------------------------------------------------
The following are brief explanations for the other scripts in this directory
that can be used as needed:

- `arc-setup.sh`
  Sets up Arcanist for use with the Phabricator code review tool.

- `bash-4-2-fix.sh`
  Fixes an issue with Ubuntu 12.04 that prevents proper variable expansion and
  readline behavior on the command line.

- `spar-virtualenv-install.sh`
  Used by ubuntu-virtualenv-config.sh. This does a platform independent set up
  of the SPAR virtualenvs.


[Back to top-level README](../README.md)
