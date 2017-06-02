[Back to top-level README](../../README.md)

ta1-test-harness
===============================================================================
The Lincoln test harness consists of two components, a client component and  a server component.  This document contains instructions for running the test harness components and using it to run the systems under test (SUTs). 

Test Harness Operations
===============================================================================
The client and server test harnesses are used to run the client and the server. Specifically, The client and server harnesses must spawn the client and server. Each harness spawns the SUT right away and then waits to connect to the other component over the network. Nothing will happen until the client and server test harness components have a network connection.  Thus, you can use this as an opportunity to start a third party component (e.g., brokers, policy handlers, etc.).

Specifically, if you need to start the server, then start the third party components, then start the client, you would first start the server *test harness*, which would start your server. Next you would start the third parties, as the test would not start running yet. Then you would start the client by starting the client *test harness*. At 
that point the client and server harnesses would connect to each other and the test would start.

Sample Data and Scripts
===============================================================================
Instructions are included in the [Database Generation Instructions](../user-manuals/DB_GENERATION.md) for generating databases and test scripts. Please follow these instructions to generate sample test scripts that can be used with the test harness. No other sample files will be provided. 

Detailed Instructions
===============================================================================
The steps below give instructions for running the SPARTA server
and client test harnesses. 

## Environment Setup
In this documentation, we will assume that you have already followed the [Database Generation Instructions](../user-manuals/DB_GENERATION.md). In particular, you should have generated a
database and set of test scripts.

## Client Test Scripts
There is a master script file: the one that is passed via the `-c` option to client harness. Note that the client harness controls everything. If the server is going to do anything the client harness will send that command to the server and have it execute it. That way we can be sure only 1 script is running at a time, etc. The master scripts have lines in 1 of 2 formats.

Format 1 is for "unloaded query latency" tests. These tests run a single query, wait for the results of that query, and then they run another one. To run one of these tests you add a line like this:
```
UnloadedQueryRunner queries/q1.sql 5
```

The first input to this command is a path to a file that contains a list of queries to be run, relative to the location of the configuration script. The queries file should contain SQL queries, one per line. Each query must start with the word `SELECT` in all capital letters.

The final token (the 5 in the above example) is the number of times to run each query. In the above example every query in `q1.sql` will be run 5 times. You generally want to have these be about 5 or 10 to get good measurements. As the queries get more expensive and slower, you might want to reduce this value.

Format 2 is for "loaded query latency" or "throughput" tests. It looks like this:
```
VariableDelayQueryRunner q2.sql 2 NO_DELAY
```

The 1st 3 tokens have the same meaning as the `UnloadedQueryRunner`. The addition is the `NO_DELAY` token. That can be either `NO_DELAY` or `EXPONENTIAL_DELAY`. `NO_DELAY` means to run the queries as fast as possible (e.g. as soon as we get a READY send the next query) and is thus a throughput test.

`EXPONENTIAL_DELAY` is for running the loaded query latency tests. `EXPONENTIAL_DELAY` must be followed by an integer specifying the mean delay in microseconds. Thus `EXPONENTIAL_DELAY 2000` means we'll schedule a query to run, and then generate a random, exponentially distributed, delay with a mean delay of 2 millisconds (2000 microseconds). After waiting the amount of time indicated by the random number generator we'll send the next query (provided the SUT is in the `READY` state).

## Server Test Scripts
As before, there is a master script file: the one that is passed via the `-c` option to client harness. Note that the client harness controls everything, even the script with the server-side commands.  If the server is going to do anything the client harness will send that command to the server and have it execute it. That way we can be sure only 1 script is running at a time, etc. The master
scripts have lines in 1 of 2 formats: 

Format 1 is for running "root mode" commands such as CLEARCACHE (which SUTs should interpret as a command to clear any cached query results) and SHUTDOWN. It looks like this:
```
RootModeMasterScript CLEARCACHE
```
or
```
RootModeMasterScript SHUTDOWN
```

This tells the test harness to issue the appropriate root mode command. In both cases the command gets sent to both the client and server.

Format 2 is used to call server-side commands such as update/insert/delete or verify. This takes a command file which specifies the commands to run.  It looks like this:
```
CallRemoteScript server-files/modify-commands
```

This tells the test harness to issue the commands in `server-files/modify-commands` to the server. The format for this command file is as follows.

The first line specifies the type of test it is, for example:
```
UnloadedModifyArgumentScript
```

This indicates that each update command in this file should be run one time without and concurrent operations.  After this, the content of the UPDATE or INSERT operation is given.

In the case of a verify command, the syntax of the command file is just
```
VerifyScript
175
```

where 175 is the ID of the record to verify. This causes the server harness to issue a verify command (i.e., test for existence of a row with that ID) on the specified record.

Running the Harness Components
---------------------------------
In general, the test harness should be invoked with `exec_ta1_test.sh` or the `remote_runner` utility. See the [Database Test Execution Instructions](../user-manuals/DB_TEST_EXECUTION.md) and [remote_runner Documentation](remote_runner.md) for more details. 

Below are some example invocations if you want to execute these binaries on your
own.

To run the client test harness:
```
./ta1-client harness -p ta1-client-main -a "--host=localhost --user=root
                     --db=<testdatabase> --pwd=<password>" -t <testscript> 
                     -n <testcasename> --test_log_dir=<testlogdirectory>
```

To see details about the available flags for the client test harness:
```
./ta1-client harness --help
```

To see details about the available flags for the baseline client:
```
./ta1-client-main --help
```

To run the server test harness:
```
./ta1-server harness -p ./server-main -a "--host=localhost --user=root
                     --db=<testdatabase> --pwd=<password> 
                     -f <trunk>/scripts-config/ta1/config/spar_schema.csv 
                     -s <trunk>/scripts-config/ta1/config/spar_stopwords.txt" 
                     --connect_addr=127.0.0.1 --test_log=<testlogfile>
```

To see details about the available flags for the server test harness:
```
./ta1-server harness -h
```

To see details about the available flags for the baseline server:
```
./ta1-server-main -h
```

TROUBLESHOOTING
===============================================================================
If the execution of the test harness should fail with the error
```
FAILED
Table 'spar.main' doesn't exist
ENDFAILED
```
this means you have not completed the steps described in the [Database Generation Instructions](../user-manuals/DB_GENERATION.md).

Otherwise, if things ever go poorly, tests can be run in debug mode. This is accomplished by appending  `-d directoryname -u` to the end of the client-harness or server-harness command (whichever one you want the debug log for). The directory `directoryname` must already exist. Note that these tests are not meant to be efficient, and thus you shouldn't be concerned about the performance data from these logs. This should purely be used for debugging purposes.

This flag will tell the relevant machine to log all of the commands that it sends and receives, and store these logs in the directory `directoryname`.

In fact, you might be able to take the commands seen in the debug logs and pipe them straight back to the SUT without using the test harness for further troubleshooting. 

For instance, you could use the debug log outputs containing the SUT client's stdin as follows:
```
cat directoryname/sut_stdin | ./client-main --host=10.10.10.221 --pwd=spar --db=testing > debug.log 2> debug_err.log
```

Similarly, on the server, you could `cat directoryname/sut_stdin | ./server-main`.

If you believe that the test harness itself is responsible for a crash, you can inspect `directoryname/sut_stdout`. For instance, the commands:
```
grep '^COMMAND ' directoryname/sut_stdin | wc -l
grep '^READY$' directoryname/sut_stdout | wc -l
```
allow you to observe the number of commands sent and the number of commands received by the test harness.

Note that under normal operation, the system should send a `READY` after initialization completes, a `READY` after `CLEARCACHE` completes (if this is part of the test script), and then one `READY` per `COMMAND` that it receives.

[Back to top-level README](../../README.md)
