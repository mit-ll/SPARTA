# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for and_query_batch
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  3 October 2013  ATLH            Original version
# *****************************************************************

from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import unittest
import time
import spar_python.common.spar_random as spar_random 
import spar_python.query_generation.BOQs.atomic_query_batches as eqb
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.generator_workers as gw
import logging
import StringIO as stringio
import spar_python.data_generation.learn_distributions as learn_distributions
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.report_generation.ta1.ta1_database as ta1_database
import spar_python.query_generation.BOQs.compound_query_batch as aqb   
import spar_python.query_generation.query_ids as qids
import time as t

class AndQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.eq_query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'EMMA'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'EMMA' }
        self.eq_query2 = { qs.QRY_QID : 2,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'DAVE'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'DAVE' }
        self.eq_query3 = { qs.QRY_QID : 3,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "military_service = 1",
                 qs.QRY_FIELD : 'military_service',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
        self.eq_query4 = { qs.QRY_QID : 4,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "sex = 1",
                 qs.QRY_FIELD : 'sex',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
        self.and_query1 = {
                qs.QRY_ENUM : qs.CAT.P1_EQ_AND, 
                qs.QRY_QID : 1,
                qs.QRY_PERF : ["LL"],
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P1',
                qs.QRY_SUBCAT : 'eq-and', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 1,
                qs.QRY_FTMUPPER : 10,
                qs.QRY_NUMCLAUSES : 2, 
                qs.QRY_NUMTERMSPERCLAUSE : 1,  
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                                                         self.eq_query3,self.eq_query3],
                                                        None, None, False)]}
        self.and_query2 = {
                qs.QRY_ENUM : qs.CAT.P1_EQ_AND, 
                qs.QRY_QID : 2,
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P1',
                qs.QRY_PERF : ['LL'],
                qs.QRY_SUBCAT : 'eq-and', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 1,
                qs.QRY_FTMUPPER : 10,
                qs.QRY_NUMCLAUSES : 2, 
                qs.QRY_NUMTERMSPERCLAUSE : 1,  
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                                                         self.eq_query4,self.eq_query4],
                                                        None, None, False)]}
        self.batch = aqb.AndQueryBatch([self.and_query1, self.and_query2],2,1,True)
        
    
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 100

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation. These results can then be used 
        to compare
        """
        
        aggs = [self.batch.make_aggregator()]
        options = gw.DataGeneratorOptions(random_seed = 0,
                                               num_processes = 1,
                                               num_rows = self.num_rows,
                                               verbose = False,
                                               aggregators = aggs,
                                               batch_size = 5)
        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(self.learner_options,
                                                 self.dummy_logger,
                                                 pums_files)         
        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(
             '''DAVID          2.629  2.629      1\n'''\
             '''PAT            1.073  3.702      2\n'''\
             '''LARRY          1.035  4.736      3\n'''\
             '''BOB            0.980  5.716      4\n'''\
             '''DAVE           0.937  6.653      5''')),
             ('female_first_names.txt', 
              stringio.StringIO(
             '''MARY           2.629  2.629      1\n'''\
             '''PATRICIA       1.073  3.702      2\n'''\
             '''LINDA          1.035  4.736      3\n'''\
             '''EMMA           0.980  5.716      4\n'''\
             '''ALICE          0.937  6.653      5'''))]
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
        dist_holder = \
            learn_distributions.make_distribution_holder(self.learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)
            
        worker = gw.Worker(options, self.dummy_logger, dist_holder)
        self.aggregator_results = worker.start()

    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """ 
        result = [({'ftm_lower': 1, 
                    'sub_category': 'eq-and', 
                    'where_clause': "fname = 'EMMA' AND military_service = 1", 
                    'r_upper': 10, 
                    'qid': 1, 
                    'enum': 3, 
                    'db_record_size': 100, 
                    'num_clauses': 2, 
                    'num_terms_per_clause': 1, 
                    'ftm_upper': 10, 
                    'negate': False, 
                    'sub_bobs': 
                       [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                        self.eq_query3,self.eq_query3],None, None, False), 
                        eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                        self.eq_query3,self.eq_query3],None, None, False)],
                    'db_num_records': 1000, 
                    'category': 'P1', 
                    'sub_queries':
                        [{'sub_category': '', 
                          'where_clause': "fname = 'EMMA'", 
                          'r_upper': 10, 
                          'r_lower': 1, 
                          'qid': 1, 
                          'enum': 0, 
                          'db_record_size': 100, 
                          'negate': False,
                          'db_num_records': 1000, 
                          'category': 'EQ', 
                          'field_type': 'string', 
                          'value': 'EMMA', 
                          'r_lower': 1, 
                          'field': 'fname'}, 
                         {'sub_category': '', 
                          'where_clause': 'military_service = 1',
                          'r_upper': 1000, 
                          'qid': 3, 
                          'enum': 0, 
                          'db_record_size': 100, 
                          'negate': False, 
                          'db_num_records': 1000, 
                          'category': 'EQ', 
                          'field_type': 'enum', 
                          'value': 1, 
                          'r_lower': 1, 
                          'field': 'military_service'}]}, 
                      {'qid': 1, 
                       'matching_record_ids': set([319, 906, 311, 485, 103]),
                       'num_records_matching_first_term' : 5,
                       'subresults': 
                          [{'qid': 1, 'valid': True, 'matching_record_ids': set([319, 906, 311, 485, 103])}, 
                           {'qid': 3, 'valid': True, 'matching_record_ids': set([319, 906, 311, 485, 103])}]})] 
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE fname = 'EMMA' AND military_service = 1\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """       
        result = {'subresults':  
                 [{'qid': 1, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 2, 'valid': True, 
                   'matching_record_ids': 
                   set([306, 531, 996, 231, 408, 796])}, 
                  {'qid': 3, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 3, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}]}  
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        aggs = self.batch.make_aggregator()
        self.batch.process_results(result, db_object, query_file)
        print query_file.getvalue()
        self.assertEqual(query_file.getvalue(),"1 SELECT * FROM main WHERE fname = 'EMMA' AND military_service = 1\n"+\
                                                "2 SELECT * FROM main WHERE fname = 'EMMA' AND sex = 1\n")
        db_object.close()

class AndTA2QueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.eq_query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "city = 'Lexington'",
                 qs.QRY_FIELD : 'city',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'EMMA' }
        self.eq_query2 = { qs.QRY_QID : 2,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "city = 'Boston'",
                 qs.QRY_FIELD : 'city',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'DAVE' }
        self.eq_query3 = { qs.QRY_QID : 3,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "citizenship = 1",
                 qs.QRY_FIELD : 'citizenship',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
        self.eq_query4 = { qs.QRY_QID : 4,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "hours_worked = 1",
                 qs.QRY_FIELD : 'hours_worked_per_week',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
        self.and_query1 = {
                qs.QRY_ENUM : qs.CAT.P1_EQ_AND, 
                qs.QRY_QID : 1,
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P1',
                qs.QRY_SUBCAT : 'eq-and', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 1,
                qs.QRY_FTMUPPER : 10,
                qs.QRY_NUMCLAUSES : 2, 
                qs.QRY_NUMTERMSPERCLAUSE : 1,  
                qs.QRY_PERF: "IBM2",
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                                                         self.eq_query3,self.eq_query3],
                                                        None, None, False)]}
        self.and_query2 = {
                qs.QRY_ENUM : qs.CAT.P1_EQ_AND, 
                qs.QRY_QID : 2,
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P1',
                qs.QRY_SUBCAT : 'eq-and', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_PERF: "IBM2",
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 1,
                qs.QRY_FTMUPPER : 10,
                qs.QRY_NUMCLAUSES : 2, 
                qs.QRY_NUMTERMSPERCLAUSE : 1,  
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                                                         self.eq_query4,self.eq_query4],
                                                        None, None, False)]}
        self.batch = aqb.AndTA2QueryBatch([self.and_query1, self.and_query2],2,1,True)
        
    
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 100

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation. These results can then be used 
        to compare
        """
        
        aggs = [self.batch.make_aggregator()]
        options = gw.DataGeneratorOptions(random_seed = 0,
                                               num_processes = 1,
                                               num_rows = self.num_rows,
                                               verbose = False,
                                               aggregators = aggs,
                                               batch_size = 5)
        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(self.learner_options,
                                                 self.dummy_logger,
                                                 pums_files)         
        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(
             '''DAVID          2.629  2.629      1\n'''\
             '''PAT            1.073  3.702      2\n'''\
             '''LARRY          1.035  4.736      3\n'''\
             '''BOB            0.980  5.716      4\n'''\
             '''DAVE           0.937  6.653      5''')),
             ('female_first_names.txt', 
              stringio.StringIO(
             '''MARY           2.629  2.629      1\n'''\
             '''PATRICIA       1.073  3.702      2\n'''\
             '''LINDA          1.035  4.736      3\n'''\
             '''EMMA           0.980  5.716      4\n'''\
             '''ALICE          0.937  6.653      5''')),
             ('last_names.txt', 
              stringio.StringIO(
             '''MARY           2.629  2.629      1\n'''\
             '''PATRICIA       1.073  3.702      2\n'''\
             '''LINDA          1.035  4.736      3\n'''\
             '''EMMA           0.980  5.716      4\n'''\
             '''ALICE          0.937  6.653      5'''))]
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
        dist_holder = \
            learn_distributions.make_distribution_holder(self.learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)   
        worker = gw.Worker(options, self.dummy_logger, dist_holder)
        self.aggregator_results = worker.start()

    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """ 
        result = [({'ftm_lower': 1, 
                    'sub_category': 'eq-and', 
                    'where_clause': "citizenship = 1 AND city = 'Boston'", 
                    'r_upper': 10, 
                    'qid': 1, 
                    'enum': 3, 
                    'db_record_size': 100, 
                    'num_clauses': 2, 
                    'num_terms_per_clause': 1, 
                    'ftm_upper': 10, 
                    'negate': False, 
                    'sub_bobs': 
                       [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                        self.eq_query3,self.eq_query3],None, None, False), 
                        eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                        self.eq_query3,self.eq_query3],None, None, False)],
                    'db_num_records': 1000, 
                    'category': 'P1', 
                    'sub_queries':
                        [{'sub_category': '', 
                          'where_clause': "city = 'Boston'", 
                          'r_upper': 10, 
                          'r_lower': 1, 
                          'qid': 1, 
                          'enum': 0, 
                          'db_record_size': 100, 
                          'negate': False,
                          'db_num_records': 1000, 
                          'category': 'EQ', 
                          'field_type': 'string', 
                          'value': 'Boston', 
                          'r_lower': 1, 
                          'field': 'city'}, 
                         {'sub_category': '', 
                          'where_clause': 'citizenship = 1',
                          'r_upper': 1000, 
                          'qid': 3, 
                          'enum': 0, 
                          'db_record_size': 100, 
                          'negate': False, 
                          'db_num_records': 1000, 
                          'category': 'EQ', 
                          'field_type': 'enum', 
                          'value': 1, 
                          'r_lower': 1, 
                          'field': 'military_service'}]}, 
                      {'qid': 1, 
                       'matching_record_ids': set([319, 906, 311, 485, 103]),
                       'num_records_matching_first_term' : 5,
                       'subresults': 
                          [{'qid': 1, 'valid': True, 
                            'matching_record_ids': set([319, 906, 311, 485, 103])}, 
                           {'qid': 3, 'valid': True, 
                            'matching_record_ids': set([319, 906, 311, 485, 103])}]})] 
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE citizenship = 1 AND city = 'Boston'\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """       
        result = {'subresults':  
                 [{'qid': 1, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 2, 'valid': True, 
                   'matching_record_ids': 
                   set([306, 531, 996, 231, 408, 796])}, 
                  {'qid': 3, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 3, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}]}   
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        aggs = self.batch.make_aggregator()
        self.batch.process_results(result, db_object, query_file)
        print query_file.getvalue()
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE city = 'Lexington' AND citizenship = 1\n"+\
                         "2 SELECT * FROM main WHERE city = 'Lexington' AND hours_worked = 1\n")
        db_object.close()
        
class OrQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.eq_query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'EMMA'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'EMMA' }
        self.eq_query2 = { qs.QRY_QID : 2,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'DAVE'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'DAVE' }
        self.eq_query3 = { qs.QRY_QID : 3,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "military_service = 1",
                 qs.QRY_FIELD : 'military_service',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
        self.eq_query4 = { qs.QRY_QID : 4,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "sex = 1",
                 qs.QRY_FIELD : 'sex',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
       
        self.and_query1 = {
                qs.QRY_ENUM : qs.CAT.P1_EQ_OR, 
                qs.QRY_QID : 1,
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P1',
                qs.QRY_SUBCAT : 'eq-or', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 10,
                qs.QRY_FTMUPPER : 100,
                qs.QRY_NUMCLAUSES : 2, 
                qs.QRY_NUMTERMSPERCLAUSE : 1,  
                qs.QRY_PERF : ["LL"],
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query3,self.eq_query4,
                                                         self.eq_query2,self.eq_query1],
                                                        None, None, False)]}
        self.and_query2 = {
                qs.QRY_ENUM : qs.CAT.P1_EQ_OR, 
                qs.QRY_QID : 2,
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P1',
                qs.QRY_SUBCAT : 'eq-or', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 10,
                qs.QRY_FTMUPPER : 100,
                qs.QRY_NUMCLAUSES : 2, 
                qs.QRY_NUMTERMSPERCLAUSE : 1,  
                qs.QRY_PERF : ["LL"],
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                                                         self.eq_query3,self.eq_query4],
                                                        None, None, False)]}
        self.batch = aqb.OrQueryBatch([self.and_query1, self.and_query2],2,1,True)
        
    
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 100

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation. These results can then be used 
        to compare
        """
        
        aggs = [self.batch.make_aggregator()]
        options = gw.DataGeneratorOptions(random_seed = 0,
                                               num_processes = 1,
                                               num_rows = self.num_rows,
                                               verbose = False,
                                               aggregators = aggs,
                                               batch_size = 5)
        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(self.learner_options,
                                                 self.dummy_logger,
                                                 pums_files)         
        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(
             '''DAVID          2.629  2.629      1\n'''\
             '''PAT            1.073  3.702      2\n'''\
             '''LARRY          1.035  4.736      3\n'''\
             '''BOB            0.980  5.716      4\n'''\
             '''DAVE           0.937  6.653      5''')),
             ('female_first_names.txt', 
              stringio.StringIO(
             '''MARY           2.629  2.629      1\n'''\
             '''PATRICIA       1.073  3.702      2\n'''\
             '''LINDA          1.035  4.736      3\n'''\
             '''EMMA           0.980  5.716      4\n'''\
             '''ALICE          0.937  6.653      5'''))]
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
        dist_holder = \
            learn_distributions.make_distribution_holder(self.learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)
            
        worker = gw.Worker(options, self.dummy_logger, dist_holder)
        self.aggregator_results = worker.start()

    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """ 
        result = [({'ftm_lower': 1, 
                    'sub_category': 'eq-or', 
                    'where_clause': "fname = 'EMMA' OR military_service = 1", 
                    'r_upper': 10, 
                    'qid': 1, 
                    'enum': 4, 
                    'perf':['LL'],
                    'db_record_size': 100, 
                    'num_clauses': 2, 
                    'num_terms_per_clause': 1, 
                    'ftm_upper': 10, 
                    'negate': False, 
                    'sub_bobs': 
                       [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                        self.eq_query3,self.eq_query3],None, None, False), 
                        eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                        self.eq_query3,self.eq_query3],None, None, False)],
                    'db_num_records': 1000, 
                    'category': 'P1', 
                    'sub_queries':
                        [{'sub_category': '', 
                          'where_clause': "fname = 'EMMA'", 
                          'r_upper': 10, 
                          'r_lower': 1, 
                          'qid': 1, 
                          'enum': 0, 
                          'db_record_size': 100, 
                          'negate': False,
                          'db_num_records': 1000, 
                          'category': 'EQ', 
                          'field_type': 'string', 
                          'value': 'EMMA', 
                          'r_lower': 1, 
                          'field': 'fname'}, 
                         {'sub_category': '', 
                          'where_clause': 'military_service = 1',
                          'r_upper': 1000, 
                          'qid': 3, 
                          'enum': 0, 
                          'db_record_size': 100, 
                          'negate': False, 
                          'db_num_records': 1000, 
                          'category': 'EQ', 
                          'field_type': 'enum', 
                          'value': 1, 
                          'r_lower': 1, 
                          'field': 'military_service'}]}, 
                      {'qid': 1, 
                       'matching_record_ids': set([319, 906, 311, 485, 103, 634, 965]),
                       'subresults': 
                          [{'qid': 1, 'valid': True, 
                            'matching_record_ids': set([319, 906, 311, 634, 485, 103])}, 
                           {'qid': 3, 'valid': True, 
                            'matching_record_ids': set([319, 906, 311, 485, 965, 103])}]})] 
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.batch.process_results(None, db_object, query_file, refined_queries=result)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE fname = 'EMMA' OR military_service = 1\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """       
        result = {'subresults':  
                 [{'qid': 1, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 2, 'valid': True, 
                   'matching_record_ids': 
                   set([306, 531, 996, 231, 408, 796])}, 
                  {'qid': 3, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 4, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}]}   
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        aggs = self.batch.make_aggregator()
        self.batch.process_results(result, db_object, query_file)
        print query_file.getvalue()
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE military_service = 1 OR fname = 'DAVE'\n"+\
                         "2 SELECT * FROM main WHERE fname = 'EMMA' OR fname = 'DAVE'\n")
        db_object.close()

class ThresholdQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.eq_query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'EMMA'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'EMMA' }
        self.eq_query2 = { qs.QRY_QID : 2,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'DAVE'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'DAVE' }
        self.eq_query3 = { qs.QRY_QID : 3,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "military_service = 1",
                 qs.QRY_FIELD : 'military_service',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
        self.eq_query4 = { qs.QRY_QID : 4,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "sex = 1",
                 qs.QRY_FIELD : 'sex',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'enum',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 1000,
                 qs.QRY_VALUE : 1}
       
        self.and_query1 = {
                qs.QRY_ENUM : qs.CAT.P8_EQ, 
                qs.QRY_QID : 1,
                qs.QRY_PERF : ["LL"],
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P8',
                qs.QRY_SUBCAT : 'threshold', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 10,
                qs.QRY_FTMUPPER : 100,
                qs.QRY_M : 2,
                qs.QRY_N : 3,  
                qs.QRY_PERF : ["LL"],
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                                                         self.eq_query3,self.eq_query3],
                                                        None, None, False)]}
        self.and_query2 = {
                qs.QRY_ENUM : qs.CAT.P8_EQ, 
                qs.QRY_QID : 2,
                qs.QRY_PERF : ["LL"],
                qs.QRY_DBNUMRECORDS : 1000,
                qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_CAT : 'P8',
                qs.QRY_SUBCAT : 'threshold', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : 1,
                qs.QRY_URSS : 10,
                qs.QRY_FTMLOWER : 10,
                qs.QRY_FTMUPPER : 100,
                qs.QRY_M : 2,
                qs.QRY_N : 3,
                qs.QRY_PERF : ["LL"],
                qs.QRY_SUBBOBS : [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                                                         self.eq_query4,self.eq_query4],
                                                        None, None, False)]}
        self.batch = aqb.ThresholdQueryBatch([self.and_query1, self.and_query2],2,1,True)
        
    
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 100

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation. These results can then be used 
        to compare
        """
        
        aggs = [self.batch.make_aggregator()]
        options = gw.DataGeneratorOptions(random_seed = 0,
                                               num_processes = 1,
                                               num_rows = self.num_rows,
                                               verbose = False,
                                               aggregators = aggs,
                                               batch_size = 5)
        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(self.learner_options,
                                                 self.dummy_logger,
                                                 pums_files)         
        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(
             '''DAVID          2.629  2.629      1\n'''\
             '''PAT            1.073  3.702      2\n'''\
             '''LARRY          1.035  4.736      3\n'''\
             '''BOB            0.980  5.716      4\n'''\
             '''DAVE           0.937  6.653      5''')),
             ('female_first_names.txt', 
              stringio.StringIO(
             '''MARY           2.629  2.629      1\n'''\
             '''PATRICIA       1.073  3.702      2\n'''\
             '''LINDA          1.035  4.736      3\n'''\
             '''EMMA           0.980  5.716      4\n'''\
             '''ALICE          0.937  6.653      5'''))]
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
        dist_holder = \
            learn_distributions.make_distribution_holder(self.learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)
            
        worker = gw.Worker(options, self.dummy_logger, dist_holder)
        self.aggregator_results = worker.start()
    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """ 
        result = [({'ftm_lower': 10, 
                   'sub_category': 'threshold', 
                   'where_clause': "M_OF_N(2, 3, fname = 'EMMA', fname = 'DAVE', military_service = 1)", 
                   'r_upper': 100, 
                   'qid': 1, 
                   'enum': 41, 
                   'perf':['LL'],
                   'db_record_size': 100, 
                   'ftm_upper': 100, 
                   'negate': False, 
                   'sub_bobs': [eqb.EqualityQueryBatch([self.eq_query1,self.eq_query2,
                        self.eq_query3,self.eq_query4],None, None, False)],
                   'db_num_records': 1000, 
                   'category': 'P8', 
                   'sub_queries': 
                     [{'sub_category': '', 
                        'where_clause': "fname = 'EMMA'", 
                        'r_upper': 10, 
                        'qid': 1, 
                        'enum': 0, 
                        'db_record_size': 100, 
                        'negate': False, 
                        'db_num_records': 1000, 
                        'category': 'EQ', 
                        'field_type': 'string', 
                        'value': 'EMMA', 
                        'r_lower': 1, 
                        'field': 'fname'}, 
                       {'sub_category': '', 
                        'where_clause': "fname = 'DAVE'", 
                        'r_upper': 10, 
                        'qid': 2, 
                        'enum': 0, 
                        'db_record_size': 100, 
                        'negate': False, 
                        'db_num_records': 1000, 
                        'category': 'EQ', 
                        'field_type': 'string', 
                        'value': 'DAVE', 
                        'r_lower': 1, 
                        'field': 'fname'}, 
                      {'sub_category': '', 
                        'where_clause': 'military_service = 1', 
                        'r_upper': 1000, 
                        'qid': 3, 
                        'enum': 0, 
                        'db_record_size': 100, 
                        'negate': False, 
                        'db_num_records': 1000, 
                        'category': 'EQ', 
                        'field_type': 'enum', 
                        'value': 1, 
                        'r_lower': 1, 
                        'field': 'military_service'}], 
                   'm_value': 2, 
                   'r_lower': 10, 
                   'n_value': 3},
          {'qid': 1,
           'matching_record_counts' : '8|0',
           'matching_record_ids': set([319, 906, 311, 485, 103, 634, 965]),
           'subresults': 
              [{'qid': 1, 'valid': True, 
                'matching_record_ids': set([15,17,20,21,26,27,28])}, 
               {'qid': 2, 'valid': True, 
                'matching_record_ids': set([319, 906, 311, 634, 485, 103])},
               {'qid': 3, 'valid': True, 
                'matching_record_ids': set([319, 906, 311, 485, 965, 103])}]})]     
         
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.batch.process_results(None, db_object, query_file, result)
        query1= "M_OF_N(2, 3, fname = 'EMMA', fname = 'DAVE', military_service = 1)"
        qid1 = qids.full_where_has_been_seen(1, query1)
        query2 = "M_OF_N(2, 3, fname = 'EMMA', fname = 'DAVE', military_service = 1) ORDER BY M_OF_N(2, 3, fname = 'EMMA', fname = 'DAVE', military_service = 1) DESC"
        qid2 = qids.full_where_has_been_seen(1, query2)
        self.assertEqual(query_file.getvalue(), "%d SELECT * FROM main WHERE %s\n%d SELECT * FROM main WHERE %s\n" % 
                         (qid1, query1, qid2, query2))
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test the refinement function
        """       
        result = {'subresults':  
                 [{'qid': 1, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 2, 'valid': True, 
                   'matching_record_ids': 
                   set([306, 531, 996, 231, 408, 796])}, 
                  {'qid': 3, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}, 
                  {'qid': 3, 'valid': True, 
                   'matching_record_ids': 
                   set([485, 103, 906, 311, 319])}]}
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        _ = self.batch.make_aggregator()
        self.batch.process_results(result, db_object, query_file)
        print query_file.getvalue()
        result = "1 SELECT * FROM main WHERE M_OF_N(2, 3, fname = 'EMMA', military_service = 1, fname = 'DAVE')\n"+\
        str(int(t.time())) + "1 SELECT * FROM main WHERE M_OF_N(2, 3, fname = 'EMMA', military_service = 1, fname = 'DAVE') "+\
        "ORDER BY M_OF_N(2, 3, fname = 'EMMA', military_service = 1, fname = 'DAVE') DESC\n"+\
        "2 SELECT * FROM main WHERE M_OF_N(2, 3, fname = 'EMMA', sex = 1, fname = 'DAVE')\n"+\
        str(int(t.time())) + "2 SELECT * FROM main WHERE M_OF_N(2, 3, fname = 'EMMA', sex = 1, fname = 'DAVE') "+\
        "ORDER BY M_OF_N(2, 3, fname = 'EMMA', sex = 1, fname = 'DAVE') DESC\n"

        self.assertEqual(query_file.getvalue(), result)
        db_object.close()
       

        
        
        
        
        
        
        
        
        
        
        
        
        
        