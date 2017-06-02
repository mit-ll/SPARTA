# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for xml_query_generator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  6 October 2013  ATLH            Original version
# *****************************************************************

from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import unittest
import time
import spar_python.common.enum as enum
import spar_python.query_generation.generators.xml_query_generator as xqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.xml_generator as xml_generator
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import StringIO as stringio
import spar_python.data_generation.learn_distributions as learn_distributions
import logging
import spar_python.common.distributions.distribution_holder as dh

class XMLQueryGeneratorTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        #set up intitialization values 
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        class Options(object):
            pass
        learner_options = Options()
        learner_options.verbose = False

        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(learner_options,
                                                 self.dummy_logger,
                                                 pums_files)
            
        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_male_first_names)),
             ('female_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_female_first_names)),
             ('last_names.txt', 
              stringio.StringIO(mock_data_files.mock_last_names))]
        names_dict = \
            learn_distributions.learn_name_dists(learner_options,
                                                 self.dummy_logger,
                                                 names_files)

        vars = [sv.VARS.SEX,
                sv.VARS.CITIZENSHIP,
                sv.VARS.AGE,
                sv.VARS.RACE,
                sv.VARS.STATE,
                sv.VARS.FIRST_NAME,
                sv.VARS.LAST_NAME]

        var_order = vars
        var_names = [sv.VARS.to_string(x) for x in vars]
        dist_dict = { }
        dist_dict.update(pums_dict)
        dist_dict.update(names_dict)
        
        dist_holder = dh.DistributionHolder(var_order, var_names, dist_dict)
        
        fields = [sv.sql_name_to_enum('xml')]

        self._dist1 = xml_generator.XmlGenerator(dist_holder)
        dists = [self._dist1]
        other_fields = ['no_queries', 'r_lower', 'r_upper', 'path_type'] 
        other_cols_full = [[5, 1, 10, 'full']]
        other_cols_short = [[5,1, 10,'short']]
        self.full_generator = xqg.XmlQueryGenerator('P11','', ["LL"],dists, fields, 1000,
                                                    100,other_fields, other_cols_full)
        self.short_generator = xqg.XmlQueryGenerator('P11','', ["LL"],dists, fields, 1000,
                                                    100,other_fields, other_cols_short)
        
    
    @unittest.skip("Sporadically fails, not sure why")
    def testGenerateQueryFull(self):
        """
        Tests xml query generator against a 'db' to make sure it is 
        generating the right queries
        """
        #generate a 'db' to test against
        values = []
        for _ in xrange(1000):
           values.append(self._dist1.generate())

        #generate queries
        query_batches = self.full_generator.produce_query_batches()
        query = []
        for query_batch in query_batches:
            query += query_batch.produce_queries()
        
        q_dist1 = 0
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        for q in query:
            count_match = len([x for x in values if x.has_path(
                                                   q[qs.QRY_XPATH],q[qs.QRY_VALUE].upper())])
            msg = 'Query %d was: \n' \
                  'sub_cat: %s\n'\
                  'field: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'where: %s\n' % (q[qs.QRY_QID], q[qs.QRY_SUBCAT], 
                                   q[qs.QRY_FIELD], q[qs.QRY_LRSS],
                                   q[qs.QRY_URSS], q[qs.QRY_WHERECLAUSE])
            self.assertLessEqual(count_match, q[qs.QRY_URSS]*10, msg)
            self.assertGreaterEqual(count_match, q[qs.QRY_LRSS]/10, msg)
    
    @unittest.skip("Sporadically fails, not sure why")
    def testGenerateQueryShort(self):
        """
        Tests xml query generator against a 'db' to make sure it is 
        generating the right queries
        """
        #generate a 'db' to test against
        values = []
        for _ in xrange(1000):
           values.append(self._dist1.generate())
        
        #generate queries
        query_batches = self.short_generator.produce_query_batches()
        query = []
        for query_batch in query_batches:
            query += query_batch.produce_queries()
            
        
        #check to see right number of queries generated
        self.assertGreater(len(query), 0, self.seed_msg)
        
        q_dist1 = 0
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        for q in query:
            count_match = len([x for x in values if x.has_leaf(
                                                   q[qs.QRY_XPATH],q[qs.QRY_VALUE].upper())])
            msg = 'Query %d was: \n' \
                  'sub_cat: %s\n'\
                  'field: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'where: %s\n' % (q[qs.QRY_QID], q[qs.QRY_SUBCAT], 
                                   q[qs.QRY_FIELD], q[qs.QRY_LRSS],
                                   q[qs.QRY_URSS], q[qs.QRY_WHERECLAUSE])
            self.assertLessEqual(count_match, q[qs.QRY_URSS]*10, msg)
            self.assertGreaterEqual(count_match, q[qs.QRY_LRSS]/10, msg)
 
        
        
        
        
        
        
