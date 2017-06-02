[Back to top-level README](../../README.md)

Database Test Execution User Manual
===============================================================================
Executing TA1 tests primarily leverages the script `scripts-config/ta1/scripts/exec_ta1_test.sh`. This document covers prerequisites for using the script, how to execute it, and what to do when the script is done.

Prerequisites
===============================================================================
The following must be done prior to proceeding:

- Execute all relevant steps in [Installation Instructions](../INSTALL.md) (including the setup of MariaDB).
- Execute all relevant steps in [Database Generation](DB_GENERATION.md) (including the generation of queries).
  - **`NOTE`** While your database can be generated on whatever node you please, note that you will likely want to make a copy of the directories where your results database (which contains information on all the queries generated and what their correct answers are) and test scripts/queries (which will be needed by `exec_ta1_test.sh`) were generated. By default, this will be `~/spar-testing/results` and `~/spar-testing/tests` on the machine you ran database/query generation on. You should copy the results databases, test scripts, and queries to the machine you will execute `exec_ta1_test.sh` from, and by default the script will expect these to live in `~/spar-testing/results` and `~/spar-testing/tests`.
- The nodes that you plan to use to execute your test should generally have the following dependencies installed (via `apt-get install`:
  - `libboost-all-dev`
  - `libmariadbclient-dev`
  - `libevent-dev`
  - `openssl`
- It is recommended that you set up passwordless SSH for a user that you use to run all your tests. This will greatly reduce the chance that `exec_ta1_test.sh` will get confused about file paths, how it archives logs, etc.

## Creating your hosts files
You must create a hosts file (preferably in `scripts-config/common/config/hosts/`) that accurately reflects your network.

**`NOTE`** We strongly recommend having two network interfaces on all machines involved in your test: one that your system under test uses to communicate with itself (e.g., for server-client communications), and one that your test infrastructure uses to communicate with your system under test (e.g., for copying logs from your client and server executables back to your test node). It's therefore prudent to create two versions of your hosts file (one version for each set of network interfaces) so you can specify one as `--run-hosts-file` and the other as `--archive-hosts-file`. 

You may use the existing `localhost_only.csv` file as a reference. `localhost_only.csv` is only appropriate if your entire test (e.g., server, client, and possibly third parties) can all run on the same machine you launch `exec_ta1_test.sh` from. 

New hosts files should have the following comma separated fields after the header:
  - column 0: host name; if you do not have DNS setup, this should be the host IP address
  - column 1: host IP address (include this even if you put the IP address in the first column)
  - column 2: number of physical cores available on the machine
    - **`NOTE`** this field is not currently used, even though there were plans to use this to core-pin certain executables to a particular number of cores for certain experiments
  - column 3: name for the workstation model; should be able to uniquely identify a certain hardware configuration 
    - **`NOTE`** this field is not currently used, even though there were plans to use this to launch certain executables on all workstations of a particular model
  - column 4: whether the workstation CPU is hyperthreaded [y/n] 
    - **`NOTE`** like the field related to number of cores, this is not currently used

## Creating your `remote_runner` configuration file
If you are using `exec_ta1_test.sh` to run tests on a relational database that is **not** MariaDB or MySQL, you will need to make a copy of `scripts-config/ta1/remote_runners/exec_ta1_test/baseline_config.py` and create your own version that reflects your particular application. 

**`NOTE`** Your application must be able to communicate with the `ta1-test-harness` binary over stdin/stdout (see [TA1 Test Harness Documentation](../tool-docs/ta1-test-harness.md) for more information).

To make a version of `baseline_config.py` work for your application, you must at least do the following (see [remote-runner Documentation](../tool-docs/remote_runner.md) for more information):
  - Update the "Client SUT" section. You should update the `client.executable` field for both local and remote invocations, the `client.args` list for the command-line parameters of your client, and the `client.files` map for remote invocations for all the file dependencies you need to copy over to the remote node that will execute the client.
  - Update the "Server SUT" section in a similar manner.
  - As needed, add sections for any third parties you need to run in addition to the client and server. Note that these will not be spawned by any test harness, and will be spawned exactly as if you had launched the executable on its own. You can copy the Client or Server SUT sections as examples, but you will only need to specify the following component fields:
    - name (which must start with `"third-party-"`)
    - host (which can be a host name or IP address)
    - executable (which should just be your executable's name)
    - args (which should be a list of strings for each command-line parameter passed to your executable)
    - files (which should be a dictionary of source-to-destination mappings of all file dependencies for your third party component)

User Manual
===============================================================================

**1)** Run through the [Installation Instructions](../INSTALL.md), the [Database Generation User Manual](DB_GENERATION.md), and the general prerequisites above regarding hosts file. If you deviated from any of the default setup, please keep those in mind as you proceed.

**2)** Run `fill_ta1_db.sh` only from the following directory:
```
cd scripts-config/ta1/scripts
```

**3)** View command line help for `fill_ta1_db.sh`:
```
./exec_ta1_test.sh --help
```

**`NOTE`** It is recommended to conduct all the following within a `screen` or `tmux` session, so you can disconnect from/share/restart sessions without losing progress.

**`NOTE`** From here on, sample command line entries use some default/placeholder values for example purposes. You should replace these with values that make sense for your task.

**4)** For all the hosts involved in your test, it's a good idea to do a quick `ping` to confirm that you can connect to all destinations.

**5)** It is also recommended to confirm that the clocks on all your hosts are synchronized, and that the clock skew is not significant (you can accomplish this by remotely executing `date` commands to all your hosts and compare the results to locally executed `date` commands). 

**6)** Execute `exec_ta1_test.sh` with your desired parameters within a `script` command to save the script's output for your records/debugging purposes. 

Note that you must have local copies of test scripts/queries to submit to your system under test; these would have been generated either manually or by following the [Database Generation User Manual](DB_GENERATION.md) and executing with the `--generate-queries` option.

The following is a sample invocation with the client and server both executing on the same host that you execute `exec_ta1_test.sh` from (note that this implies that you have locally generated and configured a MariaDB database):
```
script -c './exec_ta1_test.sh --test-case 00119_smoketest_latency_select_id 
                              --database 1krows_100Bpr 
                              --results-db ~/spar-testing/results/results_databases/1krows_100Bpr.db 
                              --schema ../config/database_schemas/100Bpr_with_hashes.csv'
```

The above invocation relies mostly on the default parameters for `exec_ta1_test.sh`, but will execute the test case `00119_smoketest_latency_select_id` (which is assumed to reside as a `.ts` file in the default location: `~/spar-testing/tests/MDB/qkrows_100Bpr/`) on a local database named `1krows_100Bpr` (which presumably has 1000 rows that use the 100 byte/row schema). This will be executed as an "MDB" test by default, but you can choose a different label for this test by specifying the `--performer` option (this is just a means for organizing test results, especially for when you auto-generate reports and want to compare a specific set of tests with a certain label with another labeled set of tests). `exec_ta1_test.sh` will auto-spawn our baseline implementation of a MariaDB client and server (which needed to have been built and installed to the `bin/` directory by `scons install`) on `localhost`. `exec_ta1_test.sh` will ensure that these are spawned by our test harness software (which also needed to have been built and installed to `bin/` by SCons), and will also ensure that the results from this test case are archived to `~/spar-testing/archive/MDB/1krows_100Bpr` and parsed into the SQlite database specified by `--results-db`. Phew!

The following is a sample invocation with the client and server executing on remote hosts:
```
script -c './exec_ta1_test.sh --test-case 00126_smoketest_latency_select_id 
                              --database 1krows_100kBpr 
                              --results-db ~/spar-testing/results/results_databases/1krows_100kBpr.db 
                              --schema /home/<USER>/repos/sparta/scripts-config/ta1/config/database_schemas/100kBpr_index_all_notes_with_hashes.csv 
                              --server-host-th remote-host-01-eth1
                              --server-host-perf remote-host-01-eth2
                              --client-host-th remote-host-02-eth1
                              --client-host-perf remote-host-02-eth2
                              --run-hosts-file /home/<USER>/repos/sparta/scripts-config/common/config/hosts/eth2_hosts.csv 
                              --archive-hosts-file /home/njhwang/repos/sparta/scripts-config/common/config/hosts/eth1_hosts.csv`
```

The above invocation again relies on a lot of default parameters, but at a high level, executes the test case `00126_smoketest_latency_select_id` on a database named `1krows_100kBpr` that is hosted on `remote-host-01`. In this invocation, we assume that DNS has been set up to provide different host names for `remote-host-01` and `remote-host-02` for two different network adapters on each host (`eth1` and `eth2`). We specify that the "test harness" host should always be the `eth1` version of the host name (i.e., `remote-host-01-eth1` and `remote-host-02-eth1`), and that the "performance" host should be the `eth2` version of the host name (i.e., `remote-host-01-eth2` and `remote-host-02-eth2`). This will make sure that the test harnesses communicate with each other over the IPs specified in `--run-hosts-file` corresponding to the `eth1` adapters, and that the server and client communicate with each other over the `eth2` adapters (so as to isolate the server/client traffic from the "test orchestration" traffic). The results from the test will be auto-archived (and the log copies will traverse the `eth1` network, per `--archive-hosts-file`), and parsed into the SQlite database specified by `--results-db`. Phew!

At a high level, `exec_ta1_test.sh` performs the following tasks:
- Copy all requisite files to all hosts involved in the test (using what you define as the server/client/third-party hosts, your hosts file, and the files specified in `baseline_config.py` (or whichever `remote_runner` configuration file you chose). By default, binaries will be copied to `~/spar-testing/bin` on remote hosts, test scripts will be copied to `~/spar-testing/tests`, and other files (e.g., schema files) will be copied to `~/spar-testing/config`.
- Start `screen` sessions on all remote hosts.
- Spawn test harnesses along with their respective server and client executables (which are defined in your `remote_runner` configuration file). The test script specified by `--test-case` will be executed, and the test will begin.
- After the test completes, collect all logs that were generated from the test and place them in (by default) in `~/spar-testing/archive` on the workstation from which you executed `exec_ta1_test.sh`.
- Parse the results of the test, and place them in a SQlite results database located (by default) at `~/spar-testing/results/results_database/results-<database_name>.db` (which is later used by analysis and report generation tools).

**7)** While the test is running, you can gauge the test's progress by going to (by default) the `~/spar-testing/results` directories on all involved hosts and finding the log directory associated with your test (you will need to know the "performer" you used to label the test, the test case name, and the start time of your test). You should see non-zero sized log files being populated, and can do a `less` on them to see how things are going.

You can also perform a `screen -r` on the screen session corresponding to your test (again, named by the "performer" you used to label the test, the test case name, and the start time of your test) on any related hosts. This allows you to attach to the screen session the test harness is being executed within; be careful not to interfere with the execution of the test (i.e., do not do a `Ctrl-C`). You can detach from the screen session by executing `Ctrl-A d`.

**8)** Once the test is complete, you may:
- Continue to run more tests.
- Browse the generated logs in (by default) `~/spar-testing/archive` to see how the test went.
- Use SQlite to browse the parsed results in the results database (via `sqlite3` on the results database and running `select` statements on the `performer_queries` table).

**`NOTE`** During parsing, you may see warnings such as `Skipping unrecognized line pattern`; these are inconsequential and merely refer to items in the test harness logs that are not relevant to determining how long database operations took.

Known Issues
===============================================================================
- **`KNOWN ISSUE`** `exec_ta1_test.sh` does not robustly detect if the `remote_runner` invocation returns a non-zero exist status. This may cause the script to continue and try to archive results that don't exist (or use ill-defined paths to try an archive results). If you notice `exec_ta1_test.sh` attempting to archive your entire filesystem, `Ctrl-C` and investigate...
- **`KNOWN ISSUE`** There is code commented out in `remote_runner.py` that attempts to also archive the stdout/stderr of the executables run by `exec_ta1_test.sh`; this would allow operators to archive the actual terminal output of the test harness and server/client/third-party binaries. As useful as this would be, it currently doesn't work. The workaround is for operators to login to the remote hosts that are used to run tests and attach to the `screen` sessions spawned by `remote_runner` to view the stdout/stderr of these executables.
- **`KNOWN ISSUE`** If `exec_ta1_test.sh` hangs at `Waiting for components requiring wait to complete`, then the current code requires you to kill processes in a very particular way. The way `remote_runner` works is that it first translates your `remote_runner` configuration file into a Bash script that is executed on the remote systems. These Bash scripts will launch the test harness and the system under test, but will also create a PID file that is monitored by `remote_runner` to determine when processes complete. `remote_runner` will wait until the PID file indicates the test harness (and by extension the system under test) has completed execution. Therefore, the "graceful" way to recover from a hung state is to login to the remote host and manually kill the **test harness** process. This will allow the Bash script created by `remote_runner` to detect end-of-process properly. So long story short, never kill processes that look like `client-harness-remote-runner-script.sh` and always lean towards killing the process that looks like `ta1-client-harness` with a long string of arguments.
- **`KNOWN ISSUE`** `remote_runner` seems to hang when a source file is not found; you will see an error message indicating that it could not find a file that was labeled as a depenency for the `remote_runner` task, but you will have to `Ctrl-C` to debug and rerun.
- **`WARNING`** Avoid using relative paths in any of the arguments you pass to `exec_ta1_test.sh` as unexpected things may happen (especially if you are spawning components on remote hosts with a different user name than the one you are using to execute `exec_ta1_test.sh`).
- **`WARNING`** You may notice that your first execution of `exec_ta1_test.sh` will copy a lot of files over to remote hosts. This is because the easiest way for us to make sure that remote hosts have enough information to execute a test script was to copy all the test queries over to remote hosts. So you will see that a lot of `.q` files are copied; rest-assured that `remote_runner` never does unnecessary file transfers, and should be able to quickly determine that these files do not need to be re-copied for every invocation of `exec_ta1_test.sh`.
- **`KNOWN ISSUE`** Archiving and parsing logs currently relies on passwordless SSH for all hosts defined in the hosts file.
- **`KNOWN ISSUE`** You may see errors if you do not run any components on `localhost`, as `exec_ta1_test.sh1` currently always attempts to do a `cp -r` command to copy and local results if they exist; if these results don't exist, you will see an inconsequential error near the end of your `exec_ta1_test.sh` invocation.

[Back to top-level README](../../README.md)
