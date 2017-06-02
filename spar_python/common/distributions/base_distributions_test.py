# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for distributions.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  21 Sep 2012   jch            Original Version
# *****************************************************************


import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)



import spar_python.common.distributions.base_distributions \
    as base_distributions
import spar_python.common.spar_random as spar_random
import spar_python.common.enum as enum
import time
import unittest

VARS = enum.Enum('AHA','BAR', 'BAT','BAZ', 'FOO', 'WOM')

class IndependentDistributionTest(unittest.TestCase): 

    def setUp(self):
                
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        
        self.simple = base_distributions.SimpleIndependentDistribution
        self.compact = base_distributions.CompactIndependentDistribution
        self.compact_dist = base_distributions.CompactIndependentDistribution()
        self.simple_dist = base_distributions.SimpleIndependentDistribution()

    def helper_correct_distribution_unweighted(self, dist):
        """
        Test template:
        
        If we set up a distribution object with 2 obsevations of
        'hello' and one each of 'there' and 'world' we expect that
        many calls to generate() should produce roughly 1/2 'hello'
        instances and 1/4 of both 'there' and 'world' instances.
        """
        dist.add('hello')
        dist.add('hello')
        dist.add('there')
        dist.add('world')
        observed = {'hello': 0, 'there': 0, 'world': 0}

        # Generate random observations
        num_observations = 2000
        hello_observations = num_observations * 0.5
        hello_tolerance = num_observations * 0.1
        other_observations = num_observations * 0.25
        other_tolerance = num_observations * 0.05
        for i in xrange(num_observations):
            value = dist.generate()
            observed[value] += 1

        # 1/2 would be expected but that's not guaranteed as this is random.
        # However, it should almost always be between some tolerance.
        self.assertGreater(observed['hello'], 
                           hello_observations - hello_tolerance, self.seed_msg)
        self.assertLess(observed['hello'], 
                        hello_observations + hello_tolerance, self.seed_msg)

        # 1/4 is expected.
        self.assertGreater(observed['there'], 
                           other_observations - other_tolerance, self.seed_msg)
        self.assertLess(observed['there'], 
                        other_observations + other_tolerance, self.seed_msg)

        self.assertGreater(observed['world'], 
                        other_observations - other_tolerance, self.seed_msg)
        self.assertLess(observed['world'], 
                        other_observations + other_tolerance, self.seed_msg)


    def helper_correct_distribution_weighted(self, dist):
        """
        Test template:

        If we set up a distribution object with 2 obsevations of
        'hello' each with weight 1, and one each of 'there' and
        'world' (with weight 2 each) we expect that many calls to
        generate() should produce roughly the same number of 'hello'
        'there' and 'world' instances.
        """
        dist.add('hello', 1)
        dist.add('hello', weight=1)
        dist.add('there', 2)
        dist.add('world', weight=2)
        observed = {'hello': 0, 'there': 0, 'world': 0}

        # Generate 900 random observations
        for i in xrange(900):
            value = dist.generate()
            observed[value] += 1

        # 1/3 == 300 so we expect observed values between 200 and 300.
        self.assertGreater(observed['hello'], 250, self.seed_msg)
        self.assertLess(observed['hello'], 350, self.seed_msg)

        self.assertGreater(observed['there'], 250, self.seed_msg)
        self.assertLess(observed['there'], 350, self.seed_msg)

        self.assertGreater(observed['world'], 250, self.seed_msg)
        self.assertLess(observed['world'], 350, self.seed_msg)

    def helper_generate_single_sided_range_string(self, dist):
        dist.add('a',1)
        dist.add('b',2)
        dist.add('c',1)
        observed_less = {'a':0, 'b':0, 'c':0}
        observed_greater = {'a':0, 'b':0, 'c':0}
        
        for _ in xrange(500):
            value_less = dist.generate_less_than(0,0.25)
            value_greater = dist.generate_greater_than(0,0.25)
            observed_less[value_less] += 1
            observed_greater[value_greater] +=1
        self.assertEqual(observed_less['a'], 500)
        self.assertEqual(observed_less['b'], 0)
        self.assertEqual(observed_less['c'], 0)
        
        self.assertEqual(observed_greater['a'], 0)
        self.assertEqual(observed_greater['b'], 0)
        self.assertEqual(observed_greater['c'], 500)
        
    def helper_generate_single_sided_range_int_enum(self, dist):
        dist.add(1,1)
        dist.add(2,2)
        dist.add(3,1)
        observed_less = {1:0, 2:0, 3:0}
        observed_greater = {1:0, 2:0, 3:0}
        for _ in xrange(500):
            value_less = dist.generate_less_than(0,0.25)
            value_greater = dist.generate_greater_than(0,0.25)
            observed_less[value_less] += 1
            observed_greater[value_greater] += 1
            
        self.assertEqual(observed_less[1], 500)
        self.assertEqual(observed_less[2], 0)
        self.assertEqual(observed_less[3], 0)
        
        self.assertEqual(observed_greater[1], 0)
        self.assertEqual(observed_greater[2], 0)
        self.assertEqual(observed_greater[3], 500)
    
    def helper_generate_double_sided_range_string(self, dist):
        dist.add('a',1)
        dist.add('b',1)
        dist.add('c',1)
        dist.add('d',1)
        dist.add('e',1)
        observed = {('a','b') : 0, ('b','c') : 0,
                    ('c','d') : 0, ('d','e') : 0}
        not_valid =0
        num_iterations = 1000
        expected_mean = num_iterations * 0.25
        tolerance = num_iterations * 0.0625
        for _ in xrange(num_iterations):
            value = dist.generate_double_range(0,0.2)
            try:
                observed[value] += 1
            except KeyError:
                print value
                not_valid +=1

        self.assertEqual(not_valid, 0)
       
        self.assertGreater(observed[('a','b')], expected_mean - tolerance)
        self.assertLess(observed[('a','b')], expected_mean + tolerance)

        self.assertGreater(observed[('b','c')], expected_mean - tolerance)
        self.assertLess(observed[('b','c')], expected_mean + tolerance)
        
        self.assertGreater(observed[('c','d')], expected_mean - tolerance)
        self.assertLess(observed[('c','d')], expected_mean + tolerance)
        
        self.assertGreater(observed[('d','e')], expected_mean - tolerance)
        self.assertLess(observed[('d','e')], expected_mean + tolerance)
        
    
        
    def helper_generate_double_sided_range_int_enum(self, dist):
        dist.add(1,1)
        dist.add(2,1)
        dist.add(3,1)
        dist.add(4,1)
        dist.add(5,1)
        observed = {(1,2) : 0, (2,3) : 0, 
                    (3,4) : 0, (4,5) : 0}
        not_valid =0
        num_iterations = 1000
        expected_mean = num_iterations * 0.25
        tolerance = num_iterations * 0.0625
        for _ in xrange(num_iterations):
            value = dist.generate_double_range(0,0.2)
            try:
                observed[value] += 1
            except KeyError:
                print value
                not_valid +=1
        print observed
        self.assertEqual(not_valid, 0)
        
        self.assertGreater(observed[(1,2)], expected_mean - tolerance)
        self.assertLess(observed[(1,2)], expected_mean + tolerance)

        self.assertGreater(observed[(2,3)], expected_mean - tolerance)
        self.assertLess(observed[(2,3)], expected_mean + tolerance)
        
        self.assertGreater(observed[(3,4)], expected_mean - tolerance)
        self.assertLess(observed[(3,4)], expected_mean + tolerance)
        
        self.assertGreater(observed[(4,5)], expected_mean - tolerance)
        self.assertLess(observed[(4,5)], expected_mean + tolerance)

        
    def helper_remap_pregeneration(self, dist):
        dist.add('hello', 3)
        dist.add('there', 1)
        dist.add('world', 2)
        dist.remap('hello', 'bye')
        observed = {'hello': 0, 'there': 0, 'world': 0, 'bye': 0}
        # Generate random observations
        num_observations = 1800
        bye_observations = num_observations * 0.5
        bye_tolerance = 50 / 900.0 * num_observations
        for i in xrange(num_observations):
            value = dist.generate()
            observed[value] += 1
        
        self.assertEqual(observed['hello'], 0)
        self.assertGreaterEqual(observed['bye'], 
                                bye_observations - bye_tolerance)
        self.assertLessEqual(observed['bye'], 
                             bye_observations + bye_tolerance)

    def helper_remap_postgeneration(self, dist):
        dist.add('hello', 3)
        dist.add('there', 1)
        dist.add('world', 2)
        dist.generate()
        dist.remap('hello', 'bye')
        observed = {'hello': 0, 'there': 0, 'world': 0, 'bye': 0}
        # Generate random observations
        num_observations = 1800
        bye_observations = num_observations * 0.5
        bye_tolerance = 50 / 900.0 * num_observations
        for i in xrange(num_observations):
            value = dist.generate()
            observed[value] += 1
        
        self.assertEqual(observed['hello'], 0, self.seed_msg)
        self.assertGreaterEqual(observed['bye'], 
                                bye_observations - bye_tolerance)
        self.assertLessEqual(observed['bye'], 
                             bye_observations + bye_tolerance)

    def helper_generate_cdf_delinated(self, dist):
        dist.add('hello',3)
        dist.add('there',1)
        observed = {'hello': 0, 'there': 0}
        for i in xrange(500):
            value  = dist.generate_pdf(0.0,0.24)
            observed[value]+=1
        
        self.assertEqual(observed['hello'], 0, self.seed_msg)

        self.assertEqual(observed['there'], 500, self.seed_msg)
        
    def helper_generate_cdf_nondelinated(self, dist):
        dist.add('hello',6)
        dist.add('there',4)
        observed = {'hello': 0, 'there': 0}
        num_iterations = 10000
        hello_mean = num_iterations * 0.6
        there_mean = num_iterations * 0.4
        tolerance = num_iterations * 0.15
        for i in xrange(num_iterations):
            value  = dist.generate_pdf(0.3,0.7)
            observed[value]+=1
        self.assertGreaterEqual(observed['hello'], 
                                hello_mean - tolerance, self.seed_msg)
        self.assertLessEqual(observed['hello'], 
                             hello_mean + tolerance, self.seed_msg)

        self.assertGreaterEqual(observed['there'], 
                                there_mean - tolerance, self.seed_msg)
        self.assertLessEqual(observed['there'], 
                             there_mean + tolerance, self.seed_msg)
    
    def helper_generate_cdf_empty(self, dist):
        self.assertRaises(AssertionError, dist.generate_pdf, 0.0, 0.5)
        
    def helper_generate_cdf_nearly_empty(self, dist):
        dist.add('hello',1)
        valuedel = dist.generate_pdf(0, 1)
        valuenondel = dist.generate_pdf(0,0.5)
        self.assertEqual(valuedel, 'hello')
        self.assertEqual(valuenondel,'hello')

    def helper_support_and_size(self, dist):
        dist.add('hello', 6)
        dist.add('hello', 4)
        dist.add('there', 1)
        self.assertEqual(dist.size(), 2)
        self.assertSetEqual(dist.support(), set(['hello', 'there']))

        
    def test_compact_distribution_buckets(self):
        """
        Run the helper_generate_cdf_delinated test on
        CompactIndependentDistribution class.
        """
        dist = self.compact_dist
        self.helper_generate_cdf_delinated(dist)
        
    def test_compact_distribution_buckets2(self):
        """
        Run the helper_generate_cdf_nondelinated test on
        CompactIndependentDistribution class.
        """
        dist = self.compact_dist
        self.helper_generate_cdf_nondelinated(dist)
    
    def test_simple_distribution_buckets(self):
        """
        Run the helper_generate_cdf_delinated test on
        SimpleIndependentDistribution class.
        """
        dist = self.simple_dist
        self.helper_generate_cdf_delinated(dist)
        
    def test_simple_distribution_buckets(self):
        """
        Run the helper_generate_cdf_delinated test on
        SimpleIndependentDistribution class.
        """
        dist = self.simple_dist
        self.helper_generate_cdf_nondelinated(dist)
    
    def test_compact_empty(self):
        dist = self.compact_dist
        self.helper_generate_cdf_empty(dist)
        
    def test_simple_empty(self):
        dist = self.simple_dist
        self.helper_generate_cdf_empty(dist)
    
    def test_compact_nearly_empty(self):
        dist = self.compact_dist
        self.helper_generate_cdf_nearly_empty(dist)
        
    def test_simple_nearly_empty(self):
        dist = self.simple_dist
        self.helper_generate_cdf_nearly_empty(dist)
        
    def test_compact_distribution_unweighted(self):
        """
        Run the helper_correct_distribution_unweighted test on
        CompactIndependentDistribution class.
        """
        dist = self.compact_dist
        self.helper_correct_distribution_unweighted(dist)


    def test_simple_distribution_unweighted(self):
        """
        Run the helper_correct_distribution_unweighted test on
        SimpleIndependentDistribution class.
        """
        dist = self.simple_dist
        self.helper_correct_distribution_unweighted(dist)


    def test_compact_distribution_weighted(self):
        """
        Run the helper_correct_distribution_weighted test on
        CompactIndependentDistribution class.
        """
        dist = self.compact_dist
        self.helper_correct_distribution_weighted(dist)


    def test_simple_distribution_weighted(self):
        """
        Run the helper_correct_distribution_weighted test on
        SimpleIndependentDistribution class.
        """
        dist = self.simple_dist
        self.helper_correct_distribution_weighted(dist)


    def test_compact_distribution_remap_pregen(self):
        """
        Run the helper_correct_distribution_weighted test on
        SimpleIndependentDistribution class.
        """
        dist = self.compact_dist
        self.helper_remap_pregeneration(dist)

    def test_compact_distribution_remap_postgen(self):
        """
        Run the helper_correct_distribution_weighted test on
        SimpleIndependentDistribution class.
        """
        dist = self.compact_dist
        self.helper_remap_postgeneration(dist)


    def test_simple_distribution_remap_pregen(self):
        """
        Run the helper_correct_distribution_weighted test on
        SimpleIndependentDistribution class.
        """
        dist = self.simple_dist
        self.helper_remap_pregeneration(dist)

    def test_simple_distribution_remap_postgen(self):
        """
        Run the helper_correct_distribution_weighted test on
        SimpleIndependentDistribution class.
        """
        dist = self.simple_dist
        self.helper_remap_postgeneration(dist)

    def test_simple_support_and_size(self):
        """
        Run the helper_support_and_size test on
        SimpleIndependentDistribution class.
        """
        dist = self.simple_dist
        self.helper_support_and_size(dist)

    def test_compact_support_and_size(self):
        """
        Run the helper_support_and_size test on
        CompactIndependentDistribution class.
        """
        dist = self.compact_dist
        self.helper_support_and_size(dist)
    
    def test_simple_single_sided_range_string(self):
        """
        Run helper_generate_single_sided_range_* to test
        single sided ranges for strings
        in simple dists
        """
        dist = self.simple_dist
        self.helper_generate_single_sided_range_string(dist)
        
    def test_simple_single_sided_range_int(self):
        """
        Run helper_generate_single_sided_range_* to test
        single sided ranges for int in simple dist
        """
        dist = self.simple_dist 
        self.helper_generate_single_sided_range_int_enum(dist)
        
    def test_simple_single_sided_range_enum(self):
        """
        Run helper_generate_single_sided_range_* to test
        single sided ranges for enums in simple dists
        """    
        dist = self.simple(VARS)
        self.helper_generate_single_sided_range_int_enum(dist)
    
    def test_compact_single_sided_range_string(self):
        """
        Run helper_generate_single_sided_range_* to test
        single sided ranges for strings
        in compact dists
        """
        dist = self.compact_dist
        self.helper_generate_single_sided_range_string(dist)
        
    def test_compact_single_sided_range_int(self):
        """
        Run helper_generate_single_sided_range_* to test
        single sided ranges for int in compact dist
        """
        dist = self.compact_dist 
        self.helper_generate_single_sided_range_int_enum(dist)
        
    def test_compact_single_sided_range_enum(self):
        """
        Run helper_generate_single_sided_range_* to test
        single sided ranges for enums in compact dists
        """    
        dist = self.compact(VARS)
        self.helper_generate_single_sided_range_int_enum(dist)
        
    
    def test_simple_double_sided_range_string(self):
        """
        Run helper_generate_double_sided_range_* to test
        double sided range generation for strings, ints, and
        enums for simple dists
        """  
        dist = self.simple_dist
        self.helper_generate_double_sided_range_string(dist)
        
    def test_simple_double_sided_range_int(self):
        """
        Run helper_generate_double_sided_range_* to test
        double sided range generation for strings, ints, and
        enums for simple dists
        """  
        dist = self.simple_dist
        self.helper_generate_double_sided_range_int_enum(dist)
        
    def test_simple_double_sided_range_enum(self):
        """
        Run helper_generate_double_sided_range_* to test
        double sided range generation for strings, ints, and
        enums for simple dists
        """  
        dist = self.simple(VARS)
        self.helper_generate_double_sided_range_int_enum(dist)
        
    def test_compact_double_sided_range_string(self):
        """
        Run helper_generate_double_sided_range_* to test
        double sided range generation for strings, ints, and
        enums for compact dists
        """  
        dist = self.compact_dist
        self.helper_generate_double_sided_range_string(dist)
        
    def test_compact_double_sided_range_int(self):
        """
        Run helper_generate_double_sided_range_* to test
        double sided range generation for strings, ints, and
        enums for compact dists
        """  
        dist = self.compact_dist
        self.helper_generate_double_sided_range_int_enum(dist)
    def test_compact_double_sided_range_enum(self):
        """
        Run helper_generate_double_sided_range_* to test
        double sided range generation for strings, ints, and
        enums for compact dists
        """  
        dist = self.compact(VARS)
        self.helper_generate_double_sided_range_int_enum(dist)
        
class ConditionalDistributionTest(unittest.TestCase): 

    def setUp(self):
                
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

        self.compact_dist = \
                base_distributions.CompactConditionalDistribution(VARS.FOO)
        self.simple_dist = \
                base_distributions.SimpleConditionalDistribution(VARS.FOO)
        self.compact_dist_2d = \
                base_distributions.CompactConditionalDistribution(VARS.FOO, VARS.BAR)
        self.simple_dist_2d = \
                base_distributions.SimpleConditionalDistribution(VARS.FOO, VARS.BAR)


    def helper_correct_distribution_unweighted(self, dist):
        """
        Test template:
        
        Set up a conditonal probability, conditioned on VARS.FOO.  For
        VARS.FOO equal to True, add 'hello' twice and 'there'
        once. For VARS.FOO equal False, reverse these
        frequencies. Then test we get roughly the right distributions
        from generate().
        """
        dist.add('hello', 1, True)
        dist.add('hello', 1, True)
        dist.add('there', 1, True)

        dist.add('hello', 1, False)
        dist.add('there', 1, False)
        dist.add('there', 1, False)

        # Test 'FOO' = True
        observed = {'hello': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : True} )
            observed[value] += 1
        self.assertGreater(observed['hello'], 1500, self.seed_msg)
        self.assertLess(observed['hello'], 2500, self.seed_msg)
        self.assertGreater(observed['there'], 500, self.seed_msg)
        self.assertLess(observed['there'], 1500, self.seed_msg)

        # Test 'FOO' = False
        observed = {'hello': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : False} )
            observed[value] += 1
        self.assertGreater(observed['hello'], 500, self.seed_msg)
        self.assertLess(observed['hello'], 1500, self.seed_msg)
        self.assertGreater(observed['there'], 1500, self.seed_msg)
        self.assertLess(observed['there'], 2500, self.seed_msg)


    def helper_correct_ind_vars(self, dist):
        """
        Test template:
        
        Testing distribitions conditioned on multiple independent
        variables, and the case where generate() is given a dictionary
        with extraneous values.
        """
        dist.add('hello', 1, True, True)
        dist.add('hello', 1, True, True)
        dist.add('there', 1, True, True)

        dist.add('hello', 1, True, False)
        dist.add('there', 1, True, False)
        dist.add('there', 1, True, False)

        dist.add('hello', 1, False, True)
        dist.add('hello', 1, False, True)
        dist.add('hello', 1, False, True)

        dist.add('there', 1, False, False)
        dist.add('there', 1, False, False)
        dist.add('there', 1, False, False)
        
        # Test FOO : True, BAR : True 
        observed = {'hello': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( { VARS.FOO : True,
                                     VARS.BAR : True,
                                     VARS.BAZ : None} )
            observed[value] += 1
        self.assertGreater(observed['hello'], 1500, self.seed_msg)
        self.assertLess(observed['hello'], 2500, self.seed_msg)
        self.assertGreater(observed['there'], 500, self.seed_msg)
        self.assertLess(observed['there'], 1500, self.seed_msg)

        # Test FOO : True, BAR : False  
        observed = {'hello': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : True,
                                    VARS.BAR : False,
                                    VARS.BAZ : 'Hi, Oliver'} )
            observed[value] += 1
        self.assertGreater(observed['hello'], 500, self.seed_msg)
        self.assertLess(observed['hello'], 1500, self.seed_msg)
        self.assertGreater(observed['there'], 1500, self.seed_msg)
        self.assertLess(observed['there'], 2500, self.seed_msg)


        # Test FOO : False, BAR : True 
        observed = {'hello': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : False,
                                    VARS.BAR : True,
                                    VARS.BAZ : 3} )
            observed[value] += 1
        self.assertEqual(observed['hello'], 3000, self.seed_msg)
        self.assertEqual(observed['there'], 0, self.seed_msg)

        # Test FOO : False, BAR : False 
        observed = {'hello': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : False,
                                    VARS.BAR : False,
                                    VARS.BAZ : [1,2,3] } )
            observed[value] += 1
        self.assertEqual(observed['hello'], 0, self.seed_msg)
        self.assertEqual(observed['there'], 3000, self.seed_msg)

    def helper_correct_distribution_weighted(self, dist):
        """
        Test template:
        
        Set up a conditonal probability, conditioned on VARS.FOO. For
        FOO equal to True, add 'hello' twice and 'there' once-- but
        add weights so they are weigthed the same. For FOO equal
        False, reverse these frequencies and wieght such that 'hello'
        gets 5/6. and 'there' gets 1/6. Then test we get roughly the
        right distributions from generate().
        """
        dist.add('hello', 1, True)
        dist.add('hello', 1, True)
        dist.add('there', 2, True)

        dist.add('hello', 10, False)
        dist.add('there', 1, False)
        dist.add('there', 1, True)

        # Test 'FOO' = True
        observed = {'hello': 0, 'there': 0}
        for i in xrange(600):
            value = dist.generate( {VARS.FOO : True} )
            observed[value] += 1
        self.assertGreater(observed['hello'], 200, self.seed_msg)
        self.assertLess(observed['hello'], 400, self.seed_msg)
        self.assertGreater(observed['there'], 200, self.seed_msg)
        self.assertLess(observed['there'], 400, self.seed_msg)

        # Test 'FOO' = False
        observed = {'hello': 0, 'there': 0}
        for i in xrange(12000):
            value = dist.generate( {VARS.FOO : False} )
            observed[value] += 1
        self.assertGreater(observed['hello'], 9000, self.seed_msg)
        self.assertLess(observed['hello'], 11000, self.seed_msg)
        self.assertGreater(observed['there'], 1000, self.seed_msg)
        self.assertLess(observed['there'], 3000, self.seed_msg)





    def helper_unseen_ind_vars(self, dist):
        """
        A test-template to ensure that conditional distributions
        act in the 'expected' way (and not throw an error) when
        asked to generate values for independent vars not
        previously seen in an add() call.
        """
        dist.add('hello', 1, True, True)
        dist.add('there', 1, True, True)

        dist.add('goodbye', 1, True, False)
        dist.add('there', 1, True, False)

        # Note that we never trained on FOO = False. 
        # What happens when we try that?
        # Should get 'hello', 'there', 'goodbye', and 'now'
        # with the same probabilities.
        observed = {'hello': 0, 'there': 0, 'goodbye': 0}
        num_samples = 10000
        for i in xrange(num_samples):
            value = dist.generate( { VARS.FOO : False,
                                     VARS.BAR : True} )
            observed[value] += 1
        for x in ['hello', 'goodbye']:
            self.assertGreater(observed[x], 
                               num_samples / 4 * .75, 
                               self.seed_msg)
            self.assertLess(observed[x], 
                            num_samples / 4 * 1.25, 
                            self.seed_msg)

        self.assertGreater(observed['there'], 
                           num_samples / 2 * .75, 
                           self.seed_msg)
        self.assertLess(observed['there'], 
                        num_samples / 2 * 1.25, 
                        self.seed_msg)


    def helper_correct_remap(self, dist):
        """
        Test template:
        
        Same as helper_correct_ind_var, but first remap()s 'hello' to 'bye'. 
        """
        dist.add('hello', 1, True, True)
        dist.add('hello', 1, True, True)
        dist.add('there', 1, True, True)

        dist.add('hello', 1, True, False)
        dist.add('there', 1, True, False)
        dist.add('there', 1, True, False)

        dist.add('hello', 1, False, True)
        dist.add('hello', 1, False, True)
        dist.add('hello', 1, False, True)

        dist.add('there', 1, False, False)
        dist.add('there', 1, False, False)
        dist.add('there', 1, False, False)
    
        dist.remap('hello', 'bye')
    
       # Test FOO : True, BAR : True 
        observed = {'bye': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( { VARS.FOO : True,
                                     VARS.BAR : True,
                                     VARS.BAZ : None} )
            observed[value] += 1
        self.assertGreater(observed['bye'], 1500, self.seed_msg)
        self.assertLess(observed['bye'], 2500, self.seed_msg)
        self.assertGreater(observed['there'], 500, self.seed_msg)
        self.assertLess(observed['there'], 1500, self.seed_msg)

        # Test FOO : True, BAR : False  
        observed = {'bye': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : True,
                                    VARS.BAR : False,
                                    VARS.BAZ : 'Hi, Oliver'} )
            observed[value] += 1
        self.assertGreater(observed['bye'], 500, self.seed_msg)
        self.assertLess(observed['bye'], 1500, self.seed_msg)
        self.assertGreater(observed['there'], 1500, self.seed_msg)
        self.assertLess(observed['there'], 2500, self.seed_msg)


        # Test FOO : False, BAR : True 
        observed = {'bye': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : False,
                                    VARS.BAR : True,
                                    VARS.BAZ : 3} )
            observed[value] += 1
        self.assertEqual(observed['bye'], 3000, self.seed_msg)
        self.assertEqual(observed['there'], 0, self.seed_msg)

        # Test FOO : False, BAR : False 
        observed = {'bye': 0, 'there': 0}
        for i in xrange(3000):
            value = dist.generate( {VARS.FOO : False,
                                    VARS.BAR : False,
                                    VARS.BAZ : [1,2,3] } )
            observed[value] += 1
        self.assertEqual(observed['bye'], 0, self.seed_msg)
        self.assertEqual(observed['there'], 3000, self.seed_msg)



    def helper_support(self, dist):
        dist.add('hello', 1, True, True)
        dist.add('there', 1, True, False)
        dist.add('foo', 1, False, True)
        dist.add('bar', 1, False, False)

        expected = set(['hello', 'there', 'foo', 'bar'])
        actual = dist.support()
        self.assertSetEqual(actual, expected, self.seed_msg)





    def test_compact_distribution_unweighted(self):
        """
        Run the helper_correct_distribution_unweighted template
        on a CompactConditionalDistribution.
        """
        dist = self.compact_dist
        self.helper_correct_distribution_unweighted(dist)


    def test_simple_distribution_unweighted(self):
        """
        Run the helper_correct_distribution_unweighted template
        on a SimpleConditionalDistribution.
        """
        dist = self.simple_dist
        self.helper_correct_distribution_unweighted(dist)


    def test_compact_distribution_weighted(self):
        """
        Run the helper_correct_distribution_weighted template
        on a CompactConditionalDistribution.
        """
        dist = self.compact_dist
        self.helper_correct_distribution_weighted(dist)


    def test_simple_distribution_weighted(self):
        """
        Run the helper_correct_distribution_weighted template
        on a SimpleConditionalDistribution.
        """
        dist = self.simple_dist
        self.helper_correct_distribution_weighted(dist)


    def test_compact_distribution_ind_vars(self):
        """
        Run the helper_correct_ind_vars template on a
        CompactConditionalDistribution.
        """
        dist = self.compact_dist_2d
        self.helper_correct_ind_vars(dist)


    def test_simple_distribution_ind_vars(self):
        """
        Run the helper_correct_ind_vars template on a
        SimpleConditionalDistribution.
        """
        dist = self.simple_dist_2d
        self.helper_correct_ind_vars(dist)

    def test_compact_distribution_remap(self):
        """
        Run the helper_correct_remap template on a
        CompactConditionalDistribution.
        """
        dist = self.compact_dist_2d
        self.helper_correct_remap(dist)


    def test_simple_distribution_remap(self):
        """
        Run the helper_correct_remap template on a
        SimpleConditionalDistribution.
        """
        dist = self.simple_dist_2d
        self.helper_correct_remap(dist)

    def test_compact_distribution_unseen_ind_vars(self):
        """
        Run the helper_unseen_ind_vars template on a
        CompactConditionalDistribution.
        """
        dist = self.compact_dist_2d
        self.helper_unseen_ind_vars(dist)


    def test_simple_distribution_unseen_ind_vars(self):
        """
        Run the helper_unseen_ind_vars template on a
        SimpleConditionalDistribution.
        """
        dist = self.simple_dist_2d
        self.helper_unseen_ind_vars(dist)

    def test_compact_distribution_support(self):
        """
        Run the helper_support template on a
        CompactConditionalDistribution.
        """
        dist = self.compact_dist_2d
        self.helper_support(dist)


    def test_simple_distribution_support(self):
        """
        Run the helper_support template on a
        SimpleConditionalDistribution.
        """
        dist = self.simple_dist_2d
        self.helper_support(dist)

