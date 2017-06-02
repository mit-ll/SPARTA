[Back to top-level README](../../README.md)

Circuit Generation User Manual
===============================================================================
This guide will show you several ways to build:
- circuits and inputs for use during testing,
- test script files that the test harness will use to find the circuits and inputs during the test, and
- a SQLite database containing useful metrics about the circuits and inputs (and which will later be populated with test results).

User Manual (the pretty easy way)
===============================================================================
## Generating IBM Circuits
**1)** Run through the [Installation Instructions](../INSTALL.md). If you deviated from any of the default setup, please keep those in mind as you proceed.

**2)** Navigate to `spar_python/circuit_generation/ibm`.

**3)** If desired, make a copy of the `phase2_tests` and `phase2_riskreduction_tests` directories. The following steps will overwrite data generated in these directories.

**4)** Execute one of the following commands: 
```
./generate_all_rr_phase2.sh
```
or
```
./generate_all_phase2.sh
```

This will build IBM circuits and place them inside either the `phase2_tests` or `phase2_riskreduction_tests` directory. Additionally, test script files are generated and can later be fed into the circuit test harness (see [Circuit Test Execution User Manual](CIRCUIT_TEST_EXECUTION)). Finally, a SQLite database is generated and will store the results of future tests (see [TA2 Results Database Documentation](../tools-docs/ta2-results-database.md)).

``*WARNING*`` This can take several minutes and about 200 MB of space.

``*KNOWN ISSUE*`` The `phase1_tests` directory has configuration files to generate other IBM circuits, but this directory is currently not compatible with the circuit generation tools. It is left for future developers to bring this directory up to date.

## Generating Stealth Circuits
``*NOTE*`` These are older tests that are not as well maintained.

**1)** Run through the [Installation Instructions](../INSTALL.md). If you deviated from any of the default setup, please keep those in mind as you proceed.

**2)** Navigate to `spar_python/circuit_generation/stealth`.

**3)** If desired, make a copy of the `phase1_tests` directory. The following steps will overwrite data generated in these directories. Note that this directory may be very large (on the order of 60 GB).

**4)** Execute one of the following commands: 
```
./generate_small_phase1.sh
```
or
```
./generate_all_phase1.sh
```

This will build Stealth circuits and place them inside the `phase1_tests` directory. Additionally, test script files are generated and can later be fed into the circuit test harness (see [Circuit Test Execution User Manual](CIRCUIT_TEST_EXECUTION)).

``*NOTE*`` The `phase1_tests/testfile` directory is *not* auto-populated by `generate_*_phase1.sh` since these tests are no longer maintained. The scripts in `phase1_tests/testfile` were manually created, and are under version control.

``*WARNING*`` This may take on the order of 5.5 hours and will require about 60 GB of space.


User Manual (the hard way)
===============================================================================
If you would like to have full control over the types of circuits generated, follow these steps.

## Generating IBM Circuits

**1)** Move to the directory `spar_python/circuit_generation/ibm`.

**2)** Execute the following:
```
python ibm_generate.py -d <RESULTSDBNAME> -c <CONFIGFILENAME> -p <DATAPATH> -t <TESTNAME>
```

Some notes on the command line parameters:
- `<RESULTSDBNAME>` is the path to the location of the results database (e.g. `./phase2_tests/resultsdb.db`; see [TA2 Results Database Documentation](../tools-docs/ta2-results-database.md) for more information)
- `<CONFIGFILE>` is the path to the location of the configuration file (e.g. `./phase2_tests/test1.config`)
- `<DATAPATH>` is the full path to the location where you want the directories with  the keyparams, circuits, inputs and test scripts to be stored (e.g. `./phase2_tests/`)
- `<TESTNAME>` is the name of the test (e.g. `test1`)

The `<DATAPATH>` directory will then be populated with four directories; `keyparams`, `circuit`, `input` and `testfile`. The `keyparams`, `circuit` and `input` directories will contain numbered key generation parameters, circuits and input files, respectively. The `testfile` directory will contain a test script `TESTNAME.ts`. 

The resulting directory structure will look as follows:
```
DATAPATH/
	circuit/
		1.cir
		2.cir
		3.cir
		...
	input/
		1.input
		2.input
		3.input
		...
	keyparams/
		1.keyparams
		2.keyparams
		3.keyparams
		...
	testfile/
		test1.ts
```

In order to add more test scripts to this directory structure, run the command above again, with a different `<TESTNAME>` and `<CONFIGFILE>`.

The config file should contain text of the following format:
```
seed = 12345
test_type = RANDOM
num_circuits = 2
num_inputs = 5
K = 80
L = 682
D = 24
W = 200
generate = True
L = 1285
D = 60
W = 50
generate = True
```
The above instructs that for each circuit (L = 682, D = 24, W = 200) and (L = 1285, D = 60, W = 50), there will be 2 circuits, each with 5 corresponding inputs, that will be created. The randomness seed 12345 is used. Generation takes place for each circuit for which `generate = True` appears.

The parameters are as follows:
- seed: the randomness seed - can be omitted
- test_type: should be `RANDOM` (meaning gate types are chosen at random) for the large circuit, varying parameter, and additional tests. Should be one of `LADD`, `LADDconst`, `LMUL`, `LMULconst`, `LSELECT` and `LROTATE` for the single gate type test.
- K: the security parameter - should be specified for all tests
- L: the batch size - should be specified for all tests
- D: the depth of the circuit, as defined by IBM - should be specified for the large circuit, varying parameter, and additional tests
- num_levels: the number of levels in the circuit - should be specified instead of D for single gate type test
- W: the number of gates possible at each level - should be specified for all tests
- num_circuits: the number of circuits to create for each parameter setting - should be specified for all tests
- num_inputs: the number of inputs to create for each circuit - should be specified for each parameter setting

## Generating Stealth Circuits
``*WARNING*`` These are older tests that are not as well maintained.

**1)** Change your current directory to `spar_python/circuit_generation/stealth`.

**2)** Execute the following:
```
python stealth_generate.py <TEST_NAME>
```

`<TEST_NAME>` can be any directory that contains an appropriately made `config.txt` file (see below).

A corresponding directory will be populated with test circuits, inputs, security parameters, and outputs, based on the `config.txt` file. 

`config.txt` should contain text of the following format:
```
seed = 12345
fam = 2
test_type = AND
K = 80
W = 20
G = 200
fg = .5
X = 300
fx = .5
num_circuits = 2
num_inputs = 5
generate = True
```

The above instructs that 2 circuits consisting entirely of "and" gates should be created with the parameters fam = 2, W = 20, G = 20, fg = .5, X = 300, and fx = .5, and that 5 inputs should be generated for each such circuit. The randomness seed 12345 is used.

The parameters are as follows:
- seed: the randomness seed - can be omitted
- fam: the circuit family - should be specified for all tests
- test_type: should be `RANDOM` (meaning gate types are chosen at random) for the large circuit and varying parameter tests; should be one of `AND`, `OR`, and `XOR` for the single gate type test
- K: the security parameter - should be specified for all tests
- W: the number of input wires - should be specified for all tests
- G: the number of intermediate gates - should be specified for the large circuit and varying parameter tests
- fg: the intermediate fanning fraction - should be specified for the large and varying parameter tests
- X: the number of xor gates - should be specified for the large circuit and varying parameter tests
- fx: the xor fanning fraction - should be specified for the large and varying parameter tests
- D: the circuit depth - should be specified for the single gate type tests
- num_circuits: the number of circuits to create for each parameter setting - should be specified for all tests
- num_inputs: the number of inputs to create for each circuit - should be specified for each parameter setting

In order to modify the sets of circuits created for each test, modify the `config.txt` files in the directories corresponding to the tests before running `stealth_generate.py`.

[Back to top-level README](../../README.md)
