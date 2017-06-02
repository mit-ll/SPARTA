# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        unit tests for RandomInt 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Nov 2011   omd            Original Version
# *****************************************************************
from __future__ import division
import spar_random
import unittest
import time
import collections

# TODO: This should really test that this works with numpy and without by
# forcing the import of numpy to fail but I can't figure out how to cause the
# import to fail.
class SparRandomTest(unittest.TestCase):

    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)


    def test_seed(self):
        list_len = 200
        first_list = [spar_random.randint(1,10) for _ in xrange(list_len)]
        
        # Now, re-seed. Do we get the same list again?
        spar_random.seed(self.seed)
        second_list = [spar_random.randint(1,10) for _ in xrange(list_len)]
        
        self.assertListEqual(first_list, second_list, self.seed_msg)
    
    def test_randint(self):
        """This tests that the randint function does indeed generate uniformly
        distributed random numbers."""
        observed = {x: 0 for x in xrange(2, 13)}
        # Generate 1000 random numbers
        for i in xrange(10000):
            num = spar_random.randint(2, 12)
            observed[num] += 1

        # Make sure that each number was observed. If things are roughly
        # uniformly distribuited each number should have been observed roughly
        # 1000 times.
        for n in xrange(2, 13):
            self.assertGreater(observed[num], 800, self.seed_msg)
            self.assertLess(observed[num], 1200, self.seed_msg)

    def test_choice(self):
        """ 
        This tests that the choice() function is roughly correct.
        """
        seq = [1,2,3]
        observed = {}
        for i in seq:
            observed[i] = 0
        for i in xrange(1000):
            x = spar_random.choice(seq)
            observed[x] += 1
    
        for i in seq:
            self.assertGreater(observed[i], 250, self.seed_msg)
            self.assertLess(observed[i], 400, self.seed_msg)
        

    def test_gauss(self):
        mu = 10
        sigma = 5
        num_above = 0
        num_below = 0
        in_std_dev = 0
        outside_std_dev = 0

        iterations = 1000

        
        for _ in xrange(iterations):
            x = spar_random.gauss(mu, sigma)

            # test mu
            if x >= mu:
                num_above += 1
            else:
                num_below += 1
                
            # test sigma
            
            if abs(x - mu) <= sigma:
                in_std_dev += 1
            else:
                outside_std_dev += 1
                
        ratio1 = float(num_above) / float(iterations)
        ratio2 = float(num_below) / float(iterations)
        
        self.assertGreater(ratio1, 0.45, self.seed_msg)
        self.assertGreater(ratio2, 0.45, self.seed_msg)        
        self.assertLess(ratio1, 0.55, self.seed_msg)
        self.assertLess(ratio2, 0.55, self.seed_msg)

        ratio3 = float(in_std_dev) / float(iterations)
        ratio4 = float(outside_std_dev) / float(iterations)

        self.assertGreater(ratio3, 0.63, self.seed_msg)
        self.assertGreater(ratio4, 0.27, self.seed_msg)
        

    def test_sample(self):
        pop_size = 10
        sample_size = 2
        num_possible_samples = 10 * (10 - 1)
        population = range(pop_size)
        counts = collections.Counter()
        
        num_iterations = num_possible_samples * 1000
        for _ in xrange(num_iterations):
        
            sample = spar_random.sample(population, sample_size)
        
            self.assertEqual(len(sample), sample_size)
            sample_set = set(sample)
            self.assertEqual(len(sample_set), sample_size)
            
            for s in sample:
                self.assertIn(s, population)

            counts[tuple(sample)] += 1

        self.assertEqual(len(counts), num_possible_samples)

        x = 0
        for i in range(pop_size):
            for j in range(pop_size):
                if i != j:
                    self.assertIn( (i,j), counts)
                    x += 1
        self.assertEqual(x, num_possible_samples)

        
        for sample in counts:
            expected_proportion = num_possible_samples * 10 / num_iterations
            proportion = counts[sample] / num_iterations
            self.assertGreater(proportion,  expected_proportion * 0.5)
            self.assertLess(proportion, expected_proportion * 1.5)

    def test_randbit(self):
        iterations = 1000
        num_1s = 0
        num_0s = 0
        
        for _ in xrange(iterations):
            b = spar_random.randbit()
            self.assertIn(b, [0,1], self.seed_msg)
            
            if b:
                num_1s += 1
            else:
                num_0s += 1
                
        ratio1 = float(num_1s) / float(iterations)
        ratio0 = float(num_0s) / float(iterations)
        
        self.assertGreater(ratio1, 0.4, self.seed_msg)
        self.assertGreater(ratio0, 0.4, self.seed_msg)

