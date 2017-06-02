# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 circuit generation function test class
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  12 Nov 2012   SY             Original Version
# *****************************************************************

import math
import time
import spar_python.circuit_generation.stealth.stealth_generation_functions as g
import spar_python.common.spar_random as sr
import unittest
import spar_python.common.test_file_handle_object as tfho

class generation_functions_test(unittest.TestCase):

    def setUp(self):
        """
        Records the randomness used.
        """
        # record the randomness used in case the test fails:
        self.rand_seed = int(time.time())
        sr.seed(self.rand_seed)
        print("seed for this test: " + str(self.rand_seed))        

    def test_make_uniform_random_f1f2_gate(self):
        """
        tests that the distribution of gate types is uniform in the uniform f1f2
        gate maker.
        """
        num_trials = 100
        fanin_frac = .5
        # test fam1 and fam2 gates:
        generate = g.TYPE_TO_GATE_GEN[g.TEST_TYPES.RANDOM]
        W = 10
        ultimate_level = [g.make_random_input_wire("W" + str(gate_num))
                          for gate_num in xrange(W)]
        # a dictionary mapping each gate to how many times it was used as input:
        num_uses_dict = dict(
            (wire.get_name(), 0) for wire in ultimate_level)
        # a dictionary mapping gate type to a list of the number of times
        # that gate type is generated:
        gate_type_dict = dict(
            (gate_type, 0) for gate_type in g.GATE_TYPES.values_generator())
        for trial_num in xrange(num_trials):
            # create a new gate:
            gate = generate(ultimate_level, fanin_frac, "this_gate")
            # add the statistics to num_uses and gate_type_dist:
            gate_type_dict[gate.get_func_name()] += 1
            for wire in gate.get_inputs():
                num_uses_dict[wire.get_name()] += 1
        # make sure that each gate type appears between .2 and .8 of the time:
        # (note that these numbers are chosen randomly, and therefor this test
        # might occasionally fail with a low probability)
        for gate_type in gate_type_dict.keys():
            self.assertTrue(float(gate_type_dict[gate_type]) / float(num_trials)
                            > .2)
            self.assertTrue(float(gate_type_dict[gate_type]) / float(num_trials)
                            < .8)
        # make sure that each wire is chosen as input between .2 and .8 of the
        # time: (note that these numbers are chosen randomly, and therefor this
        # test might occasionally fail with a low probability)
        for wire in num_uses_dict.keys():
            self.assertTrue(float(num_uses_dict[wire]) / float(num_trials)
                            > (fanin_frac) / 2.0)
            self.assertTrue(float(num_uses_dict[wire]) / float(num_trials)
                            < max(fanin_frac * 2.0, 1.0))

    def test_make_uniform_random_f3_gate(self):
        """
        tests that the distribution of gate types is uniform in the uniform f3
        gate maker.
        """
        num_trials = 100
        fanin_frac = .5
        # test fam1 and fam2 gates:
        generate = g.TYPE_TO_FAM3_GATE_GEN[g.TEST_TYPES.RANDOM]
        W = 10
        num_levels = 2
        levels = [[g.make_random_input_wire(
            "W" + str((W * level_num) + gate_num))
                   for gate_num in xrange(W)]
                  for level_num in xrange(num_levels)]
        # a dictionary mapping each gate to how many times it was used as input:
        num_uses_dict = {}
        for level in levels:
            for wire in level:
                num_uses_dict[wire.get_name()] = 0
        # a dictionary mapping gate type to a list of the number of times
        # that gate type is generated:
        gate_type_dict = dict(
            (gate_type, 0) for gate_type in g.GATE_TYPES.values_generator())
        for trial_num in xrange(num_trials):
            # create a new gate:
            gate = generate(levels, "this_gate")
            # add the statistics to num_uses and gate_type_dist:
            gate_type_dict[gate.get_func_name()] += 1
            for wire in gate.get_inputs():
                num_uses_dict[wire.get_name()] += 1
        # make sure that each gate type appears between .2 and .8 of the time:
        # (note that these numbers are chosen randomly, and therefor this test
        # might occasionally fail with a low probability)
        for gate_type in gate_type_dict.keys():
            self.assertTrue(float(gate_type_dict[gate_type]) / float(num_trials)
                            > .2)
            self.assertTrue(float(gate_type_dict[gate_type]) / float(num_trials)
                            < .8)
        # make sure that each wire in the ultimate level is chosen as input
        # between 1/(2*W) and (W-1)/W of the time:
        # (note that these numbers are chosen randomly, and therefor this test
        # might occasionally fail with a low probability)
        for wire in levels[-1]:
            self.assertTrue(float(num_uses_dict[wire.get_name()])
                            / float(num_trials)
                            > 1.0 / float(2.0 * W))
            self.assertTrue(float(num_uses_dict[wire.get_name()])
                            / float(num_trials)
                            < (float(W) - 1.0) / float(2.0 * W))
        # make sure that each wire in the other levels is chosen as input
        # between 1/(2*W*num_levels) and (W-1)/(2*W*num_levels) of the time:
        # (note that these numbers are chosen randomly, and therefor this test
        # might occasionally fail with a low probability)
        for level in levels[:-1]:
            for gate in level:
                self.assertTrue(float(num_uses_dict[wire.get_name()])
                                / float(num_levels)
                                > 1.0 / float(2 * W * num_levels))
                self.assertTrue(float(num_uses_dict[wire.get_name()])
                                / float(num_trials)
                                < (float(W) - 1.0) / float(2 * W * num_levels))

    def test_get_prob_needs_trimming(self):
        """
        Tests that the get_prob_needs_trimming function functions as desired.
        """
        # for a family 1 circuit:
        level_type_array = [g.LEVEL_TYPES.RANDOM]
        W = 2
        G = 2
        fg = .5
        X = None
        fx = None
        desired_prob = 1.0 - ((1.0 - ((1 - fg) ** G)) ** 2)
        self.assertEqual(g.get_prob_needs_trimming(W, G, fg, X, fx,
                                                   level_type_array),
                         desired_prob)

    def test_f1_circuit_maker(self):
        """
        Tests that the family 1 circuit makers function as desired.
        Makes sure that the trimming and no-trimming methods both produce
        the same inputs and outputs under the same randomness, and have the
        same circuit headers.
        """
        fho = tfho.TestFileHandleObject()
        W = 5
        G = 20
        fg = .9
        X = 10
        fx = .85
        gate_maker = g.TYPE_TO_GATE_GEN[g.TEST_TYPES.RANDOM]
        # family 1 files:
        t_circuit_file_name = "circuit_file_trimming"
        t_circuit_file = fho.get_file_object(t_circuit_file_name, 'w')
        t_input_file_name = "input_file_trimming"
        t_input_file = fho.get_file_object(t_input_file_name, 'w')
        t_output_file_name = "output_file_trimming"
        t_output_file = fho.get_file_object(t_output_file_name, 'w')
        nt_circuit_file_name = "circuit_file_no_trimming"
        nt_circuit_file = fho.get_file_object(nt_circuit_file_name, 'w')
        nt_input_file_name = "input_file_no_trimming"
        nt_input_file = fho.get_file_object(nt_input_file_name, 'w')
        nt_output_file_name = "output_file_no_trimming"
        nt_output_file = fho.get_file_object(nt_output_file_name, 'w')
        level_type_array = [g.LEVEL_TYPES.RANDOM]
        F = 1
        # make a family 1 circuit with trimming:
        sr.seed(self.rand_seed)
        t_gen = g.f1f2_circuit_maker_with_trimming_switch(W, G, fg,
                                                     t_circuit_file,
                                                     t_input_file,
                                                     t_output_file,
                                                     X, fx, gate_maker,
                                                     level_type_array, True)
        t_gen.generate()
        # make a family 1 circuit without trimming, with the same randomness:
        sr.seed(self.rand_seed)
        nt_gen = g.f1f2_circuit_maker_with_trimming_switch(W, G, fg,
                                                      nt_circuit_file,
                                                      nt_input_file,
                                                      nt_output_file,
                                                      X, fx, gate_maker,
                                                      level_type_array, False)
        nt_gen.generate()
        # obtain strings representing the contents of all the resulting files:
        t_circuit_string = fho.get_file(t_circuit_file_name).getvalue()
        t_input_string = fho.get_file(t_input_file_name).getvalue()
        t_output_string = fho.get_file(t_output_file_name).getvalue()
        nt_circuit_string = fho.get_file(nt_circuit_file_name).getvalue()
        nt_input_string = fho.get_file(nt_input_file_name).getvalue()
        nt_output_string = fho.get_file(nt_output_file_name).getvalue()
        # make sure that the inputs and outputs produced by the trimming and
        # no trimming algorithms are the same:
        self.assertEqual(t_input_string, nt_input_string)
        self.assertEqual(t_output_string, nt_output_string)
        # make sure that the input begins and ends with a bracket:
        self.assertEqual("[", t_input_string[0])
        self.assertEqual("]", t_input_string[-1])
        # make sure that each input element is a bit:
        for bit in t_input_string[1:-1]:
            self.assertTrue((bit == '0') or (bit == '1'))
        # make sure that the output is a bit:
        self.assertTrue((t_output_string == '0') or (t_output_string == '1'))
        # make sure that the two circuit headers are the same, and that they
        # contain the correct values:
        t_circuit_header = t_circuit_string.split("\n")[0]
        nt_circuit_header = nt_circuit_string.split("\n")[0]
        self.assertEqual(t_circuit_header, nt_circuit_header)
        (W_string, G_string, F_string) = t_circuit_header.split(",")
        W_value = int(W_string.split("=")[-1])
        G_value = int(G_string.split("=")[-1])
        F_value = int(F_string.split("=")[-1])
        self.assertEqual(W, W_value)
        self.assertEqual(G, G_value)
        self.assertEqual(F, F_value)
        # note that we cannot test that the circuits themselves are the same,
        # because the trimming algorithm produces a circuit with gates listed
        # in a different order.

    def test_f2_circuit_maker(self):
        """
        Tests that the family 2 circuit makers function as desired.
        Makes sure that the trimming and no-trimming methods both produce
        the same inputs and outputs under the same randomness, and have the
        same circuit headers.
        """
        fho = tfho.TestFileHandleObject()
        W = 5
        G = 20
        fg = .9
        X = 10
        fx = .85
        gate_maker = g.TYPE_TO_GATE_GEN[g.TEST_TYPES.RANDOM]
        # family 2 files:
        t_circuit_file_name = "circuit_file_trimming"
        t_circuit_file = fho.get_file_object(t_circuit_file_name, 'w')
        t_input_file_name = "input_file_trimming"
        t_input_file = fho.get_file_object(t_input_file_name, 'w')
        t_output_file_name = "output_file_trimming"
        t_output_file = fho.get_file_object(t_output_file_name, 'w')
        nt_circuit_file_name = "circuit_file_no_trimming"
        nt_circuit_file = fho.get_file_object(nt_circuit_file_name, 'w')
        nt_input_file_name = "input_file_no_trimming"
        nt_input_file = fho.get_file_object(nt_input_file_name, 'w')
        nt_output_file_name = "output_file_no_trimming"
        nt_output_file = fho.get_file_object(nt_output_file_name, 'w')
        level_type_array = [g.LEVEL_TYPES.XOR, g.LEVEL_TYPES.RANDOM,
                            g.LEVEL_TYPES.XOR]
        F = 2
        # make a family 1 circuit with trimming:
        sr.seed(self.rand_seed)
        t_gen = g.f1f2_circuit_maker_with_trimming_switch(W, G, fg,
                                                     t_circuit_file,
                                                     t_input_file,
                                                     t_output_file,
                                                     X, fx, gate_maker,
                                                     level_type_array, True)
        t_gen.generate()
        # make a family 1 circuit without trimming, with the same randomness:
        sr.seed(self.rand_seed)
        nt_gen = g.f1f2_circuit_maker_with_trimming_switch(W, G, fg,
                                                      nt_circuit_file,
                                                      nt_input_file,
                                                      nt_output_file,
                                                      X, fx, gate_maker,
                                                      level_type_array, False)
        nt_gen.generate()
        # obtain strings representing the contents of all the resulting files:
        t_circuit_string = fho.get_file(t_circuit_file_name).getvalue()
        t_input_string = fho.get_file(t_input_file_name).getvalue()
        t_output_string = fho.get_file(t_output_file_name).getvalue()
        nt_circuit_string = fho.get_file(nt_circuit_file_name).getvalue()
        nt_input_string = fho.get_file(nt_input_file_name).getvalue()
        nt_output_string = fho.get_file(nt_output_file_name).getvalue()
        # make sure that the inputs and outputs produced by the trimming and
        # no trimming algorithms are the same:
        self.assertEqual(t_input_string, nt_input_string)
        self.assertEqual(t_output_string, nt_output_string)
        # make sure that the input begins and ends with a bracket:
        self.assertEqual("[", t_input_string[0])
        self.assertEqual("]", t_input_string[-1])
        # make sure that each input element is a bit:
        for bit in t_input_string[1:-1]:
            self.assertTrue((bit == '0') or (bit == '1'))
        # make sure that the output is a bit:
        self.assertTrue((t_output_string == '0') or (t_output_string == '1'))
        # make sure that the two circuit headers are the same, and that they
        # contain the correct values:
        t_circuit_header = t_circuit_string.split("\n")[0]
        nt_circuit_header = nt_circuit_string.split("\n")[0]
        self.assertEqual(t_circuit_header, nt_circuit_header)
        (W_string, G_string, X_string, F_string) = t_circuit_header.split(",")
        W_value = int(W_string.split("=")[-1])
        G_value = int(G_string.split("=")[-1])
        X_value = int(X_string.split("=")[-1])
        F_value = int(F_string.split("=")[-1])
        self.assertEqual(W, W_value)
        self.assertEqual(G, G_value)
        self.assertEqual(F, F_value)
        # note that we cannot test that the circuits themselves are the same,
        # because the trimming algorithm produces a circuit with gates listed
        # in a different order.

    def test_f3_circuit_maker(self):
        """
        Tests that the family 3 circuit makers function as desired.
        """
        fho = tfho.TestFileHandleObject()
        W = 5
        D = 6
        gate_maker = g.TYPE_TO_FAM3_GATE_GEN[g.TEST_TYPES.RANDOM]
        # family 3 files:
        circuit_file_name = "circuit_file"
        circuit_file = fho.get_file_object(circuit_file_name, 'w')
        input_file_name = "input_file"
        input_file = fho.get_file_object(input_file_name, 'w')
        output_file_name = "output_file"
        output_file = fho.get_file_object(output_file_name, 'w')
        F = 3
        # make a family 3 circuit:
        sr.seed(self.rand_seed)
        gen = g.f3_circuit_maker(W, D, circuit_file, input_file, output_file,
                                   gate_maker)
        gen.generate()
        # obtain strings representing the contents of all the resulting files:
        circuit_string = fho.get_file(circuit_file_name).getvalue()
        input_string = fho.get_file(input_file_name).getvalue()
        output_string = fho.get_file(output_file_name).getvalue()
        # make sure that the input begins and ends with a bracket:
        self.assertEqual("[", input_string[0])
        self.assertEqual("]", input_string[-1])
        # make sure that each input element is a bit:
        for bit in input_string[1:-1]:
            self.assertTrue((bit == '0') or (bit == '1'))
        # make sure that the output is a bit:
        self.assertTrue((output_string == '0') or (output_string == '1'))
        # make sure that the circuit header contains the correct values:
        circuit_header = circuit_string.split("\n")[0]
        (W_string, D_string, F_string) = circuit_header.split(",")
        W_value = int(W_string.split("=")[-1])
        D_value = int(D_string.split("=")[-1])
        F_value = int(F_string.split("=")[-1])
        self.assertEqual(W, W_value)
        self.assertEqual(D, D_value)
        self.assertEqual(F, F_value)

