# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Test for query and data generation
# *****************************************************************
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import unittest
import logging
import StringIO as stringio
import time
import re
import tempfile

import spar_python.data_generation.learn_distributions as learn_distributions 
import spar_python.common.spar_random as spar_random
import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import spar_python.data_generation.generator_workers as gw
import spar_python.query_generation.pre_test_generation as dg
import spar_python.common.aggregators.line_raw_aggregator as lra
import spar_python.report_generation.ta1.ta1_database as ta1_database   
import spar_python.report_generation.ta1.ta1_schema as ts   

                                                              
# Note: need this to make mock options
class Options(object):
    pass


class DataGenTest(unittest.TestCase):
    
    def setUp(self):
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())

        self.make_dist_holder()
        self.make_engine_options()
        self.cl_flags = Options()
        self.cl_flags.query_seed = 0
        self.cl_flags.num_processes = 1
        self.cl_flags.pickle_dir_for_intermediate_values = None


    def tearDown(self):
        os.unlink(self.line_raw_file.name)

    def make_dist_holder(self):
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

        zipcode_files = \
            [('mock_zipcodes', 
              stringio.StringIO(mock_data_files.mock_zipcodes))]
        zipcode_dict = \
            learn_distributions.learn_zipcode_dists(learner_options,
                                                    self.dummy_logger,
                                                    zipcode_files)
        
        text_files = \
            [('mock_text', 
              stringio.StringIO(mock_data_files.mock_text_files))]
        text_engine = \
            learn_distributions.train_text_engine(learner_options, 
                                                  self.dummy_logger, 
                                                  text_files)

        streets_files = \
            [('mock street file', 
              stringio.StringIO(mock_data_files.mock_street_names))]
        address_dict = \
                learn_distributions.learn_street_address_dists \
                (learner_options, 
                 self.dummy_logger, 
                 streets_files)
        
        dist_holder = \
            learn_distributions.make_distribution_holder(learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)
        self.dist_holder = dist_holder


    def make_engine_options(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        spar_random.seed(self.seed)
 
        self.num_rows = 100
 
        engine_options = gw.DataGeneratorOptions()
        engine_options.named_pipes = False
        engine_options.random_seed = self.seed
        engine_options.num_processes = 1
        engine_options.num_rows = self.num_rows 
        engine_options.row_width = 100

        self.line_raw_file = tempfile.NamedTemporaryFile(delete=False)
        lra_options_dict = {
            'file_obj'    : self.line_raw_file,
            'schema_file' : \
                os.path.join(base_dir, 
                            'spar_python/data_generation/test_schema.csv')}
        lra_aggregator = lra.LineRawHandleAggregator(**lra_options_dict)            
        engine_options.aggregators = [ lra_aggregator ]

        self.engine_options = engine_options


    def test_queries_file(self):
        # Open some files
        queries_file = stringio.StringIO()
        results_db = ta1_database.Ta1ResultsDB(':memory:')

        #
        # NOTE: update this schema file as we add more query types
        #
        test_schema_file_path = os.path.join(this_dir,
            '../../scripts-config/ta1/config/query_schemas/test.csv')
        schema_file = open(test_schema_file_path, 'rU')

        # Run the query and data generator
        dg.execute_generation(self.dist_holder, self.engine_options, 
                           self.dummy_logger, self.cl_flags,
                           schema_file,
                           queries_file,
                           results_db)




        #
        # Check the queries_file
        #
 
        queries_file_data = queries_file.getvalue()
        num_queries = queries_file_data.count('\n')
        self.assertTrue(num_queries > 10)




    def test_database(self):
        # Open some files
        queries_file = stringio.StringIO()
        results_db = ta1_database.Ta1ResultsDB(':memory:')

        #
        # NOTE: update this schema file as we add more query types
        #
        test_schema_file_path = os.path.join(this_dir,
            '../../scripts-config/ta1/config/query_schemas/test.csv')
        schema_file = open(test_schema_file_path, 'rU')

        # Run the query and data generator
        dg.execute_generation(self.dist_holder, self.engine_options, 
                           self.dummy_logger, self.cl_flags,
                           schema_file,
                           queries_file,
                           results_db)

        #
        # Check results db
        #
        for table in [ts.F2A_TABLENAME, ts.DBA_TABLENAME, ts.DBF_TABLENAME, 
                      ts.F2F_TABLENAME]:
            results_db_obj = stringio.StringIO()
            results_db.output_csv(table, results_db_obj)
            results_db_csv = results_db_obj.getvalue()
            num_lines = results_db_csv.count('\n')

            # empty tables have one line which is the header line
            golden = 1
            # we do not have any complex queries yet so this table is empty
            if table == ts.F2F_TABLENAME:
                golden = 0
            self.assertTrue(num_lines > golden)


        # Cleanup
        queries_file.close()
        results_db.close()
        schema_file.close()


    
    def test_line_raw_files(self):
        # Open some files
        queries_file = stringio.StringIO()
        results_db = ta1_database.Ta1ResultsDB(':memory:')

        #
        # NOTE: update this schema file as we add more query types
        #
        test_schema_file_path = os.path.join(this_dir,
            '../../scripts-config/ta1/config/query_schemas/test.csv')
        schema_file = open(test_schema_file_path, 'rU')

        # Run the query and data generator
        dg.execute_generation(self.dist_holder, self.engine_options, 
                           self.dummy_logger, self.cl_flags,
                           schema_file,
                           queries_file,
                           results_db)

        #
        # Check the line raw file
        #
        # expect about 100K per row
        file_handle = open(self.line_raw_file.name,'r')
        line_raw_file_data = file_handle.read()
        file_handle.close()
        num_bytes = sys.getsizeof(line_raw_file_data)
        bytes_per_row = float(num_bytes) / float(self.num_rows)
        self.assertGreater(bytes_per_row, 100 * 1000)
        self.assertLess(bytes_per_row, 105 * 1000)

        # Expect 100 INSERTS and 100 ENDINSERTS
        insert_re = re.compile("^INSERT$", re.MULTILINE)
        inserts = insert_re.findall(line_raw_file_data)
        num_inserts = len(inserts)
        self.assertEqual(num_inserts, self.num_rows)


        endinsert_re = re.compile("^ENDINSERT$", re.MULTILINE)
        endinserts = endinsert_re.findall(line_raw_file_data)
        num_endinserts = len(endinserts)
        self.assertEqual(num_endinserts, self.num_rows)



