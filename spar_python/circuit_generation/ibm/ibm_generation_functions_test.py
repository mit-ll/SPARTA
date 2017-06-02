# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 circuit generation function test class
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  12 Nov 2012   SY             Original Version
# *****************************************************************

# general imports:
import math
import time
import unittest

# SPAR imports:
import spar_python.circuit_generation.ibm.ibm_generation_functions as g
import spar_python.common.spar_random as sr

class generation_functions_test(unittest.TestCase):

    def setUp(self):
        """
        Records the randomness used.
        """
        # record the randomness used in case the test fails:
        rand_seed = int(time.time())
        sr.seed(rand_seed)
        print("seed for this test: " + str(rand_seed))        

    def test_dist_gates(self):
        """
        tests that the distribution of gate types is not too skewed in circuit
        generation with random gate type.
        Specifically, tests that the fraction of gates belonging to
        each gate type is between 1/24 and 1/3. Note that these bounds are
        arbitary, and there is some very small chance that this test will fail.
        It should pass with overwhelming probability, however.
        """
        generate = g.TEST_TYPE_TO_GENERATOR_BY_DEPTH[g.TEST_TYPES.RANDOM]
        L = 100
        D = 10
        W = 10
        num_trials = 50
        # a dictionary mapping gate type to a list of the number of times
        # that gate type appears in each circuit generated:
        gate_type_dist = dict(
            (gate_type, []) for gate_type in g.GATE_TYPES.values_generator())
        # a dictionary mapping gate type to the number of times that gate type
        # appears as the output gate:
        output_gate_type_dist = dict(
            (gate_type, 0) for gate_type in g.GATE_TYPES.values_generator())
        for trial_num in xrange(num_trials):
            # create a new circuit:
            circ = generate(L, D, W)
            # get a dictionary mapping each gate type to the number of times it
            # appears in the new circuit: 
            dist = dict(
                (gate_type, 0) for gate_type in g.GATE_TYPES.values_generator())
            levels = circ.get_levels()
            for level_num in xrange(1, len(levels)):
                level = levels[level_num]
                for gate in level:
                    dist[gate.get_func_name()] += 1
            # add these numbers to gate_type_dist:
            for key in dist.keys():
                gate_type_dist[key].append(dist[key])
            # keep track of the number of output gates of each type:
            output_gate_type = circ.get_levels()[-1][0].get_func_name()
            output_gate_type_dist[output_gate_type] += 1
        # the average number of gates of each type per circuit:
        averages = [float(sum(gate_type_dist[key])) / float(num_trials)
                    for key in gate_type_dist.keys()]
        # make sure that the average number of gates of each type per circuit
        # is between 1/24 and 1/3 of the total of the averages:
        for num in averages:
            self.assertTrue(float(num) / float(sum(averages)) > 1.0 / 24.0)
            self.assertTrue(float(num) / float(sum(averages)) < 1.0 / 3.0)
        # make sure that the number of output gates of each type is between
        # 1/24 and 1/3 of the total number of circuits created
        for key in output_gate_type_dist.keys():
            self.assertTrue(
                float(output_gate_type_dist[key]) / float(num_trials)
                > 1.0 / 24.0)
            self.assertTrue(
                float(output_gate_type_dist[key]) / float(num_trials)
                < 1.0 / 3.0)

    def test_depth(self):
        """
        Tests that the depth is as desired.
        """
        generate = g.TEST_TYPE_TO_GENERATOR_BY_DEPTH[g.TEST_TYPES.RANDOM]
        L = 100
        D = 10
        W = 10
        num_trials = 50
        for counter1 in range(num_trials):
            circ = generate(L, D, W)
            self.assertTrue(circ.get_depth() < float(D) + 1.0)
            self.assertTrue(circ.get_depth() >= float(D))

    def test_single_gate_type_dist_gates(self):
        """
        Tests that single gate type circuits have the correct gate types.
        """
        num_trials = 50
        L = 100
        num_levels = 5
        W = 10
        for gate_type_ind in g.GATE_TYPES.numbers_generator():
            gate_type_string = g.GATE_TYPES.to_string(gate_type_ind)
            generate = g.TEST_TYPE_TO_GENERATOR_BY_LEVEL[gate_type_ind]
            for trial_num in xrange(num_trials):
                circ = generate(L, num_levels, W)
                levels = circ.get_levels()[1:]
                for level in levels:
                    for gate in level:
                        self.assertEqual(gate_type_string,
                                         gate.get_func_name())

    def test_single_gate_type_num_levels(self):
        """
        Tests that single gate type circuits have the desired number of levels.
        """
        num_trials = 50
        L = 100
        W = 10
        num_levels = 5
        for gate_type_ind in g.GATE_TYPES.numbers_generator():
            gate_type_string = g.GATE_TYPES.to_string(gate_type_ind)
            generate = g.TEST_TYPE_TO_GENERATOR_BY_LEVEL[gate_type_ind]
            for trial_num in xrange(num_trials):
                circ = generate(L, num_levels, W)
                self.assertEqual(num_levels, circ.get_num_levels())

