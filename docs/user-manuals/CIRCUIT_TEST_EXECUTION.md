[Back to top-level README](../../README.md)

Circuit Test Execution User Manual
===============================================================================
This guide will show you how to use the SPARTA test harness to evaluate circuits with homomorphic encryption software, or on the SPARTA baseline that evaluates circuits without homomorphic encryption.

The test harness spawns the homomorphic encryption software's server and client, and then it iteratively feeds them key generation, circuit ingestion, encryption, homomorphic evaluation, and decryption requests. The order and contents of these requests are spelled out by a test script.

Prerequisites
===============================================================================
Please execute all relevant steps in [Installation Instructions](../INSTALL.md).

User Manual
===============================================================================
The standard build will generate binaries for the test harness, server baseline, and client baseline in the `bin/` directory.

The first time you use the program, we strongly suggest that you run the following:
```
./ta2-test-harness -h
```

## Testting IBM Circuits
To run the baseline evaluator on all 14 of the IBM test scripts generated in the [Circuit Generation Instructions](CIRCUIT_GENERATION.md) by `generate_all_phase2.sh`, you can execute the following bash command at the terminal from the `spar_python/circuit_generation/ibm` directory (where `$BASEDIR` is the base directory of your SPARTA repository):
```
script -c 
'for f in `seq -f "%02.0f" 1 14`; 
do 
    $BASEDIR/bin/ta2-test-harness -p BASE 
                                  -s $BASEDIR/bin/ta2-ibm-baseline-server
                                  -c $BASEDIR/bin/ta2-dummy-client 
                                  -l phase2_tests/logs/ 
                                  -t phase2_tests/testfile/${f}* 
                                  -n ${f}; 
done;'
```

This will take about 30 seconds to run, depending on the speed of your machine.

``*NOTE*`` The generated tests have hardcoded paths in the test script files, so you must invoke the test harness as shown above from the `spar_python/circuit_generation/ibm` directory.

## Testting Stealth Circuits
To run the baseline evaluator on all 18 of the Stealth tests generated in the [Circuit Generation Instructions](CIRCUIT_GENERATION.md) by `generate_all_phase1.sh`, you can execute the following bash command at the terminal from the `spar_python/circuit_generation/stealth` directory (where `$BASEDIR` is the base directory of your SPARTA repository):
```
script -c 
'for f in `seq -f "%02.0f" 1 18`; 
do 
    $BASEDIR/bin/ta2-test-harness -p BASE 
                                  -s $BASEDIR/bin/ta2-stealth-baseline-server
                                  -c $BASEDIR/bin/ta2-dummy-client 
                                  -l phase1_tests/logs/ 
                                  -t phase1_tests/testfile/${f}* 
                                  -n ${f}; 
done;'
```

This will take about 90 minutes to run, depending on the speed of your machine.

``*NOTE*`` The generated tests have hardcoded paths in the test script files, so you must invoke the test harness as shown above from the `spar_python/circuit_generation/stealth` directory.

## General Notes
You can modify the `-s` and `-c` flags for `ta2-test-harness` to point to a different set of homomorphic encryption software binaries that comply with the test harness' communication protocol. When you run the same test cases against different software, be sure to change the `-p` option to something other than `BASE`. This will allow the report generator to distinguish between runs from the baseline circuit evaluator and a different circuit evaluator.

If the test harness crashes in the middle of a test script, you can resume from the crash point by running the harness again with the `-x` option. This option requires the name of the log file of the test that crashed. It will then resume the test from the point of the crash and append the results to the end of that log file.

Additionally, the harness contains debug options that can be activated with the `-d` flag. You should NOT run the harness in debug mode for any results that you want to score for timing, but it can be useful after a crash to discover where things went wrong.

Building Your Own Binaries
===============================================================================
If you are more adventurous and would like to build our code on your own, this section explains how you can do it. Once you have built the binaries, return to the section above to see how the test harness is used.

All of the test harness, baseline server, and dummy client code is written in C++ and located in `cpp`. You will likely need the following programs/libraries to compile the code (can be installed via `apt-get` in Ubuntu):
- `g++`
- `scons`
- `lemon`
- `flex`
- `libevent-dev`
- `libboost-all-dev`

Once the packages are installed, compiling the code is a simple application of SCons. First, from the base directory, run the following to remove all build files:
```
scons -c --opt
scons -c --opt
```

Note that it's a good idea to run this command twice! 

Then run the following to compile binaries:
```
scons -u --opt
```

If you happen to get an error message, don't worry; just run `scons -u --opt` again and it should work the second time.
 
Then you can run the following to install the binaries to the `bin/` directory:
```
scons -u --opt install
```

Parsing IBM Test Harness Logs
===============================================================================
We have built a Python tool that will aggregate the results from all log files and insert them into the SQLite database (which was constructed back when the circuits were first built). The Python tool lives at `spar_python/analytics/ta2/parse_circuit_log.py`.

The first time you use it, we strongly recommend that you run the program with the `-h` option and review its command-line options.

Assuming you have followed the commands we've listed so far, the IBM results database should live in `spar_python/circuit_generation/ibm/phase2_tests/resultsdb.db` and the log files should live in `spar_python/circuit_generation/ibm/phase2_tests/logs`. You are encouraged to make a copy of the results database prior to parsing logs.

Run the following from the top-level repository directory to parse all the logs and store the parsed results into the results database. This may take several minutes.
```
python spar_python/analytics/ta2/parse_circuit_log.py -i spar_python/circuit_generation/ibm/phase2_tests/logs/ 
                                                      -o spar_python/circuit_generation/ibm/phase2_tests/resultsdb.db
```

``*WARNING*`` While the parser will try to skip over any files in the logs directory that aren't actually logs, we are not promising that this feature is bullet-proof. To be safe, you should make sure that all of the files in the log directory really correspond to logs created by the test harness.

``*KNOWN ISSUE*`` This automated parsing and storage of results into a results database was introduced in Phase 2; we therefore do not yet support this automated parsing for any Phase 1 tests (e.g., Stealth Phase 1). We leave it to future contributors to add this functionality.

[Back to top-level README](../../README.md)
