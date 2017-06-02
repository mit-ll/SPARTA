# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 circuit generation test
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  02 Jan 2013   SY             Original Version
# *****************************************************************

import time
import os
import StringIO
import spar_python.circuit_generation.stealth.stealth_generate as gen
import unittest
import spar_python.common.spar_random as sr
import spar_python.common.test_file_handle_object as tfho

class GenerateTest(unittest.TestCase):

    def setUp(self):
        """
        Records the randomness used.
        """
        # record the randomness used in case the test fails:
        rand_seed = int(time.time())
        sr.seed(rand_seed)
        print("seed for this test: " + str(rand_seed))        

    def test_simple_config_file(self):
        """
        tests that the key, input, circuit and test files are roughly as
        expected in a simple case.
        """
        # create the config file:
        test_name = "unit_test_test_1"
        K = "'key'"
        fam = 3
        W = 5
        D = 8
        num_circuits = 1
        num_inputs = 1
        config_file_text = "\n".join(["test_type = RANDOM",
                                      " = ".join(["K", str(K)]),
                                      " = ".join(["fam", str(fam)]),
                                      " = ".join(["W", str(W)]),
                                      " = ".join(["D", str(D)]),
                                      " = ".join(["num_circuits",
                                                  str(num_circuits)]),
                                      " = ".join(["num_inputs",
                                                  str(num_inputs)]),
                                      " = ".join(["generate", "True"])])
        config_file = StringIO.StringIO(config_file_text)
        # create the parser/generator:
        fho = tfho.TestFileHandleObject()
        pag = gen.ParserAndGenerator(test_name, config_file, fho)
        pag.parse_and_generate()
        # retrieve the test file and check that it is correct:
        test_file = fho.get_file(os.path.join(test_name, "test.txt"))
        test_file_text = test_file.getvalue()
        expected_test_file_text = "\n".join(
            ["KEY",
             os.path.join("stealth", test_name, "key", str(1)),
             "CIRCUIT",
             os.path.join("stealth", test_name, "circuit", str(1)),
             "INPUT",
             os.path.join("stealth", test_name, "input", str(1)),
             ""])
        self.assertEqual(expected_test_file_text, test_file_text)
        # retrieve the key file and check that it is correct:
        key_file = fho.get_file(os.path.join(test_name, "key", "1"))
        key_file_text = key_file.getvalue()
        self.assertEqual(K, key_file_text)
        # retrieve the input and check that it is correct:
        input_file = fho.get_file(os.path.join(test_name, "input", "1"))
        input_file_text = input_file.getvalue()
        # check that input text begins and ends with a bracket:
        self.assertEqual("[", input_file_text[0])
        self.assertEqual("]", input_file_text[-1])
        # check that all bits are 0 or 1:
        for bit in input_file_text[1:-1]:
            self.assertTrue((bit == '0') or (bit == '1'))
        # retrieve the circuit and check that it begins with the correct header:
        circuit_file = fho.get_file(os.path.join(test_name, "circuit", "1"))
        circuit_file_text = circuit_file.getvalue()
        circuit_header = circuit_file_text.split("\n")[0]
        (W_string, D_string, fam_string) = circuit_header.split(",")
        W_value = int(W_string.split("=")[-1])
        D_value = float(D_string.split("=")[-1])
        fam_value = int(fam_string.split("=")[-1])
        self.assertEqual(W, W_value)
        self.assertEqual(D, D_value)
        self.assertEqual(fam, fam_value)
 
