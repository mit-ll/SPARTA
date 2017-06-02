# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        The Stealth circuit generation main method
#                      generation 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 May 2012   SY             Original Version
# *****************************************************************

from optparse import OptionParser
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import spar_python.circuit_generation.stealth.stealth_generation_functions as sgf
import spar_python.common.file_handle_object as fho
import spar_python.common.spar_random as sr

class ParserAndGenerator(object):
    """
    This class parses the config file living in the directory test_name,
    and generates corresponding circuits.
    config.txt should contain text of the following format:
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
    this means that 2 circuits consisting entirely of and gates should  be
    created with the parameters fam = 2, W = 20, G = 20, fg = .5, X = 300, and
    fx = .5, and that 5 inputs should be generated for each such circuit.
    The randomness seed 12345 is used for generation.
    all the possible parameters (seed, fam, test_type, K, W, G, fg, X, fx, D,
    num_circuits, and num_inputs) can be reset multiple times throughout the
    config.txt file.
    Note that the seed parameter may be omitted.
    For the large and varying parameters tests, test_type should be RANDOM.
    fam, K, W, G, fg, X, fx, num_circuits and num_inputs should be specified.
    For the single gate type test, test_type should change throughout the test;
    it should take on the values AND, OR, and XOR. fam should be set to 3,
    and K, W, D, num_circuits and num_inputs should be specified.
    Each time generate = True occurs, generation will occur with the current
    values. Generation stores numbered circuits in the 'circuit' directory in
    the 'test_name' folder, numbered inputs in the 'input' directory, and
    numbered security parameters in the 'key' directory.
    It also generates a 'test.txt' file which lists the paths to the keys,
    circuits and inputs in the order in which they are used.
    """
    def __init__(self, test_name, config_file,
                 file_handle_object=None):
        """
        Initializes the class with a config_file, a test_name and a
        file_handle_object.
        Test_name should correspond to a directory with the name 'test_name'.
        """
        self.__config_file_lines = config_file.read().split("\n")
        self.__test_name = test_name
        self.__fho = file_handle_object
        if not self.__fho:
            self.__fho = fho.FileHandleObject()
        # initialize the key, circuit, input and output directory names:
        self.__key_dir_name = os.path.join(self.__test_name, "key")
        self.__circuit_dir_name = os.path.join(self.__test_name, "circuit")
        self.__input_dir_name = os.path.join(self.__test_name, "input")
        self.__output_dir_name = os.path.join(self.__test_name, "output")
        # make the key, circuit, input and output folders:
        self.__fho.create_dir(self.__key_dir_name)
        self.__fho.create_dir(self.__circuit_dir_name)
        self.__fho.create_dir(self.__input_dir_name)
        self.__fho.create_dir(self.__output_dir_name)
        # initialize the key, circuit and input counters to 0:
        self.__unique_key_num = 0
        self.__unique_circuit_num = 0
        self.__unique_input_num = 0
        # create the map which maps line to line handler:
        self.__line_to_handler = {"fam": self.__handle_fam,
                                  "test_type": self.__handle_test_type,
                                  "K": self.__handle_k,
                                  "W": self.__handle_w,
                                  "G": self.__handle_g,
                                  "fg": self.__handle_fg,
                                  "X": self.__handle_x,
                                  "fx": self.__handle_fx,
                                  "D": self.__handle_d,
                                  "num_circuits": self.__handle_num_circuits,
                                  "num_inputs": self.__handle_num_inputs,
                                  "generate": self.__handle_generate,
                                  "seed": self.__handle_seed}

    def __handle_seed(self, randseed):
        """Handles a new randomness seed appropriately."""
        sr.seed(int(randseed))

    def __handle_fam(self, fam):
        """Handles a new fam appropriately."""
        self.__fam = int(fam)

    def __handle_test_type(self, test_type):
        """Handles a new test type appropriately."""
        self.__test_type = sgf.TEST_TYPES.value_to_number[test_type]
        
    def __handle_w(self, W):
        """Handles a new number of input wires appropriately."""
        self.__W = int(W)

    def __handle_g(self, G):
        """Handles a new number of intermediate gates appropriately."""
        self.__G = int(G)

    def __handle_fg(self, fg):
        """Handles a new intermediate fanin appropriately."""
        self.__fg = float(fg)

    def __handle_x(self, X):
        """Handles a new number of xor gates appropriately."""
        self.__X = int(X)

    def __handle_fx(self, fx):
        """Handles a new xor fanin appropriately."""
        self.__fx = float(fx)

    def __handle_d(self, D):
        """Handles a new depth appropriately."""
        self.__D = int(D)

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

    def __handle_k(self, K):
        """Handles a new security parameter appropriately."""
        self.__K = K
        self.__unique_key_num += 1
        # write the security parameter to a key file:
        sec_param_file_name = os.path.join(self.__key_dir_name,
                                           str(self.__unique_key_num))
        sec_param_file = self.__fho.get_file_object(sec_param_file_name, 'w')
        sec_param_file.write(str(self.__K))
        self.__fho.close_file_object(sec_param_file)
        # write the key location to the test file:
        self.__test_file.write("".join(["KEY\n",
                                        os.path.join("stealth",
                                                     sec_param_file_name),
                                        "\n"]))
    
    def __make_circuits(self):
        """Generates circuits with the current parameters"""
        for circuit_num in xrange(self.__num_circuits):
            self.__unique_circuit_num += 1
            self.__unique_input_num +=1 
            circuit_file_name = os.path.join(self.__circuit_dir_name,
                                             str(self.__unique_circuit_num))
            circuit_file = self.__fho.get_file_object(circuit_file_name, 'w')
            input_file_name = os.path.join(self.__input_dir_name,
                                           str(self.__unique_input_num))
            input_file = self.__fho.get_file_object(input_file_name, 'w')
            output_file_name = os.path.join(self.__output_dir_name,
                                            str(self.__unique_input_num))
            output_file = self.__fho.get_file_object(output_file_name, 'w')
            type_to_generator = sgf.FAM_TO_TYPE_TO_GENERATOR[self.__fam]
            generator = type_to_generator[self.__test_type]
            if self.__fam == 3:
                generator(self.__W, self.__D, circuit_file,
                          input_file, output_file).generate()
            elif self.__fam == 1:
                generator(self.__W, self.__G, self.__fg, circuit_file,
                          input_file, output_file).generate()
            elif self.__fam == 2:
                generator(self.__W, self.__G, self.__fg,
                          circuit_file, input_file, output_file,
                          self.__X, self.__fx).generate()
            self.__fho.close_file_object(circuit_file)
            self.__fho.close_file_object(input_file)
            self.__fho.close_file_object(output_file)
            # write the circuit location to the test file:
            self.__test_file.write("".join(["CIRCUIT\n",
                                            os.path.join("stealth",
                                                         circuit_file_name),
                                            "\n"]))
            # write the input location to the test file:
            self.__test_file.write("".join(["INPUT\n",
                                            os.path.join("stealth",
                                                         input_file_name),
                                            "\n"]))
            # for each circuit, make self.__num_inputs inputs:
            for input_num in xrange(1, self.__num_inputs):
                self.__unique_input_num += 1
                # generate a random input:
                inp = sgf.make_random_input(self.__W)
                # write the input to an input file:
                input_file_name = os.path.join(self.__input_dir_name,
                                                str(self.__unique_input_num))
                input_file = self.__fho.get_file_object(input_file_name, 'w')
                input_file.write(str(inp))
                self.__fho.close_file_object(input_file)
                # write the input location to the test file:
                self.__test_file.write("".join(["INPUT\n",
                                                os.path.join("stealth",
                                                             input_file_name),
                                                "\n"]))

    def parse_and_generate(self):
        """Does the actual parsing and generation."""
        # open the test file:
        test_file_name = os.path.join(self.__test_name, "test.txt")
        self.__test_file = self.__fho.get_file_object(test_file_name, 'w')
        # parse all the lines, writing the corresponding stuff to the test file
        # and to key, circuit and input files:
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
    # Arguments are interpreted as test names.
    (options, args) = parser.parse_args()
    for arg in args:
        config_file_name = os.path.join(arg, 'config.txt')
        config_file = open(config_file_name, 'r')
        ParserAndGenerator(arg, config_file).parse_and_generate()
        config_file.close()
