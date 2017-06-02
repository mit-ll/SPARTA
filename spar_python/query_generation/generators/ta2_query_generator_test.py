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
import spar_python.query_generation.generators.ta2_query_generator as tqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.base_distributions \
    as base_distribution
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import StringIO as stringio
import spar_python.data_generation.learn_distributions as learn_distributions
import logging
import itertools

class AndTA2QueryGeneratorTest(unittest.TestCase):
    
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
                  sv.VARS.AGE,
                  sv.VARS.DOB,
                  sv.VARS.LAST_UPDATED,
                  sv.VARS.CITIZENSHIP, 
                  sv.VARS.RACE,
                  sv.VARS.STATE,
                  sv.VARS.ZIP_CODE]
        dists1 = [self.dist_holder.dist_dict[sv.VARS.ZIP_CODE],
                  self.dist_holder.dist_dict[sv.VARS.CITIZENSHIP]]
        dists2 = [self.dist_holder.dist_dict[sv.VARS.ZIP_CODE],
                  self.dist_holder.dist_dict[sv.VARS.LAST_UPDATED]]
        dists3 = [self.dist_holder.dist_dict[sv.VARS.CITIZENSHIP],
                  self.dist_holder.dist_dict[sv.VARS.ZIP_CODE]]
        
        other_fields = ['no_queries','r_lower','r_upper','range']
        other_cols1 = [[5, 10, 100, 'none'],[5,1,10, 'none']]
        other_cols2 = [[5, 10, 100, 'less'],[5,10,100, 'greater']]
        other_cols3 = [[5, 10, 100, 'range']]
        self.generator1 = tqg.AndTA2QueryGenerator("P1", 'ta2', ["LL"], dists1,
                                                   [sv.VARS.ZIP_CODE,sv.VARS.CITIZENSHIP], 1000,100,
                                                    other_fields, other_cols1)
        self.generator2 = tqg.AndTA2QueryGenerator("P1", 'ta2', ["LL"], dists2,
                                                [sv.VARS.ZIP_CODE, sv.VARS.LAST_UPDATED], 1000,100,
                                                other_fields, other_cols2)
        self.generator3 = tqg.AndTA2QueryGenerator("P1", 'ta2', ["LL"], dists3,
                                                [sv.VARS.CITIZENSHIP, sv.VARS.ZIP_CODE], 1000,100,
                                                other_fields, other_cols3)
        
    
    def testGenerateQueryNotRange(self):
        """
        Tests and ta2 query generator against a 'db' to make sure it is 
        generating the right queries does not include a fishing term
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
        query_batches = self.generator1.produce_query_batches()
        query_value_sets = []
        for query_batch in query_batches:
            queries = query_batch.produce_queries()
            for query in queries:
                for (a, b) in itertools.permutations(range(0,3), 2):       
                        query_value_sets.append({ 
                         'first_clause' : query['sub_queries'][0][a][qs.QRY_VALUE],
                         'first_clause_field' : query['sub_queries'][0][a][qs.QRY_FIELD],
                         'second_clause' : query['sub_queries'][1][b][qs.QRY_VALUE],
                         'second_clause_field' : query['sub_queries'][1][b][qs.QRY_FIELD],
                         'r_lower' : query['r_lower'],
                         'r_upper' : query['r_upper'],
                         'ftm_lower' : query['ftm_lower'],
                         'ftm_upper' : query['ftm_upper']}) 
        #check to see right number of queries generated
        self.assertEqual(len(query_value_sets), 120, self.seed_msg)
    
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        working_queries = 0
        non_working_queries = []
        for q in query_value_sets:
            one_var = sv.sql_name_to_enum(q['first_clause_field'])
            two_var = sv.sql_name_to_enum(q['second_clause_field'])
            ftm_match = len([x for x in rows if sv.VAR_CONVERTERS[one_var].to_agg_fmt(x[sv.sql_name_to_enum(
                                                    q['first_clause_field'])]) == q['first_clause']])
            count_match = len([x for x in rows if sv.VAR_CONVERTERS[one_var].to_agg_fmt(x[sv.sql_name_to_enum(
                                                    q['first_clause_field'])]) == q['first_clause'] 
                                              and sv.VAR_CONVERTERS[two_var].to_agg_fmt(x[sv.sql_name_to_enum(
                                                    q['second_clause_field'])]) == q['second_clause']])
            msg = 'Query was\n'\
                  'where: %s=%s AND %s=%s\n'\
                  'ftm_lower: %d\n'\
                  'ftm_lower: %d\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'ftm_match: %d\n'\
                  'count_match: %d\n'\
                  '\n' % (q['first_clause_field'], q['first_clause'],
                                         q['second_clause_field'], q['second_clause'],
                                         q['ftm_lower'], q['ftm_upper'], q['r_lower'],
                                         q['r_upper'], ftm_match,count_match)
            if count_match <= q[qs.QRY_URSS]*2 and count_match >= q[qs.QRY_LRSS]/2 and\
               ftm_match <= q['ftm_upper']*2 and ftm_match >= q['ftm_lower']/2:
                    working_queries+=1
            else:
                non_working_queries.append(msg)
        fail_msg = ''
        for msg in non_working_queries[:3]:
            fail_msg += msg      
        self.assertGreaterEqual(working_queries, 10, fail_msg)
        
    def testGenerateQueryThanRanges(self):
        """
        Tests and ta2 query generator against a 'db' to make sure it is 
        generating the right queries does not include a fishing term
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
        query_batches = self.generator2.produce_query_batches()
        query_value_sets = []
        for query_batch in query_batches:
            queries = query_batch.produce_queries()
            for query in queries:                    
                for (a, b) in itertools.permutations(range(0,3), 2):                   
                        query_value_sets.append({ 
                         'first_clause' : query['sub_queries'][0][a][qs.QRY_VALUE],
                         'first_clause_field' : query['sub_queries'][0][a][qs.QRY_FIELD],
                         'second_clause' : query['sub_queries'][0][b][qs.QRY_VALUE],
                         'second_clause_field' : query['sub_queries'][0][b][qs.QRY_FIELD],
                         'r_lower' : query['r_lower'],
                         'r_upper' : query['r_upper'],
                         'range_type' : query[qs.QRY_SUBCAT]}) 
        #check to see right number of queries generated
        self.assertEqual(len(query_value_sets), 120, self.seed_msg)
    
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        working_queries = 0
        non_working_queries = []
        for q in query_value_sets:
            one_var = sv.sql_name_to_enum(q['first_clause_field'])
            two_var = sv.sql_name_to_enum(q['second_clause_field'])
            if q['range_type'] == 'less':
                op = '<='
                comp = lambda x, y: x <= y
            else:
                op = '>='
                comp = lambda x, y: x >= y
            count_match = len([x for x in rows if sv.VAR_CONVERTERS[one_var].to_agg_fmt(x[sv.sql_name_to_enum(
                                                    q['first_clause_field'])]) == q['first_clause'] 
                                              and comp(sv.VAR_CONVERTERS[two_var].to_agg_fmt(x[sv.sql_name_to_enum(
                                                       q['second_clause_field'])]), 
                                                       q['second_clause'])])
            msg = 'Query was\n'\
                  'where: %s=%s AND %s%s%s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'count_match: %d\n'\
                  '\n' % (q['first_clause_field'], q['first_clause'],
                                         q['second_clause_field'], op, q['second_clause'],
                                         q['r_lower'],
                                         q['r_upper'],count_match)
            if count_match <= q[qs.QRY_URSS]*2 and count_match >= q[qs.QRY_LRSS]/2:
                    working_queries+=1
            else:
                non_working_queries.append(msg)
        fail_msg = ''
        for msg in non_working_queries[:3]:
            fail_msg += msg      
        self.assertGreaterEqual(working_queries, 10, fail_msg)
        
    def testGenerateQueryRanges(self):
        """
        Tests and ta2 query generator against a 'db' to make sure it is 
        generating the right queries does not include a fishing term
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
        query_batches = self.generator3.produce_query_batches()
        query_value_sets = []
        for query_batch in query_batches:
            queries = query_batch.produce_queries()
            for query in queries:
                query['sub_queries'] = list(itertools.chain.from_iterable(query['sub_queries']))
                for (a, b) in itertools.permutations(range(0,6), 2):
                    try:
                        value = query['sub_queries'][a][qs.QRY_VALUE]
                        lower = query['sub_queries'][b][qs.QRY_LBOUND]
                        upper = query['sub_queries'][b][qs.QRY_UBOUND]
                    except:
                        continue                   
                    query_value_sets.append({ 
                     'first_clause' : value,
                     'first_clause_field' : query['sub_queries'][a][qs.QRY_FIELD],
                     'second_clause_lower' : lower,
                     'second_clause_upper' : upper,
                     'second_clause_field' : query['sub_queries'][b][qs.QRY_FIELD],
                     'r_lower' : query['r_lower'],
                     'r_upper' : query['r_upper'],
                     'range_type' : query[qs.QRY_SUBCAT]}) 
        #check to see right number of queries generated
        self.assertEqual(len(query_value_sets), 90, self.seed_msg)
    
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        working_queries = 0
        non_working_queries = []
        for q in query_value_sets:
            one_var = sv.sql_name_to_enum(q['first_clause_field'])
            two_var = sv.sql_name_to_enum(q['second_clause_field'])
            comp = lambda x,y,z : x >= y and x <= z
            count_match = len([x for x in rows if sv.VAR_CONVERTERS[one_var].to_agg_fmt(x[sv.sql_name_to_enum(
                                                    q['first_clause_field'])]) == q['first_clause'].upper() 
                                              and comp(sv.VAR_CONVERTERS[two_var].to_agg_fmt(x[sv.sql_name_to_enum(
                                                       q['second_clause_field'])]), 
                                                       q['second_clause_lower'].upper(),
                                                       q['second_clause_upper'].upper())])
            msg = 'Query was\n'\
                  'where: %s=%s AND %s BETWEEN %s AND %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'count_match: %d\n'\
                  '\n' % (q['first_clause_field'], q['first_clause'],
                                         q['second_clause_field'], q['second_clause_lower'],
                                         q['second_clause_upper'], q['r_lower'],
                                         q['r_upper'],count_match)
            if count_match <= q[qs.QRY_URSS]*2 and count_match >= q[qs.QRY_LRSS]/2:
                    working_queries+=1
            else:
                non_working_queries.append(msg)
        fail_msg = ''
        for msg in non_working_queries[:3]:
            fail_msg += msg      
        self.assertGreaterEqual(working_queries, 10, fail_msg)
        
        
        