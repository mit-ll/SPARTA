[Back to top-level README](../../README.md)

TA2 (Circuit Testing) Results Database
===============================================================================

We store the test results in a sqlite3 database. Sqlite3 is a light-weight database that can be relocated with a simple move or copy/paste operation. We interface with the results database through the Ta2ResultsDB class in `spar_python/report_generation/ta2/ta2_database.py`, which has a few handy methods.

The results database has 6 tables, which are described below.

## `key_parameters`

Each entry in this table describes a set security parameters.
- testname (string) : the name of the test
- param_id (int) : a unique id associated with this set of security parameters
- k (int) : the security parameter
- d (int) : the depth of the circuit, as defined by IBM
- l (int) : the number of bits packed into a single ciphertext

## `circuits`

Each entry in this table describes a single circuit.
- test name (string) : the name of the test
- cid (int) : a unique id associated with this circuit
- w (int) : the number of input wires of the circuit
- param_id (int) : the id of the security parameters with which this circuit is associated
- num_adds (int) : the number of addition gates in this circuit
- num_add_consts (int) : the number of add constant gates in this circuit
- num_muls (int) : the number of multiplication gates in this circuit
- num_mul_consts (int) : the number of multiply by constant gates in this circuit
- num_rotates (int) : the number of rotate gates in this circuit
- num_selects (int) : the number of select gates in this circuit
- num_levels (int) : the number of levels in this circuit
- num_gates (int) : the total number of gates in this circuit
- output_gate_type (string) : the type of the circuit output gate
- atomic_row_id (int) : the query id of the atomic query in question

## `inputs`

Each entry in this table describes a single input to a given circuit.
- testname (string) : the name of the test
- input_id (int) : a unique id associated with this input
- circuit_id (int) : the id of the circuit with which this input is associated
- num_zeros (int) : the number of zeros in this input
- num_ones (int) : the number of ones in this input
- correct_output (string) : the correct output of the given circuit on this input

## `performer_keygen`

Each entry in this table describes a single key generation by either the performer or the baseline.
- performer_name (string) : the name of the performer (or baseline)
- testname (string) : the name of the test
- timestamp (string) : the time at which the key generation command was sent
- param_id (int) : the id of the security parameters associated with this command
- latency (real) : the time it took to execute this command
- transmit_latency (real) : the time it took to transmit the command
- keysize (real) : the size of the resulting key
- status (string) : any error messages go here. If it is empty, that means that the command succeeded.
- recovery (int) : field that facilitates recovery

## `performer_circuit_ingestion`

Each entry in this table describes a single circuit ingestion by either the performer or the baseline.
- performer_name (string) : the name of the performer (or baseline)
- testname (string) : the name of the test
- timestamp (string) : the time at which the circuit ingestion command was sent
- circuit_id (int) : the id of the circuit associated with this command
- latency (real) : the time it took to execute this command
- transmit_latency (real) : the time it took to transmit the command
- status (string) : any error messages go here. If it is empty, that means that the command succeeded.
- recovery (int) : field that facilitates recovery

## `performer_evaluation`

Each entry in this table describes a single circuit evaluation by either the performer or the baseline.
- performer_name (string) : the name of the performer (or baseline)
- testname (string) : the name of the test
- timestamp (string) : the time at which the circuit evaluation command was sent
- input_id (int) : the id of the input associated with this command
- input_transmit_latency (real) : the time it took to transmit the input to the circuit evaluator
- output_transmit_latency (real) : the time it took to transmit the output from the circuit evaluator
- encryption_latency (real) : the time it took to encrypt the input
- evaluation_latency (real) : the time it took to perform the evaluation
- decryption_latency (real) : the time it took to decrypt the output
- output (string) : the output of the evaluation
- encrypted_output_size (real) : the size of the encrypted output
- encrypted_input_size (real) : the size of the encrypted input
- correctness (boolean) : an indicator of whether or not the evaluation was correct
- status (string) : any error messages go here. If it is empty, that means that the command succeeded.
- recovery (int) : field that facilitates recovery

[Back to top-level README](../../README.md)
