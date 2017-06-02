# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for equality_query_generator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  6 August 2012  ATLH            Original version
# *****************************************************************

from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import unittest
import time
import foo_range_query_generator as frqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.bespoke_distributions \
    as bespoke_distribution
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
    
class FooRangeQueryGeneratorTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        #set up intitialization values 
        sub_cat = 'foo-range'
        self._foo_dist = bespoke_distribution.FooDistribution()
        fields = [sv.sql_name_to_enum('foo')]
        dists = [self._foo_dist]
        other_fields = ['no_queries', 'r_lower', 'r_upper','r_exp_lower','r_exp_upper','type']
        other_cols = [[2, 1, 100, 21, 21, 'range'], [2,1, 100,32, 32,'range'],
                      [2, 1, 200, 21, 21,'greater'],[2,1, 200,25, 25,'greater']]
        self.generator = frqg.FooRangeQueryGenerator('P2',sub_cat, ["LL"],dists, fields, 50000,
                                                     100,other_fields, other_cols)
        
    @unittest.skip("Sporadically fails, not sure why")
    def testGenerateQuery(self):
        
        """
        Tests equality query generator against a 'db' to make sure it is 
        generating the right queries
        """
        #generate a 'db' to test against
        foos = [self._foo_dist.generate() for _ in xrange(50000)]

        #generate queries
        query_batches = self.generator.produce_query_batches()
        queries = []
        for query_batch in query_batches:
            queries += query_batch.produce_queries()
        
        #check to see right number of queries generated
        self.assertEqual(len(queries), 16, self.seed_msg)
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        foo_range = 0
        foo_greater = 0
        for q in queries:
            if q[qs.QRY_TYPE] == 'range':
                min = q[qs.QRY_LBOUND]
                maxim = q[qs.QRY_UBOUND]
                x = lambda y: y >= min and y <= maxim
                foo_range +=1
            elif q[qs.QRY_TYPE] == 'greater':
                min = q[qs.QRY_LBOUND]
                maxim = q[qs.QRY_UBOUND]
                x = lambda y: y >= min
                foo_greater +=1
                
            count_match = len([foo for foo in foos if x(foo)])
            msg = 'Query %d was: \n' \
                  'sub_cat: %s\n'\
                  'field: %s\n'\
                  'type: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'range_exp: %d\n'\
                  'value: %d %d\n' % (q[qs.QRY_QID], q[qs.QRY_SUBCAT], 
                                      q[qs.QRY_FIELD], q[qs.QRY_TYPE], 
                                      q[qs.QRY_LRSS], q[qs.QRY_URSS], 
                                      q[qs.QRY_RANGEEXP], min, maxim)
            self.assertLessEqual(count_match, q[qs.QRY_URSS]*2, msg)
            self.assertGreaterEqual(count_match, q[qs.QRY_LRSS]/2, msg)
        #check to see each field had the correct number of queries
        self.assertEqual(foo_range, 8, self.seed_msg)
        self.assertEqual(foo_greater, 8, self.seed_msg)
