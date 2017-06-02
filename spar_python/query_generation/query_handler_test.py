# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for query_handler_test
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  7 August 2012  ATLH            Original version
# *****************************************************************

from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import unittest
import time
import spar_python.common.enum as enum
import spar_python.query_generation.generators.equality_query_generator as eqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.base_distributions \
    as base_distribution
import spar_python.query_generation.query_handler as handler
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import logging 

VARS = enum.Enum('dist1')

class QueryHandlerTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.dummy_logger = logging.getLogger('dummy')
        
        #set up intitialization values 
        self._dist1 = base_distribution.CompactIndependentDistribution()
        self._dist1.add('hello', 1)
        self._dist1.add('there', 999)
        self._dist2 = base_distribution.SimpleConditionalDistribution(VARS.dist1)
        self._dist2.add('hello', 1, 'hello')
        self._dist2.add('hi', 300, 'there')
        self._dist2.add('there', 400, 'there')
        self._dist2.add('person', 300, 'there')
        fields = [sv.VARS.FIRST_NAME, sv.VARS.LAST_NAME]
        dists = [self._dist1,self._dist2]
        other_fields = ['no_queries', 'r_lower', 'r_upper']
        other_cols = [[5, 1, 7]]
        query_object = [eqg.EqualityQueryGenerator('EQ','eq', ["LL"],[self._dist1], [sv.VARS.FIRST_NAME],
                                                    100,10000,other_fields, other_cols),
                        eqg.EqualityQueryGenerator('EQ','eq', ["LL"], [self._dist2], [sv.VARS.LAST_NAME], 10000,
                                                        100,other_fields, other_cols),
                        eqg.EqualityQueryGenerator('EQ','eq', ["LL"], dists, fields, 10000,
                                                        100,other_fields, other_cols)]
        self.handler = handler.QueryHandler(query_object)
   
    def testRun(self):
        """
        Tests the run functionality of the query handler
        """   
         
        queries_bobs = self.handler.run(self.dummy_logger)
        queries = []
        for bobs in queries_bobs:
            queries+=bobs.produce_queries()
        self.assertGreaterEqual(len(queries),2,self.seed_msg)
        counts = {'': 0}
        for q in queries:
           counts[q[qs.QRY_SUBCAT]]+=1
        
        self.assertGreaterEqual(counts[''], 2, self.seed_msg)


       
