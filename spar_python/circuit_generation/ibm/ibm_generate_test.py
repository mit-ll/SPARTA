# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 circuit generation test
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  12 Nov 2012   SY             Original Version
# *****************************************************************

# general imports:
import time
import os
import StringIO
import unittest

# SPAR imports:
import spar_python.circuit_generation.ibm.ibm_generate as gen
import spar_python.common.spar_random as sr
import spar_python.common.test_file_handle_object as tfho
import spar_python.report_generation.ta2.ta2_database as t2d
import spar_python.report_generation.ta2.ta2_schema as t2s

class GenerateTest(unittest.TestCase):

    def setUp(self):
        """
        Records the randomness used.
        """
        # record the randomness used in case the test fails:
        self.rand_seed = int(time.time())
        sr.seed(self.rand_seed)
        print("seed for this test: " + str(self.rand_seed))        

    def test_simple_config_file(self):
        """
        tests that the key, input, circuit and test files are roughly as
        expected in a simple case.
        """
        # create the config file:
        test_name = "unit_test_test_1"
        K = "'key'"
        L =  10
        D = 3.0
        W = 5
        num_circuits = 1
        num_inputs = 1
        config_file_text = "\n".join(["test_type = RANDOM",
                                      " = ".join(["seed", str(self.rand_seed)]),
                                      " = ".join(["K", str(K)]),
                                      " = ".join(["L", str(L)]),
                                      " = ".join(["D", str(D)]),
                                      " = ".join(["W", str(W)]),
                                      " = ".join(["num_circuits",
                                                  str(num_circuits)]),
                                      " = ".join(["num_inputs",
                                                  str(num_inputs)]),
                                      " = ".join(["generate", "True"])])
        config_file = StringIO.StringIO(config_file_text)
        # create the parser/generator:
        fho = tfho.TestFileHandleObject()
        resultsdb = t2d.Ta2ResultsDB(":memory:")
        data_path = "ibm"
        pag = gen.ParserAndGenerator(test_name, config_file,
                                     results_database=resultsdb,
                                     data_path=data_path,
                                     file_handle_object=fho)
        pag.parse_and_generate()
        # retrieve the test file and check that it is correct:
        test_file = fho.get_file(os.path.join(data_path, "testfile",
                                              test_name + ".ts"))
        test_file_text = test_file.getvalue()
        expected_test_file_text = "\n".join(
            ["KEY",
             os.path.join("ibm", "keyparams", str(1) + ".keyparams"),
             "CIRCUIT",
             os.path.join("ibm", "circuit", str(1) + ".cir"),
             "INPUT",
             os.path.join("ibm", "input", str(1) + ".input"),
             ""])
        self.assertEqual(expected_test_file_text, test_file_text)
        # retrieve the key file and check that it is correct:
        key_file = fho.get_file(os.path.join(data_path, "keyparams",
                                             "1.keyparams"))
        key_file_text = key_file.getvalue()
        expected_key_file_text = ",".join(["=".join(["L", str(L)]),
                                           "=".join(["D", str(D)]),
                                           "=".join(["K", str(K)])])
        self.assertEqual(expected_key_file_text, key_file_text)
        # retrieve the input and check that it is correct:
        input_file = fho.get_file(os.path.join(data_path, "input", "1.input"))
        input_file_text = input_file.getvalue()
        # check that input text begins and ends with a bracket:
        self.assertEqual("[", input_file_text[0])
        self.assertEqual("]", input_file_text[-1])
        input_batches = input_file_text[1:-1].split(",")
        # check that the number of batches is correct:
        self.assertEqual(W, len(input_batches))
        # check that all batch characters are bits:
        for batch in input_batches:
            for bit in batch:
                self.assertTrue((bit == '0') or (bit == '1'))
        # retrieve the circuit and check that it begins with the correct header:
        circuit_file = fho.get_file(os.path.join(data_path, "circuit", "1.cir"))
        circuit_file_text = circuit_file.getvalue()
        circuit_header = circuit_file_text.split("\n")[0]
        (W_string, D_string, L_string) = circuit_header.split(",")
        W_value = int(W_string.split("=")[-1])
        D_value = float(D_string.split("=")[-1])
        L_value = int(L_string.split("=")[-1])
        self.assertEqual(W, W_value)
        self.assertTrue((D <= D_value) and (D + 1.0 > D_value))
        self.assertEqual(L, L_value)
        # check that the database contains the correct stuff:
        def check_values(table, fields_and_values):
            for (field, expected_value) in fields_and_values:
                values = resultsdb.get_values(
                    fields=[(table, field)])[0]
                self.assertEqual(1, len(values))
                value = values[0]
                self.assertEqual(expected_value, value)
        # security parameters:
        param_fields_and_values = [
            (t2s.PARAM_PID, 1),
            (t2s.PARAM_K, K),
            (t2s.PARAM_L, L),
            (t2s.PARAM_D, D)]
        check_values(t2s.PARAM_TABLENAME, param_fields_and_values)
        # circuits:
        circuit_fields_and_values = [
            (t2s.CIRCUIT_CID, 1),
            (t2s.CIRCUIT_PID, 1),
            (t2s.CIRCUIT_W, W),
            (t2s.CIRCUIT_TESTTYPE, "RANDOM")]
        check_values(t2s.CIRCUIT_TABLENAME, circuit_fields_and_values)
        # inputs:
        input_fields_and_values = [
            (t2s.INPUT_IID, 1),
            (t2s.INPUT_CID, 1)]
        check_values(t2s.INPUT_TABLENAME, input_fields_and_values)
