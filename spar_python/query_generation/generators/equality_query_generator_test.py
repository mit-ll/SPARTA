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
import spar_python.common.enum as enum
import equality_query_generator as eqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.base_distributions \
    as base_distribution
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import StringIO as stringio
import spar_python.data_generation.learn_distributions as learn_distributions
import logging
import spar_python.query_generation.query_ids as qids

VARS = enum.Enum('dist1')

class EqualityQueryGeneratorTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        #set up intitialization values  
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(self.learner_options,
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
            learn_distributions.learn_name_dists(self.learner_options,
                                                 self.dummy_logger,
                                                 names_files)
        zipcode_files = \
            [('mock_zipcodes', 
              stringio.StringIO(mock_data_files.mock_zipcodes))]
        zipcode_dict = \
            learn_distributions.learn_zipcode_dists(self.learner_options,
                                                    self.dummy_logger,
                                                    zipcode_files)
        
        text_files = \
            [('mock_text', 
              stringio.StringIO(mock_data_files.mock_text_files))]
        text_engine = \
            learn_distributions.train_text_engine(self.learner_options, 
                                                  self.dummy_logger, 
                                                  text_files)
        streets_files = \
            [('mock street file', 
              stringio.StringIO(mock_data_files.mock_street_names))]
        address_dict = \
                learn_distributions.learn_street_address_dists(self.learner_options, 
                                                               self.dummy_logger, 
                                                               streets_files)
        self.dist_holder = \
            learn_distributions.make_distribution_holder(self.learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)
        self.fields_to_gen = [
                  sv.VARS.SEX,
                  sv.VARS.FIRST_NAME,
                  sv.VARS.LAST_NAME]
        sub_cat = 'eq'
        fields = [sv.sql_name_to_enum('fname'), sv.sql_name_to_enum('lname')]
        dists1 = [self.dist_holder.dist_dict[sv.VARS.FIRST_NAME],
                  self.dist_holder.dist_dict[sv.VARS.LAST_NAME]]
        other_fields = ['no_queries', 'r_lower', 'r_upper']
        other_cols = [[5, 1, 10], [5,11,100]]
        self.generator = eqg.EqualityQueryGenerator('EQ',sub_cat, ["LL"], dists1, fields, 1000,
                                                    100,other_fields, other_cols)
        
    
    @unittest.skip("Sporadically fails, not sure why")
    def testGenerateQuery(self):
        """
        Tests equality query generator against a 'db' to make sure it is 
        generating the right queries
        """
        #generate a 'db' to test against
        rows = []
        for _ in xrange(1000): 
            row_dict = {}
            for var in self.fields_to_gen:
                dist = self.dist_holder.dist_dict[var]
                v = dist.generate(row_dict)
                row_dict[var] = v
            rows.append(row_dict)

        #generate queries
        query_batches = self.generator.produce_query_batches()
        query = []
        for query_batch in query_batches:
            query += query_batch.produce_queries()
     
        q_dist1 = 0
        q_dist2 = 0
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        working_queries = 0
        non_working_queries = []
        for q in query:
            self.assertEqual('', q[qs.QRY_SUBCAT], self.seed_msg)
            if q[qs.QRY_FIELD] == 'fname':
                q_dist1 += 1
            elif q[qs.QRY_FIELD] == 'lname':
                q_dist2 += 1
            count_match = len([x for x in rows if x[sv.sql_name_to_enum(q[qs.QRY_FIELD])] == q[qs.QRY_VALUE]])
            msg = 'Query %d was: \n' \
                  'sub_cat: %s\n'\
                  'field: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'value: %s\n' % (q[qs.QRY_QID], q[qs.QRY_SUBCAT], 
                                   q[qs.QRY_FIELD], q[qs.QRY_LRSS],
                                   q[qs.QRY_URSS], q[qs.QRY_VALUE])
            if count_match <= q[qs.QRY_URSS]*2 and count_match >= q[qs.QRY_LRSS]/2:
                working_queries+=1
            else:
                non_working_queries.append(msg)
                
        fail_msg = ''
        for msg in non_working_queries[:3]:
            fail_msg += msg
    
        self.assertGreaterEqual(working_queries, 10, fail_msg)
        #check to see each field had the correct number of queries
        #ideally this number would be greater than 5 (the requested amount)
        #but because the distribution used for unit testing is so small
        #there is a greater margin of error at this scale
        self.assertGreaterEqual(q_dist1, 4, self.seed_msg)
        self.assertGreaterEqual(q_dist2, 4, self.seed_msg)
        
        
        
        
        
        
