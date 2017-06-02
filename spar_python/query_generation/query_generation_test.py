# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Unit tests for query_generation.py
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 August 2012  ATLH            Original file
# *****************************************************************


import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import unittest
import time
import spar_python.common.distributions.distribution_holder as dh
import spar_python.query_generation.query_generation as qg
import spar_python.common.enum as enum
import spar_python.query_generation.query_ids as qids
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.base_distributions \
    as base_distribution
import StringIO
import spar_python.query_generation.query_schema as qs
import logging

VARS = enum.Enum('FIRST_NAME')

class QueryGeneratorTest(unittest.TestCase):
    
    def setUp(self):
        
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.dummy_logger = logging.getLogger('dummy')
        
        #distribution holder
        dist1 = base_distribution.CompactIndependentDistribution()
        dist1.add('hello', 1)
        dist1.add('there', 99)
        vars = [VARS.FIRST_NAME]
        dists = [dist1]
        dist_dict = dict(zip(vars, dists))
        self._holder = dh.DistributionHolder(vars,
                                             ['fname'],
                                             dist_dict)

        self._file_name = StringIO.StringIO('cat,sub_cat,perf,fields,\"[\'no_queries' \
                          '\',\'r_lower\',\'r_upper\']\"\nEQ,eq,"[\'LL\']","[\'fname\']","[10, 1, 100]\"')
                                
        self._db_size = 1000

    def testQueryGeneration(self):
        qids.reset_full_where()
        query_bobs = qg.query_generation(self._file_name, self.dummy_logger,
                                      self._holder, self._db_size,100,self.seed)
        
        queries = []
        for bobs in query_bobs:
            queries += bobs.produce_queries()
        values = ['HELLO', 'THERE']
        self.assertGreaterEqual(len(queries), 1, self.seed_msg)
        for q in queries:
            self.assertEqual(q[qs.QRY_SUBCAT], '', self.seed_msg)
            self.assertEqual(q[qs.QRY_FIELD], 'fname', self.seed_msg)
            self.assertEqual(q[qs.QRY_LRSS], 1, self.seed_msg)
            self.assertEqual(q[qs.QRY_URSS], 100, self.seed_msg)
            self.assertTrue(q[qs.QRY_VALUE] in values, self.seed_msg)
        
