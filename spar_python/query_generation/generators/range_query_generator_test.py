# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for range_query_generator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  31 October 2013  ATLH            Original version
# *****************************************************************

from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import unittest
import time
import range_query_generator as rqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.bespoke_distributions \
    as bespoke_distribution
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import logging
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import StringIO as stringio
import spar_python.data_generation.learn_distributions as learn_distributions

class FooRangeQueryGeneratorTest(unittest.TestCase):
    
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
                  sv.VARS.CITIZENSHIP,
                  sv.VARS.RACE,
                  sv.VARS.STATE,
                  sv.VARS.ZIP_CODE,
                  sv.VARS.AGE,
                  sv.VARS.DOB, 
                  sv.VARS.SSN,
                  sv.VARS.LAST_UPDATED]
        
        fields = [sv.VARS.FIRST_NAME,
                  sv.VARS.ZIP_CODE, 
                  sv.VARS.SSN,
                  sv.VARS.LAST_UPDATED]
        dist_dict = self.dist_holder.dist_dict
        dists = [dist_dict[sv.VARS.FIRST_NAME], dist_dict[sv.VARS.ZIP_CODE], 
                 dist_dict[sv.VARS.SSN], dist_dict[sv.VARS.LAST_UPDATED]]
        other_fields = ['no_queries','r_lower','r_upper','type']
        other_cols = [[3, 10, 100,'less'],[3,10,100,'range'],[3,10,100,'greater']]
        self.generator = rqg.RangeQueryGenerator("P2", 'range', ["LL"],dists,fields, 1000, 100,
                                                    other_fields, other_cols)
        
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
                if var != sv.VARS.DOB:
                    row_dict[var] = sv.VAR_CONVERTERS[var].to_csv(v)
                else:
                    row_dict[var] = v
            rows.append(row_dict)

        #generate queries
        query_batches = self.generator.produce_query_batches()
        queries = []
        for query_batch in query_batches:
            queries += query_batch.produce_queries()
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        count = 0
        fail_msg = ''
        for q in queries:
            if count % 3 == 0:
                fail_count = 0
            count += 1
            if q[qs.QRY_SUBCAT] == 'range':
                minin = q[qs.QRY_LBOUND]
                max = q[qs.QRY_UBOUND]
                val = (minin, max)
                x = lambda y: y >= minin and y <= max
            elif q[qs.QRY_SUBCAT] == 'greater':
                val = q[qs.QRY_VALUE]
                x = lambda y: y >= val
                val = str(val)
            else:
                val = q[qs.QRY_VALUE]
                x = lambda y: y <= val
                val = str(val)
            count_match = len([row for row in rows if x(row[sv.sql_name_to_enum(q[qs.QRY_FIELD])])])
            msg = 'Query %d was: \n' \
                  'sub_cat: %s\n'\
                  'field: %s\n'\
                  'type: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'count: %d\n'\
                  'value: %s\n' % (q[qs.QRY_QID], q[qs.QRY_SUBCAT], 
                                      q[qs.QRY_FIELD], q[qs.QRY_SUBCAT], 
                                      q[qs.QRY_LRSS], q[qs.QRY_URSS], 
                                      count, val)
            if count_match > q[qs.QRY_URSS]*10 or count_match < q[qs.QRY_LRSS]/10:
                fail_count += 1
                fail_msg = msg
        self.assertLessEqual(fail_count, 6, fail_msg) 

