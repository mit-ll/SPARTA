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
import spar_python.query_generation.generators.compound_query_generator as aqg
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


class AndQueryGeneratorTest(unittest.TestCase):
    
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
                  sv.VARS.FOO,
                  sv.VARS.LAST_NAME,
                  sv.VARS.CITIZENSHIP,
                  sv.VARS.AGE,
                  sv.VARS.INCOME,
                  sv.VARS.RACE,
                  sv.VARS.STATE,
                  sv.VARS.WEEKS_WORKED,
                  sv.VARS.HOURS_WORKED, 
                  sv.VARS.MILITARY_SERVICE,
                  sv.VARS.MARITAL_STATUS,
                  sv.VARS.GRADE_ENROLLED,
                  sv.VARS.LANGUAGE,
                  sv.VARS.FIRST_NAME,
                  sv.VARS.ZIP_CODE,
                  sv.VARS.CITY,
                  sv.VARS.STREET_ADDRESS,
                  sv.VARS.DOB]
        other_fields = ['no_queries','r_lower','r_upper','num_clauses','tm_lower','tm_upper']
        other_cols = [[5, 10, 100,2,100,1000],[5,1,10,2,10,100]]
        self.generator = aqg.AndQueryGenerator("P1", 'and-eq', ["LL"],self.dist_holder.dist_dict.values(), 
                                               self.dist_holder.dist_dict.keys(), 1000,100,
                                                    other_fields, other_cols)
        
    
    def testGenerateQuery(self):
        """
        Tests and query generator against a 'db' to make sure it is 
        generating the right queries
        """
        #generate a 'db' to test against
        rows = []
        for _ in xrange(1000): 
            row_dict = {}
            for var in self.fields_to_gen:
                dist = self.dist_holder.dist_dict[var]
                v = dist.generate(row_dict)
                row_dict[var] = sv.VAR_CONVERTERS[var].to_agg_fmt(v)
            rows.append(row_dict)
        #generate queries
        query_batches = self.generator.produce_query_batches()
        query_value_sets = []
        for query_batch in query_batches:
            queries = query_batch.produce_queries()
            for query in queries:                  
                for (a, b) in itertools.permutations(range(6), 2):                   
                        query_value_sets.append({ 
                         'first_clause' : query['sub_queries'][0][a][qs.QRY_VALUE],
                         'first_clause_field' : query['sub_queries'][0][a][qs.QRY_FIELD],
                         'second_clause' : query['sub_queries'][0][b][qs.QRY_VALUE],
                         'second_clause_field' : query['sub_queries'][0][b][qs.QRY_FIELD],
                         'r_lower' : query['r_lower'],
                         'r_upper' : query['r_upper'],
                         'ftm_lower' : query['ftm_lower'],
                         'ftm_upper' : query['ftm_upper']}) 
        #check to see right number of queries generated
        self.assertEqual(len(query_value_sets), 600, self.seed_msg)
    
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        working_queries = 0
        non_working_queries = []
        for q in query_value_sets:
            first_field = sv.sql_name_to_enum(q['first_clause_field'])
            second_field = sv.sql_name_to_enum(q['second_clause_field'])
            ftm_match = len([x for x in rows if x[first_field] == q['first_clause']])
            count_match = len([x for x in rows if x[first_field] == q['first_clause'] 
                                              and x[second_field] == q['second_clause']])
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


class OrQueryGeneratorTest(unittest.TestCase):
    
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
                  sv.VARS.FOO,
                  sv.VARS.LAST_NAME,
                  sv.VARS.CITIZENSHIP,
                  sv.VARS.AGE,
                  sv.VARS.INCOME,
                  sv.VARS.RACE,
                  sv.VARS.STATE,
                  sv.VARS.WEEKS_WORKED,
                  sv.VARS.HOURS_WORKED, 
                  sv.VARS.MILITARY_SERVICE,
                  sv.VARS.MARITAL_STATUS,
                  sv.VARS.GRADE_ENROLLED,
                  sv.VARS.LANGUAGE,
                  sv.VARS.FIRST_NAME,
                  sv.VARS.ZIP_CODE,
                  sv.VARS.CITY,
                  sv.VARS.STREET_ADDRESS,
                  sv.VARS.DOB]
        other_fields = ['no_queries','r_lower','r_upper','num_clauses','tm_lower','tm_upper']
        other_cols = [[5, 10, 100,2,10,100],[5,1,10,2,10,100]]
        self.generator = aqg.OrQueryGenerator("P1", 'and-or', ["LL"],self.dist_holder.dist_dict.values(), 
                                               self.dist_holder.dist_dict.keys(), 1000,100,
                                                    other_fields, other_cols)
        
    
    def testGenerateQuery(self):
        """
        Tests or query generator against a 'db' to make sure it is 
        generating the right queries
        """
        #generate a 'db' to test against
        rows = []
        for _ in xrange(1000): 
            row_dict = {}
            for var in self.fields_to_gen:
                dist = self.dist_holder.dist_dict[var]
                v = dist.generate(row_dict)
                row_dict[var] = sv.VAR_CONVERTERS[var].to_agg_fmt(v)
            rows.append(row_dict)
        #generate queries
        query_batches = self.generator.produce_query_batches()
        query_value_sets = []
        for query_batch in query_batches:
            queries = query_batch.produce_queries()
            for query in queries:      
                for (a, b) in itertools.permutations(range(6), 2):                   
                        query_value_sets.append({ 
                         'first_clause' : query['sub_queries'][0][a][qs.QRY_VALUE],
                         'first_clause_field' : query['sub_queries'][0][a][qs.QRY_FIELD],
                         'second_clause' : query['sub_queries'][0][b][qs.QRY_VALUE],
                         'second_clause_field' : query['sub_queries'][0][b][qs.QRY_FIELD],
                         'r_lower' : query['r_lower'],
                         'r_upper' : query['r_upper'],
                         'stm_lower' : query['ftm_lower'],
                         'stm_upper' : query['ftm_upper']})             
        #check to see right number of queries generated
        self.assertEqual(len(query_value_sets), 600, self.seed_msg)
    
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        working_queries = 0
        distribution_ineligible = 0
        non_working_queries = []
        for q in query_value_sets:
            first_field = sv.sql_name_to_enum(q['first_clause_field'])
            second_field = sv.sql_name_to_enum(q['second_clause_field'])
            ftm_match = len([x for x in rows if x[first_field] == q['first_clause']])
            stm_match = len([x for x in rows if x[second_field] == q['second_clause']])
            total_match = ftm_match + stm_match
            count_match = len([x for x in rows if x[first_field] == q['first_clause'] 
                                              or x[second_field] == q['second_clause']])
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
                                         q['stm_lower'], q['stm_upper'], q['r_lower'],
                                         q['r_upper'], ftm_match,count_match)
            if count_match <= q[qs.QRY_URSS]*2 and count_match >= q[qs.QRY_LRSS]/2 and\
               total_match <= q['stm_upper']*2 and total_match >= q['stm_lower']/2:
                    working_queries+=1
            else:
                non_working_queries.append(msg)
        fail_msg = ''
        for msg in non_working_queries[:3]:
            fail_msg += msg      
        self.assertGreaterEqual(working_queries, 10, fail_msg)
        
class ThresholdQueryGeneratorTest(unittest.TestCase):
    
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
                  sv.VARS.FOO,
                  sv.VARS.LAST_NAME,
                  sv.VARS.CITIZENSHIP,
                  sv.VARS.AGE,
                  sv.VARS.INCOME,
                  sv.VARS.RACE,
                  sv.VARS.STATE,
                  sv.VARS.WEEKS_WORKED,
                  sv.VARS.HOURS_WORKED, 
                  sv.VARS.MILITARY_SERVICE,
                  sv.VARS.MARITAL_STATUS,
                  sv.VARS.GRADE_ENROLLED,
                  sv.VARS.LANGUAGE,
                  sv.VARS.FIRST_NAME,
                  sv.VARS.ZIP_CODE,
                  sv.VARS.CITY,
                  sv.VARS.STREET_ADDRESS,
                  sv.VARS.DOB]
        other_fields = ['no_queries','r_lower','r_upper','m','n','tm_lower','tm_upper']
        other_cols = [[5, 10, 100,2,3,1,10],[5,10,100,2,3,10,100]]
        self.generator = aqg.ThresholdQueryGenerator("P8", 'threshold', ["LL"], self.dist_holder.dist_dict.values(), 
                                               self.dist_holder.dist_dict.keys(), 1000,100,
                                                    other_fields, other_cols)
        
    
    def testGenerateQuery(self):
        """
        Tests threshold query generator against a 'db' to make sure it is 
        generating the right queries
        """
        #generate a 'db' to test against
        rows = []
        for x in xrange(1000): 
            row_dict = { sv.VARS.ID : x}
            for var in self.fields_to_gen:
                dist = self.dist_holder.dist_dict[var]
                v = dist.generate(row_dict)
                row_dict[var] = sv.VAR_CONVERTERS[var].to_agg_fmt(v)
            rows.append(row_dict)
        #generate queries
        query_batches = self.generator.produce_query_batches()
        query_value_sets = []
        for query_batch in query_batches:
            queries = query_batch.produce_queries()
            for query in queries:
                    for (a, b, c) in itertools.permutations(range(6), 3):                   
                        query_value_sets.append({ 
                         'first_clause' : query['sub_queries'][0][a][qs.QRY_VALUE],
                         'first_clause_field' : query['sub_queries'][0][a][qs.QRY_FIELD],
                         'second_clause' : query['sub_queries'][0][b][qs.QRY_VALUE],
                         'second_clause_field' : query['sub_queries'][0][b][qs.QRY_FIELD],
                         'third_clause' : query['sub_queries'][0][c][qs.QRY_VALUE],
                         'third_clause_field' : query['sub_queries'][0][c][qs.QRY_FIELD],
                         'r_lower' : query['r_lower'],
                         'r_upper' : query['r_upper'],
                         'sftm_lower' : query['ftm_lower'],
                         'sftm_upper' : query['ftm_upper']})

        #check to see right number of queries generated
        self.assertEqual(len(query_value_sets), 2400, self.seed_msg)
    
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        working_queries = 0
        non_working_queries = []
        id = sv.VARS.ID
        for q in query_value_sets:
            first_field = sv.sql_name_to_enum(q['first_clause_field'])
            second_field = sv.sql_name_to_enum(q['second_clause_field'])
            third_field = sv.sql_name_to_enum(q['third_clause_field'])
            ft = [x[id] for x in rows if x[first_field] == q['first_clause']]
            st = [x[id] for x in rows if x[second_field] == q['second_clause']]
            tt = [x[id] for x in rows if x[third_field] == q['third_clause']]
            matching_ids_set = set()
            for m_set in itertools.combinations([ft,st,tt], 2):
                matching_ids_set.update(reduce(set.intersection, [set(x) for x  
                                                                     in m_set]))
            count_match = len(matching_ids_set)     
            total_match = len(ft) + len(st)
            msg = 'Query was\n'\
                  'where: %s=%s AND %s=%s\n'\
                  'ftm_lower: %d\n'\
                  'ftm_lower: %d\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'sftm_match: %d\n'\
                  'count_match: %d\n'\
                  '\n' % (q['first_clause_field'], q['first_clause'],
                                         q['second_clause_field'], q['second_clause'],
                                         q['sftm_lower'], q['sftm_upper'], q['r_lower'],
                                         q['r_upper'], total_match,count_match)
            if count_match <= q[qs.QRY_URSS]*2 and count_match >= q[qs.QRY_LRSS]/2 and\
               total_match <= q['sftm_upper']*2 and total_match >= q['sftm_lower']/2:
                    working_queries+=1
            else:
                non_working_queries.append(msg)
        fail_msg = ''
        for msg in non_working_queries[:3]:
            fail_msg += msg  
        self.assertGreaterEqual(working_queries, 10, fail_msg)                        

                
                
                
            