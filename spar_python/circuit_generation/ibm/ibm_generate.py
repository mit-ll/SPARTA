# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        The IBM circuit generation main method 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 May 2012   SY             Original Version
# *****************************************************************

# general imports:
from optparse import OptionParser
import csv
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '../../..')
sys.path.append(base_dir)

# SPAR imports:
import spar_python.circuit_generation.ibm.ibm_generation_functions as igf
import spar_python.common.file_handle_object as fho
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.ta2.ta2_database as t2d
import spar_python.common.spar_random as sr

RESULTSDB_FIELDS_TO_GATE_TYPES = {
    t2s.CIRCUIT_NUMADDS: igf.GATE_TYPES.to_string(igf.GATE_TYPES.LADD),
    t2s.CIRCUIT_NUMADDCONSTS: igf.GATE_TYPES.to_string(igf.GATE_TYPES.LADDconst),
    t2s.CIRCUIT_NUMMULS: igf.GATE_TYPES.to_string(igf.GATE_TYPES.LMUL),
    t2s.CIRCUIT_NUMMULCONSTS: igf.GATE_TYPES.to_string(igf.GATE_TYPES.LMULconst),
    t2s.CIRCUIT_NUMSELECTS: igf.GATE_TYPES.to_string(igf.GATE_TYPES.LSELECT),
    t2s.CIRCUIT_NUMROTATES: igf.GATE_TYPES.to_string(igf.GATE_TYPES.LROTATE)}

PERFORMERNAME = "ibm"

class ParserAndGenerator(object):
    """
    This class parses the config file living in the directory test_name,
    and generates corresponding circuits.
    A config.txt should contain text of the following format:
    seed = 12345
    K = 80
    L = 100
    D = 10
    W = 200
    num_circuits = 2
    num_inputs = 5
    generate = True
    this means that 2 circuits should  be created with the parameters L = 100,
    D = 10 and W = 200, and that 5 inputs should be generated for each such
    circuit.
    The randomness seed 12345 is used for generation.
    all the possible parameters (seed, test_type, K, L, D, num_levels, W,
    num_circuits, and num_inputs) can be reset multiple times throughout the
    config.txt file.
    Note that the seed parameter may be omitted.
    For the large and varying parameters tests, test_type should be 'random' and
    K, L, D, W, num_circuits and num_inputs should be specified.
    For the single gate type test, test_type should change throughout the test;
    it should take on the values 'add', 'addconst', 'mul', 'mulconst', 'select',
    and 'rotate'. K, L, num_levels, W, num_circuits and num_inputs should be
    specified.
    Each time generate = True occurs, generation will occur with the current
    values. Generation stores numbered circuits in the 'circuit' directory in
    the 'test_name' folder, numbered inputs in the 'input' directory, and
    numbered security parameters in the 'params' directory.
    It also generates a 'test.txt' file which lists the paths to the params,
    circuits and inputs in the order in which they are used.
    """
    def __init__(self, test_name, config_file,
                 results_database, data_path=PERFORMERNAME,
                 file_handle_object=None):
        """
        Initializes the class with a test_name, a config file, a results
        database, and a file_handle_object.
        Test_name should correspond to a directory with the name 'test_name'.
        """
        self.__resultsdb = results_database
        self.__config_file_lines = config_file.read().split("\n")
        self.__test_name = test_name
        self.__fho = file_handle_object
        if not self.__fho:
            self.__fho = fho.FileHandleObject()
        # initialize the testname, params, circuit and input directory names:
        self.__data_path = data_path
        self.__testfile_dir_name = os.path.join(self.__data_path, "testfile")
        self.__params_dir_name = os.path.join(self.__data_path, "keyparams")
        self.__circuit_dir_name = os.path.join(self.__data_path, "circuit")
        self.__input_dir_name = os.path.join(self.__data_path, "input")
        self.__log_dir_name = os.path.join(self.__data_path, "logs")
        # make the testname, params, circuit and input folders:
        self.__fho.create_dir(self.__testfile_dir_name)
        self.__fho.create_dir(self.__params_dir_name)
        self.__fho.create_dir(self.__circuit_dir_name)
        self.__fho.create_dir(self.__input_dir_name)
        self.__fho.create_dir(self.__log_dir_name)
        # create the map which maps line to line handler:
        self.__line_to_handler = {"test_type": self.__handle_test_type,
                                  "K": self.__handle_k,
                                  "L": self.__handle_l,
                                  "D": self.__handle_d,
                                  "W": self.__handle_w,
                                  "num_levels": self.__handle_num_levels,
                                  "num_circuits": self.__handle_num_circuits,
                                  "num_inputs": self.__handle_num_inputs,
                                  "generate": self.__handle_generate,
                                  "seed": self.__handle_seed}
        # stores the latest param recorded, in order to detect changes:
        self.__latest_params = None
        # set all of the parameters to None:
        self.__seed = None
        self.__K = None
        self.__L = None
        self.__D = None
        self.__W = None
        self.__num_levels = None
        self.__num_circuits = None
        self.__num_inputs = None
        self.__sec_param_id = None
        self.__circuit_id = None
        self.__input_id = None
        self.__test_type = None

    def __handle_seed(self, randseed):
        """Handles a new randomness seed appropriately."""
        sr.seed(int(randseed))

    def __handle_test_type(self, test_type):
        """Handles a new test type appropriately."""
        self.__test_type = igf.TEST_TYPES.value_to_number[test_type]
        
    def __handle_k(self, K):
        """Handles a new security parameter appropriately."""
        self.__K = K
        
    def __handle_l(self, L):
        """Handles a new batch size appropriately."""
        self.__L = int(L)

    def __handle_d(self, D):
        """Handles a new depth appropriately."""
        self.__D = float(D)

    def __handle_w(self, W):
        """Handles a new width appropriately."""
        self.__W = int(W)

    def __handle_num_levels(self, num_levels):
        """Handles a new num_levels appropriately."""
        self.__num_levels = int(num_levels)

    def __handle_num_circuits(self, num_circuits):
        """Handles a new number of circuits appropriately."""
        self.__num_circuits = int(num_circuits)

    def __handle_num_inputs(self, num_inputs):
        """Handles a new number of inputs appropriately."""
        self.__num_inputs = int(num_inputs)

    def __handle_generate(self, generate):
        """Handles a 'generate = True' command"""
        if eval(generate):
            self.__make_circuits()

    def __handle_new_params(self):
        """Writes the new params (consisting of K, L, D (or num_levels))."""
        if self.__test_type == igf.TEST_TYPES.RANDOM:
            sec_param_text = ",".join(["L" + "=" + str(self.__L),
                                       "D" + "=" + str(self.__D),
                                       "K" + "=" + str(self.__K)])
        else:
            sec_param_text = ",".join(["L" + "=" + str(self.__L),
                                       "D" + "=" +
                                       str(self.__num_levels),
                                       "K" + "=" + str(self.__K)])
        # Only update the params if there have been changes to it:
        if sec_param_text != self.__latest_params:
            self.__latest_params = sec_param_text
            # find the security parameter id:
            self.__sec_param_id = self.__resultsdb.get_next_params_id()
            # write the security parameter to the results database:
            self.__resultsdb.add_row(
                t2s.PARAM_TABLENAME,
                {t2s.PARAM_PID: self.__sec_param_id,
                 t2s.PARAM_TESTNAME: self.__test_name,
                 t2s.PARAM_K: self.__K,
                 t2s.PARAM_D: self.__D,
                 t2s.PARAM_L: self.__L})
            # write the security parameter to a params file:
            sec_param_file_name = os.path.join(self.__params_dir_name,
                                               str(self.__sec_param_id)
                                               + ".keyparams")
            sec_param_file = self.__fho.get_file_object(sec_param_file_name,
                                                        'w')
            sec_param_file.write(sec_param_text)
            self.__fho.close_file_object(sec_param_file)
            # write the params location to the test file:
            self.__test_file.write(
                "".join(["KEY\n",
                         self.__get_testfile_path(sec_param_file_name), "\n"]))

    def __get_testfile_path(self, path):
        """Takes in a path, and returns the same path relative to the
        appropriate directory for the test file."""
        path = os.path.relpath(
            path, os.path.join(self.__data_path, os.pardir))
        return path       

    def __make_circuits(self):
        """Generates circuits with the current parameters"""
        # update the params if needed:
        self.__handle_new_params()
        # make self.__num_circuits circuits:
        for circuit_num in xrange(self.__num_circuits):
            # generate a random circuit:
            if self.__test_type == igf.TEST_TYPES.RANDOM:
                gen = igf.TEST_TYPE_TO_GENERATOR_BY_DEPTH[igf.TEST_TYPES.RANDOM]
                circ = gen(self.__L, self.__D, self.__W)
            else:
                gen = igf.TEST_TYPE_TO_GENERATOR_BY_LEVEL[self.__test_type]
                circ = gen(self.__L, self.__num_levels, self.__W)
            self.__write_circuit(circ)
            # for each circuit, make self.__num_inputs inputs:
            for input_num in xrange(self.__num_inputs):
                # generate a random input:
                inp = igf.make_random_input(self.__L, self.__W)
                self.__write_input(inp)

    def __write_circuit(self, circ):
        """Handles writing a circuit, both to the circuit file and to the test
        file."""
        # find the circuit id:
        self.__circuit_id = self.__resultsdb.get_next_circuit_id()
        # write the circuit to the results database:
        row = {t2s.CIRCUIT_TESTNAME: self.__test_name,
               t2s.CIRCUIT_CID: self.__circuit_id,
               t2s.CIRCUIT_PID: self.__sec_param_id,
               t2s.CIRCUIT_W: self.__W,
               t2s.CIRCUIT_NUMLEVELS: circ.get_num_levels(),
               t2s.CIRCUIT_OUTPUTGATETYPE: circ.get_output_gate_func(),
               t2s.CIRCUIT_TESTTYPE:
               igf.TEST_TYPES.number_to_value[self.__test_type]}
        num_gates = 0
        for database_field in RESULTSDB_FIELDS_TO_GATE_TYPES.keys():
            num_gates_this_type = circ.get_num_gates(
                gate_func_name=RESULTSDB_FIELDS_TO_GATE_TYPES[database_field])
            row[database_field] = num_gates_this_type
            num_gates += num_gates_this_type
        row[t2s.CIRCUIT_NUMGATES] = num_gates
        self.__resultsdb.add_row(t2s.CIRCUIT_TABLENAME, row)
        # write the circuit to the circuit file:
        circuit_file_name = os.path.join(self.__circuit_dir_name,
                                         str(self.__circuit_id) + ".cir")
        circuit_file = self.__fho.get_file_object(circuit_file_name, 'w')
        circuit_file.write(circ.display())
        self.__fho.close_file_object(circuit_file)
        # write the circuit location to the test file:
        self.__test_file.write(
            "".join(["CIRCUIT\n",
                     self.__get_testfile_path(circuit_file_name), "\n"]))

    def __write_input(self, inp):
        """Handles writing an input, both to the input file and to the test
        file."""
        # find the input id:
        self.__input_id = self.__resultsdb.get_next_input_id()
        # write the input to the results database:
        row = {t2s.INPUT_TESTNAME: self.__test_name,
               t2s.INPUT_IID: self.__input_id,
               t2s.INPUT_CID: self.__circuit_id,
               t2s.INPUT_NUMZEROS: inp.get_num_zeros(),
               t2s.INPUT_NUMONES: inp.get_num_ones()}
        self.__resultsdb.add_row(t2s.INPUT_TABLENAME, row)
         # write the input to an input file:
        input_file_name = os.path.join(self.__input_dir_name,
                                       str(self.__input_id) + ".input")
        input_file = self.__fho.get_file_object(input_file_name, 'w')
        input_file.write(str(inp))
        self.__fho.close_file_object(input_file)
        # write the input location to the test file:
        self.__test_file.write(
            "".join(["INPUT\n",
                     self.__get_testfile_path(input_file_name), "\n"]))

    def parse_and_generate(self):
        """Does the actual parsing and generation."""
        # open the test file:
        test_file_name = os.path.join(self.__testfile_dir_name,
                                      self.__test_name + ".ts")
        self.__test_file = self.__fho.get_file_object(test_file_name, 'w')
        # parse all the lines, writing the corresponding stuff to the test file
        # and to params, circuit and input files:
        for line in self.__config_file_lines:
            parts = line.split(' ')
            assert(len(parts) == 3)
            assert(parts[1] == '=')
            self.__line_to_handler[parts[0]](parts[2])
        # close the test file:
        self.__fho.close_file_object(self.__test_file)

if __name__ == '__main__':
    parser = OptionParser(usage = ('This generates test files,'
                                   'one per argument passed to this script.'))
    parser.add_option(
        "-d", "--results-database-name",
        help="the path to the results database")
    parser.add_option(
        "-c", "--config-file-name",
        help="the path to the config file")
    parser.add_option(
        "-p", "--data-path",
        help="the path to where the produced data is stored")
    parser.add_option(
        "-t", "--test-name",
        help="the name to be assigned to the test script")
    # Arguments are interpreted as test names.
    (options, args) = parser.parse_args()
    config_file_name = options.config_file_name
    config_file = open(config_file_name, 'r')
    results_database_name = options.results_database_name
    results_database = t2d.Ta2ResultsDB(results_database_name)
    data_path = options.data_path
    if not data_path:
        data_path = PERFORMERNAME
    test_name = options.test_name
    if not test_name:
        # strip the slash from the right side of the config file name:
        tempval = config_file_name.rstrip(os.sep)
        test_name = os.path.basename(tempval)
    ParserAndGenerator(test_name=test_name,
                       config_file=config_file,
                       results_database=results_database,
                       data_path=data_path).parse_and_generate()
    config_file.close()
