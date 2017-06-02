# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for equality_query_batch
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  6 September 2013  ATLH            Original version
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
import datetime
import spar_python.data_generation.learn_distributions as learn_distributions
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.report_generation.ta1.ta1_database as ta1_database    

class EqualityQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.query1 = { qs.QRY_QID : 1,
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
        self.query2 = { qs.QRY_QID : 2,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'DAVE'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 30,
                 qs.QRY_URSS : 50,
                 qs.QRY_VALUE : 'DAVE' }
        self.query3 = { qs.QRY_QID : 3,
                        qs.QRY_ENUM : qs.CAT.EQ,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100,          
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "", 
                 qs.QRY_WHERECLAUSE : "fname = 'ALICE'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : 'ALICE'}
        queries = [self.query1,self.query2,self.query3]
        self.refine_batch = eqb.EqualityQueryBatch(queries, 3, 1,True)
        self.nonrefine_batch = eqb.EqualityQueryBatch(queries, 3, 1, True)
        self.refine_test = eqb.EqualityQueryBatch(queries,3,1,True)
        
    
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
        
        aggs = [self.refine_batch.make_aggregator()]
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


        
    
    def testRefineQueries(self):
        """
        Tests query refinement
        """
        result = { qs.QRY_SUBRESULTS : \
                  [{'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}, 
                   {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])}, 
                   {'qid': 3, 'valid': False, 'matching_record_ids': set([])} ] }
        self.refine_test.refine_queries(result)
        refined = self.refine_test.produce_queries()
        self.assertTrue(len(refined)==2, self.seed_msg)
        self.assertEqual(refined[0][0],self.query1, self.seed_msg)
        self.assertLess(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)

    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """       
        result = [(self.query1, {'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])})]
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.refine_batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE fname = 'EMMA'\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """       
        result = { qs.QRY_SUBRESULTS : [{'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}, 
                   {'qid': 2, 'valid': False, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])}, 
                   {'qid': 3, 'valid': True, 'matching_record_ids': set([693, 710, 987, 239, 494, 175])} ] }
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.refine_batch.process_results(result, db_object, query_file)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE fname = 'EMMA'\n3 SELECT * FROM main WHERE fname = 'ALICE'\n")
        db_object.close()
    
    
class FooRangeQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                qs.QRY_ENUM : qs.CAT.P2_RANGE_FOO,
                 qs.QRY_CAT : 'P2',
                 qs.QRY_SUBCAT : "foo-range", 
                 qs.QRY_WHERECLAUSE : "foo BETWEEN 8830130 AND 13119622",
                 qs.QRY_FIELD : 'foo',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'integer',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_RANGEEXP : 17,
                 qs.QRY_LBOUND : 8830130,
                 qs.QRY_UBOUND : 13119622,
                 qs.QRY_RANGE : 13119622-8830130}        
        self.query2 = { qs.QRY_QID : 2,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P2',
                 qs.QRY_SUBCAT : "foo-range",
                  qs.QRY_ENUM : qs.CAT.P2_RANGE_FOO, 
                 qs.QRY_WHERECLAUSE : "foo BETWEEN 36564612 AND 49231831",
                 qs.QRY_FIELD : 'foo',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'integer',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_RANGEEXP : 18,
                 qs.QRY_LBOUND : 36564612,
                 qs.QRY_UBOUND : 49231831,
                 qs.QRY_RANGE : 49231831-36564612}
        self.query3 = { qs.QRY_QID : 3,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P2',
                 qs.QRY_SUBCAT : "foo-range", 
                  qs.QRY_ENUM : qs.CAT.P2_RANGE_FOO,
                 qs.QRY_WHERECLAUSE : "foo BETWEEN 48676972 AND 67229801",
                 qs.QRY_FIELD : 'foo',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'integer',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_RANGEEXP : 18,
                 qs.QRY_LBOUND : 48676972,
                 qs.QRY_UBOUND : 67229801,
                 qs.QRY_RANGE : 67229801-48676972}
        queries = [self.query1,self.query2,self.query3]
        self.refine_batch = eqb.FooRangeQueryBatch(queries,3,2,True)
        self.nonrefine_batch = eqb.FooRangeQueryBatch(queries,3,2,True)
        self.refine_test = eqb.FooRangeQueryBatch(queries,3,2,True)
        
    
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 1000

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation.
        """

        aggs = [self.refine_batch.make_aggregator(),
                self.nonrefine_batch.make_aggregator()]
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

        
    
    def testRefineQueries(self):
        """
        Tests query refinement
        """
        result = { qs.QRY_SUBRESULTS : [{'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}, 
                   {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])}, 
                   {'qid': 3, 'valid': True, 'matching_record_ids': set([693, 710, 987, 239, 494, 175])} ] }
        self.refine_test.refine_queries(result)
        refined = self.refine_test.produce_queries()
        self.assertEqual(len(refined), 2, self.seed_msg)
        self.assertEqual(refined[0][0],self.query1, self.seed_msg)
        self.assertLess(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)

    
    def testProcessResultsCallingRefine(self):
        """
        test write_query
        """       

        result = [(self.query1, {'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}), 
                  (self.query2, {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])})] 
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.refine_batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE foo BETWEEN 8830130 AND 13119622\n"\
                                                +"2 SELECT * FROM main WHERE foo BETWEEN 36564612 AND 49231831\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRegine(self):
        """
        test write_query
        """       
        result = { qs.QRY_SUBRESULTS : [{'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}, 
                   {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])}, 
                   {'qid': 3, 'valid': True, 'matching_record_ids': set([693, 710, 987, 239, 494, 175])} ] }
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.refine_batch.process_results(result, db_object, query_file)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE foo BETWEEN 8830130 AND 13119622\n"\
                                                +"2 SELECT * FROM main WHERE foo BETWEEN 36564612 AND 49231831\n")
        db_object.close()

class RangeQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_ENUM : qs.CAT.P2_RANGE,
                 qs.QRY_CAT : 'P2',
                 qs.QRY_SUBCAT : "range", 
                 qs.QRY_WHERECLAUSE : "income BETWEEN 17135 AND 23984",
                 qs.QRY_FIELD : 'income',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'integer',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_LBOUND : 17135,
                 qs.QRY_UBOUND : 23984,
                 qs.QRY_RANGE : 0}        
        self.query2 = { qs.QRY_QID : 2,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P2',
                 qs.QRY_SUBCAT : "less",
                 qs.QRY_ENUM : qs.CAT.P2_LESS, 
                 qs.QRY_WHERECLAUSE : "dob <= ''1991-08-19''",
                 qs.QRY_FIELD : 'dob',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'date',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : datetime.date(1991,8,19),
                 qs.QRY_RANGE : 0}
        self.query3 = { qs.QRY_QID : 3,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P2',
                 qs.QRY_SUBCAT : "foo-range", 
                 qs.QRY_ENUM : qs.CAT.P2_GREATER,
                 qs.QRY_WHERECLAUSE : "ssn >= ''464457854''",
                 qs.QRY_FIELD : 'ssn',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_VALUE : '464457854',
                 qs.QRY_RANGE : 0}
        queries = [self.query1,self.query2,self.query3]
        self.refine_batch = eqb.RangeQueryBatch(queries,3,2,True)
        self.nonrefine_batch = eqb.RangeQueryBatch(queries,3,2,True)
        self.refine_test = eqb.RangeQueryBatch(queries,3,2,True)
        
    
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 1000

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation.
        """

        aggs = [self.refine_batch.make_aggregator(),
                self.nonrefine_batch.make_aggregator()]
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

        
    
    def testRefineQueries(self):
        """
        Tests query refinement
        """
        result = { qs.QRY_SUBRESULTS : [{'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}, 
                   {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])}, 
                   {'qid': 3, 'valid': False, 'matching_record_ids': set([693, 710, 987, 239, 494, 175])} ] }
        self.refine_test.refine_queries(result)
        refined = self.refine_test.produce_queries()
        self.assertEqual(len(refined), 2, self.seed_msg)
        self.assertEqual(refined[0][0],self.query1, self.seed_msg)
        self.assertLess(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)

    
    def testProcessResultsCallingRefine(self):
        """
        test write_query
        """       

        result = [(self.query1, {'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}), 
                  (self.query2, {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])})] 
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.refine_batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE income BETWEEN 17135 AND 23984\n"+\
                         "2 SELECT * FROM main WHERE dob <= '1991-08-19'\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRegine(self):
        """
        test write_query
        """       
        result = { qs.QRY_SUBRESULTS : [{'qid': 1, 'valid': True, 'matching_record_ids': set([672, 736, 331, 485, 103, 906, 311, 319])}, 
                   {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])}, 
                   {'qid': 3, 'valid': False, 'matching_record_ids': set([693, 710, 987, 239, 494, 175])} ] }
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.refine_batch.process_results(result, db_object, query_file)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE income BETWEEN 17135 AND 23984\n"+\
                         "2 SELECT * FROM main WHERE dob <= '1991-08-19'\n")
        db_object.close()        
        
class KeywordQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P3',
                 qs.QRY_SUBCAT : "word", 
                  qs.QRY_ENUM : qs.CAT.P3,
                 qs.QRY_WHERECLAUSE : "CONTAINED_IN(notes3, 'gooseberry')",
                 qs.QRY_FIELD : 'notes3',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN: 10,
                 qs.QRY_SEARCHFOR: 'gooseberry'
                 }        
        self.query2 = { qs.QRY_QID : 2,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P3',
                 qs.QRY_SUBCAT : "word", 
                 qs.QRY_WHERECLAUSE : "CONTAINED_IN(notes3, 'navigables')",
                 qs.QRY_FIELD : 'notes3',
                  qs.QRY_ENUM : qs.CAT.P3,
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN: 10,
                 qs.QRY_SEARCHFOR: 'navigables'
                 } 
        self.query3 = { qs.QRY_QID : 3,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P4',
                 qs.QRY_SUBCAT : "stem", 
                  qs.QRY_ENUM : qs.CAT.P4,
                 qs.QRY_WHERECLAUSE : "CONTAINS_STEM(notes3, 'recreating')",
                 qs.QRY_FIELD : 'notes3',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN: 10,
                 qs.QRY_SEARCHFOR: 'recreat'
                 } 
        self.query4 = { qs.QRY_QID : 4,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P4',
                 qs.QRY_SUBCAT : "stem", 
                  qs.QRY_ENUM : qs.CAT.P4,
                 qs.QRY_WHERECLAUSE : "CONTAINS_STEM(notes3, 'navigable')",
                 qs.QRY_FIELD : 'notes3',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN: 10,
                 qs.QRY_SEARCHFOR: 'navig'
                 } 
        word_queries = [self.query1,self.query2]
        stem_queries = [self.query3,self.query4]
        self.word_batch = eqb.KeywordQueryBatch(word_queries,2,1,True)
        self.stem_batch = eqb.KeywordQueryBatch(stem_queries,2,1,True)
        
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 1000

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation.
        """

        aggs = [self.word_batch.make_aggregator(),
                self.stem_batch.make_aggregator()]
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

        
    
    def testRefineQueries(self):
        """
        Tests query refinement
        """
        result = { qs.QRY_SUBRESULTS : [{'qid': 1, 'valid': True, 'matching_record_ids': set([])}, 
                   {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])} ] }
        self.word_batch.refine_queries(result)
        refined = self.word_batch.produce_queries()
        self.assertEqual(len(refined), 1, self.seed_msg)
        self.assertEqual(refined[0][0],self.query2, self.seed_msg)
        self.assertLess(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        
        result = { qs.QRY_SUBRESULTS : [{'qid': 3, 'valid': True, 'matching_record_ids': set([])},
                   {'qid': 4, 'valid': True, 'matching_record_ids': set([63, 700, 87, 139, 594, 675])} ] }
        self.stem_batch.refine_queries(result)
        refined = self.stem_batch.produce_queries()
        self.assertEqual(len(refined), 1, self.seed_msg)
        self.assertEqual(refined[0][0], self.query4, self.seed_msg)
        self.assertLess(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)

    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """       
        result = [(self.query2, {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])})]
   
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.word_batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), "2 SELECT * FROM main WHERE CONTAINED_IN(notes3, 'navigables')\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """       
        result = { qs.QRY_SUBRESULTS : [{'qid': 3, 'valid': True, 'matching_record_ids': set([])},
                   {'qid': 4, 'valid': True, 'matching_record_ids': set([63, 700, 87, 139, 594, 675])} ] }
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.stem_batch.process_results(result, db_object, query_file)
        self.assertEqual(query_file.getvalue(), 
                         "4 SELECT * FROM main WHERE CONTAINS_STEM(notes3, 'navigable')\n")
        db_object.close()
        
        
class WildcardQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P6',
                  qs.QRY_ENUM : qs.CAT.P6_INITIAL_ONE,
                 qs.QRY_SUBCAT : "initial-one", 
                 qs.QRY_WHERECLAUSE : "fname LIKE '_AMANTHA'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN : 6,
                 qs.QRY_SEARCHFOR : 'amantha',
                 qs.QRY_SEARCHFORLIST : [None, None],
                 qs.QRY_SEARCHDELIMNUM : 1 }
        self.query2 = { qs.QRY_QID : 2,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P6',
                 qs.QRY_SUBCAT : "initial-one",
                 qs.QRY_ENUM : qs.CAT.P6_INITIAL_ONE, 
                 qs.QRY_WHERECLAUSE : "fname LIKE '_ERBERT'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN : 6,
                 qs.QRY_SEARCHFOR : 'arbor',
                 qs.QRY_SEARCHFORLIST : [None, None],
                 qs.QRY_SEARCHDELIMNUM : 1 }
                 
        self.query3 = { qs.QRY_QID : 3,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P7',
                 qs.QRY_SUBCAT : "both", 
                 qs.QRY_ENUM : qs.CAT.P7_BOTH,
                 qs.QRY_WHERECLAUSE : "notes3 LIKE %arbor o%",
                 qs.QRY_FIELD : 'notes3',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN: 10,
                 qs.QRY_SEARCHFOR: 'arbor o'
                 } 
        self.query4 = { qs.QRY_QID : 4,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P7',
                 qs.QRY_SUBCAT : "both", 
                 qs.QRY_ENUM : qs.CAT.P7_BOTH,
                 qs.QRY_WHERECLAUSE : "notes3 LIKE %ubble and%",
                 qs.QRY_FIELD : 'notes3',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_KEYWORDLEN: 10,
                 qs.QRY_SEARCHFOR: 'ubble and'
                 } 
        word_queries = [self.query1,self.query2]
        stem_queries = [self.query3,self.query4]
        self.P6_batch = eqb.WildcardQueryBatch(word_queries,2,1,True)
        self.P7_batch = eqb.WildcardQueryBatch(stem_queries,2,1,True)
        
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 1000

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation.
        """

        aggs = [self.P6_batch.make_aggregator(),
                self.P7_batch.make_aggregator()]
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

        
    
    def testRefineQueries(self):
        """
        Tests query refinement
        """
        result = { qs.QRY_SUBRESULTS : \
                  [{'qid': 1, 'valid': False, 'matching_record_ids': set([])}, 
                   {'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])} ] }
        self.P6_batch.refine_queries(result)
        refined = self.P6_batch.produce_queries()
        self.assertEqual(len(refined), 1, self.seed_msg)
        self.assertEqual(refined[0][0],self.query2, self.seed_msg)
        self.assertLess(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        
        result = { qs.QRY_SUBRESULTS : \
                  [{'qid': 3, 'valid': True, 'matching_record_ids': set([])},
                   {'qid': 4, 'valid': True, 'matching_record_ids': set([63, 700, 87, 139, 594, 675])} ] }
        self.P7_batch.refine_queries(result)
        refined = self.P7_batch.produce_queries()
        self.assertEqual(len(refined), 1, self.seed_msg)
        self.assertEqual(refined[0][0], self.query4, self.seed_msg)
        self.assertLess(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)

    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """       
        result = [(self.query2,{'qid': 2, 'valid': True, 'matching_record_ids': set([306, 531, 996, 231, 408, 796])})]
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.P6_batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), "2 SELECT * FROM main WHERE fname LIKE '_ERBERT'\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """       
        result = { qs.QRY_SUBRESULTS : [{'qid': 3, 'valid': True, 'matching_record_ids': set([])},
                   {'qid': 4, 'valid': True, 'matching_record_ids': set([63, 700, 87, 139, 594, 675])} ] }
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.P7_batch.process_results(result, db_object, query_file)
        self.assertEqual(query_file.getvalue(), "4 SELECT * FROM main WHERE notes3 LIKE %ubble and%\n")
        db_object.close()
 
        
class EqualityFishingQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "eq", 
                 qs.QRY_ENUM : qs.CAT.EQ_FISHING_STR,
                 qs.QRY_WHERECLAUSE : "ssn = '162467564'",
                 qs.QRY_FIELD : 'ssn',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_SEARCHFOR : '162',
                 qs.QRY_LBOUND : None,
                 qs.QRY_UBOUND : None,
                 qs.QRY_VALUE : 162467564}
        self.query2 = { qs.QRY_QID : 2,
                 qs.QRY_ENUM : qs.CAT.EQ_FISHING_STR,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "eq", 
                 qs.QRY_WHERECLAUSE : "ssn = '007689345'",
                 qs.QRY_FIELD : 'fname',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_SEARCHFOR : '007',  
                 qs.QRY_LBOUND : None,
                 qs.QRY_UBOUND : None  }
                 
        self.query3 = { qs.QRY_QID : 3,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : "eq", 
                 qs.QRY_ENUM : qs.CAT.EQ_FISHING_INT,
                 qs.QRY_WHERECLAUSE : "last_updated = '950375422'",
                 qs.QRY_FIELD : 'last_updated',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_SEARCHFOR : None, 
                 qs.QRY_LBOUND : 950375000,
                 qs.QRY_UBOUND : 950376000} 
        self.query4 = { qs.QRY_QID : 4,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_ENUM : qs.CAT.EQ_FISHING_INT,
                 qs.QRY_SUBCAT : "eq", 
                 qs.QRY_WHERECLAUSE : "last_updated = '950375428'",
                 qs.QRY_FIELD : 'last_updated',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_SEARCHFOR : None, 
                 qs.QRY_LBOUND : 950370000,
                 qs.QRY_UBOUND : 950380000} 
        
        string_queries = [self.query1,self.query2]
        integer_queries = [self.query3,self.query4]
        self.string_batch = eqb.EqualityFishingQueryBatch(string_queries,2,1,True)
        self.integer_batch = eqb.EqualityFishingQueryBatch(integer_queries,2,1,True)
        
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 1000

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation.
        """

        aggs = [self.string_batch.make_aggregator(),
                self.integer_batch.make_aggregator()]
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
        

    def testRefineQueries(self):
        """
        Tests query refinement
        """
        result1 = {qs.QRY_SUBRESULTS : [{'fishing_matches_found': {'162467564': 
              set([4294967865]), '162467564': set([4294967412]), 
              '162467564': set([4294967961]), '162467564': set([4294968097])}, 
              'qid': 1, 'matching_record_ids': set([])}, 
           {'fishing_matches_found': {}, 'qid': 2, 'matching_record_ids': 
               set([])} ] } 
        result2 = {qs.QRY_SUBRESULTS : [{'fishing_matches_found':  {}, 'qid': 3, 'matching_record_ids': 
               set([])}, 
           {'fishing_matches_found': {'950375428' : set([39480934])}, 'qid': 4, 
               'matching_record_ids': set([])} ] }
        self.string_batch.refine_queries(result1)
        refined = self.string_batch.produce_queries()
        self.assertEqual(len(refined), 1, self.seed_msg)
        self.assertEqual(refined[0][0],self.query1, self.seed_msg)
        self.assertLessEqual(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        
        self.integer_batch.refine_queries(result2)
        refined = self.integer_batch.produce_queries()
        self.assertEqual(len(refined), 1, self.seed_msg)
        self.assertEqual(refined[0][0], self.query4, self.seed_msg)
        self.assertLessEqual(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreater(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)

        
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """  
        result1 = [(self.query1,{'qid': 1, 'valid': True, 'matching_record_ids': set([306])})]     
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.string_batch.process_results(None, db_object, query_file, result1)
        self.assertEqual(query_file.getvalue(), "1 SELECT * FROM main WHERE ssn = '162467564'\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """       
        result1 = {qs.QRY_SUBRESULTS : 
                    [{'fishing_matches_found': {'162467564': set([4294967865]), 
                                                '162467564': set([4294967412]), 
                                                '162467564': set([4294967961]), 
                                                '162467564': set([4294968097])}, 
                      'qid': 1, 
                      'matching_record_ids': set([])}, 
                     {'fishing_matches_found': {}, 
                      'qid': 2, 
                      'matching_record_ids': set([])} ] }
         
        result2 = {qs.QRY_SUBRESULTS : 
                   [{'fishing_matches_found':  {}, 
                     'qid': 3, 
                     'matching_record_ids': set([])}, 
                    {'fishing_matches_found': {'950375428' : set([39480934])}, 
                     'qid': 4, 
                     'matching_record_ids': set([])} ] }
        
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.integer_batch.process_results(result2, db_object, query_file)
        self.assertEqual(query_file.getvalue(), "4 SELECT * FROM main WHERE last_updated = 950375428\n")
        db_object.close()


class AlarmQueryBatchTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = 0
        self.seed_msg = "Seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        self.query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P9',
                 qs.QRY_PERF : ['LL'],
                 qs.QRY_ENUM : qs.CAT.P9_ALARM_WORDS,
                 qs.QRY_SUBCAT : "alarm-words", 
                 qs.QRY_WHERECLAUSE : "BYTE_DISTANCE(notes2, ''daxoz'', ''devaaz'') < 50",
                 qs.QRY_FIELD : 'notes2',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_ALARMWORDONE : 'daxoz', 
                 qs.QRY_ALARMWORDTWO : 'devaaz',
                 qs.QRY_ALARMWORDDISTANCE : 50}
        self.query2 = { qs.QRY_QID : 2,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P9',
                 qs.QRY_SUBCAT : 'alarm-words',
                 qs.QRY_PERF : ['LL'],
                 qs.QRY_ENUM : qs.CAT.P9_ALARM_WORDS, 
                 qs.QRY_WHERECLAUSE : "BYTE_DISTANCE(notes2, ''dharahz'', ''dharamaanz'') < 50",
                 qs.QRY_FIELD : 'notes2',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_ALARMWORDONE : 'dharahz',
                 qs.QRY_ALARMWORDTWO : 'dharamaanz',
                 qs.QRY_ALARMWORDDISTANCE : 50 }

        queries = [self.query1,self.query2]
        self.batch = eqb.AlarmQueryBatch(queries,2,1,True)
        
        class Object(object):
            pass
        self.learner_options = Object()
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()
        self.num_rows = 1000
        self.aggregator_results = None

    
        
    def testMakeAggregator(self):
        """
        Tests the aggregator produced to see if it is 
        fully functioning. Do this by running a small
        data generation.
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
        self.assertEqual(len(self.aggregator_results),1)
        self.assertEqual(self.aggregator_results[0].keys(),['subresults'])
        self.assertEqual(len(self.aggregator_results[0]['subresults']),2)
        self.assertEqual(set(self.aggregator_results[0]['subresults'][0].keys()),
                         set(['qid','alarmword_matching_row_id_and_distances',
                          'matching_record_ids','valid']))

    
    def testRefineQueries(self):
        """
        Tests query refinement
        """
        result = {'subresults': 
                   [{'qid': 1, 'valid': True, 
                     'alarmword_matching_row_id_and_distances': [(12,14),(41,23)], 
                     'matching_record_ids': set([12,41])}, 
                    {'qid': 2, 'valid': True, 
                     'alarmword_matching_row_id_and_distances': [], 
                     'matching_record_ids': set([])}]}
        self.batch.refine_queries(result)
        refined = self.batch.produce_queries()
        self.assertEqual(len(refined), 1, self.seed_msg)
        self.assertEqual(refined[0][0],self.query1, self.seed_msg)
        self.assertLessEqual(refined[0][0][qs.QRY_LRSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertGreaterEqual(refined[0][0][qs.QRY_URSS],
                            len(refined[0][1][rdb.DBF_MATCHINGRECORDIDS]), self.seed_msg)
        self.assertEqual(refined[0][1][rdb.DBF_MATCHINGRECORDIDS], [12,41])
        self.assertEqual(refined[0][1][qs.QRY_MATCHINGRECORDCOUNTS],'1|1')
        
    
    def testProcessResultsAlreadyRefined(self):
        """
        test write_query
        """      
        result = [(self.query1, {'matching_record_counts': '1|1|2|2', 
                                 'qid': 1, 
                                 'valid': True, 
                                 'alarmword_matching_row_id_and_distances': 
                                    [(4294968035, 22), (4294967382, 19), (4294967739, 50), 
                                     (4294967695, 25), (4294968281, 25), (4294967602, 50)], 
                                 'matching_record_ids': [4294967382, 4294968035, 4294967695, 
                                                         4294968281, 4294967739, 4294967602]})]
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.batch.process_results(None, db_object, query_file, result)
        self.assertEqual(query_file.getvalue(), 
                         "1 SELECT * FROM main WHERE BYTE_DISTANCE(notes2, 'daxoz', 'devaaz') < 50\n")
        db_object.close()
        
    
    def testProcessResultsNotCallingRefine(self):
        """
        test write_query
        """    
        result = {'subresults': 
                   [{'qid': 1, 'valid': True, 
                     'alarmword_matching_row_id_and_distances': [(12,14),(41,23)], 
                     'matching_record_ids': set([12,41])}, 
                    {'qid': 2, 'valid': True, 
                     'alarmword_matching_row_id_and_distances': [], 
                     'matching_record_ids': set([])}]}
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_file = stringio.StringIO()
        self.batch.process_results(result, db_object, query_file)
        self.assertEqual(query_file.getvalue(), 
                         "1 SELECT * FROM main WHERE BYTE_DISTANCE(notes2, 'daxoz', 'devaaz') < 50\n")
        db_object.close()




        
