# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 XOR gate class test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
#  08 Nov 2012   SY             Incorporated Oliver's feedback
# *****************************************************************
 # general imports:
import unittest
import time

# SPAR imports:
import spar_python.circuit_generation.stealth.stealth_wire as sw
import spar_python.circuit_generation.stealth.stealth_gate_xor as sgx
import spar_python.common.spar_random as sr

class TestXorGate(unittest.TestCase):

    def setUp(self):
        """
        Records the randomness used.
        """
        # record the randomness used in case the test fails:
        rand_seed = int(time.time())
        sr.seed(rand_seed)
        print("seed for this test: " + str(rand_seed))

    def test_get_full_display_string(self):
        """
        Tests that the method get_full_display_string returns the correct
        string.
        """
        #Initialize the input wires:
        wire1 = sw.StealthInputWire("wire1", True)
        wire2 = sw.StealthInputWire("wire2", False)
        #Initialize the gate:
        unnegated_gate = sgx.StealthXorGate("unnegated_gate",
                                            [wire1, wire2],
                                            [False, False])

        somenegated_gate = sgx.StealthXorGate("somenegated_gate",
                                              [wire1, wire2],
                                              [True, False])
        
        negated_gate = sgx.StealthXorGate("negated_gate",
                                          [wire1, wire2],
                                          [True, True])

        self.assertEquals(unnegated_gate.get_full_display_string(),
                          "unnegated_gate:XOR(wire1,wire2)")

        self.assertEquals(somenegated_gate.get_full_display_string(),
                          "somenegated_gate:XOR(N(wire1),wire2)")

        self.assertEquals(negated_gate.get_full_display_string(),
                          "negated_gate:XOR(N(wire1),N(wire2))")


    def test_xor_without_negations(self):
        """
        Tests that xor gates return the expected values on a few inputs and
        with no negations.
        """
        # xor_inp_outp_map maps the values of inputs of a xor gate to the
        # expected output:
        xor_inp_outp_map = {(True, True): False,
                            (True, False): True,
                            (False, True): True,
                            (False, False): False,
                            (True, True, True): True,
                            (True, True, False): False,
                            (True, False, True): False,
                            (True, False, False): True,
                            (False, True, True): False,
                            (False, True, False): True,
                            (False, False, True): True,
                            (False, False, False): False}
        # check that each output is as expected:
        for inp_value_list in xor_inp_outp_map.keys():
            inp_wire_list = [sw.StealthInputWire("wire", inp_value)
                             for inp_value in inp_value_list]
            gate = sgx.StealthXorGate("xor_gate",
                                      inp_wire_list,
                                      [False for val in inp_value_list])
            self.assertEqual(gate.evaluate(), xor_inp_outp_map[inp_value_list])

    def test_xor_with_negations(self):
        """
        Tests that XOR gates return the expected values on a two inputs with
        each possible negation configuration.
        """
        # xor_inp_outp_map maps tuples of the form (inputs, negations)
        # to the expected output:
        xor_inp_outp_map = {((True, True), (True, True)): False,
                            ((True, True), (True, False)): True,
                            ((True, True), (False, True)): True,
                            ((True, True), (False, False)): False,
                            ((True, False), (True, True)): True,
                            ((True, False), (True, False)): False,
                            ((True, False), (False, True)): False,
                            ((True, False), (False, False)): True,
                            ((False, True), (True, True)): True,
                            ((False, True), (True, False)): False,
                            ((False, True), (False, True)): False,
                            ((False, True), (False, False)): True,
                            ((False, False), (True, True)): False,
                            ((False, False), (True, False)): True,
                            ((False, False), (False, True)): True,
                            ((False, False), (False, False)): False}

        # check that each output is as expected:
        for key in xor_inp_outp_map.keys():
            (inp_value_list, negation_list) = key
            inp_wire_list = [sw.StealthInputWire("wire", inp_value)
                             for inp_value in inp_value_list]
            gate = sgx.StealthXorGate("xor_gate",
                                      inp_wire_list,
                                      negation_list)
            self.assertEqual(gate.evaluate(),xor_inp_outp_map[key])
    
    def test_xor_comment_example(self):
        """
        Test to see whether the 'simple use' example in the comment for the
        StealthXorGate class returns the expected value.
        """
        # initialize the objects used as inputs in the example provided in the
        # code comments.
        wire1 = sw.StealthInputWire("wire1", True)
        wire2 = sw.StealthInputWire("wire2", False)
        # Instantiate our XOR gate as follows:
        this_gate = sgx.StealthXorGate("this_gate",
                                       [wire1, wire2],
                                       [False, False])
        # Our XOR gate can be prompted to return its value as follows:
        val = this_gate.evaluate()
        # val will be equal to True.
        self.assertEqual(val, True)

    def test_balancing_simple(self):
        """
        Test to determine that balancing forces the desired output. Only tests
        one simple case, where we take the desired output to be the negation
        of the output of the comment example.
        """
        # initialize the objects used as inputs in the example provided in the
        # code comments.
        wire1 = sw.StealthInputWire("wire1", True)
        wire2 = sw.StealthInputWire("wire2", False)
        # Instantiate our XOR gate as follows:
        this_gate = sgx.StealthXorGate("this_gate",
                                       [wire1, wire2],
                                       [False, False])

        val = this_gate.evaluate()
        this_gate.balance(not val)
        self.assertEqual(this_gate.evaluate(), not val)

    def test_balancing_randomized(self):
        """
        Test to determine that balancing forces the desired output. Tests
        many randomized cases.
        """
        num_tests = 100
        min_num_inputs = 2
        max_num_inputs = 20
        for test_num in xrange(num_tests):
            num_inputs = sr.randint(min_num_inputs, max_num_inputs)
            inputs = [sw.StealthInputWire("wire", bool(sr.randbit()))
                      for input_num in xrange(num_inputs)]
            negations = [bool(sr.randbit())
                         for input_num in xrange(num_inputs)]
            gate = sgx.StealthXorGate("xor_gate", inputs, negations)
            desired_output = bool(sr.randbit())
            gate.balance(desired_output)
            self.assertEqual(gate.evaluate(), desired_output)
 
