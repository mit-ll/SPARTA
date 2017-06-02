

# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for data_generator_engine.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 Sep 2012   jch            Original version
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.data_generation.learn_distributions as learn_distributions 
import spar_python.data_generation.data_generator_engine\
       as data_generator_engine
import spar_python.common.distributions.distribution_holder \
    as distribution_holder
import spar_python.common.aggregators.counts_aggregator as ca
import spar_python.common.spar_random as spar_random
from spar_python.common.enum import Enum as Enum
import unittest
import logging
import copy
import spar_python.data_generation.spar_variables as sv
import StringIO as stringio
import learning.mock_data_files as mock_data_files
import time
import spar_python.data_generation.generator_workers as gw


#
# On to the data-generation-engine tests. First, create a distribution
# object. This is time-consuming, so I don't want to do this in setUp
#

# Note: need this to make mock options
class Options(object):
    pass

class DataGeneratorEngineTest(unittest.TestCase):


    def setUp(self):
        
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
 
        learner_options = Options()
        learner_options.verbose = False
        self.learner_options = learner_options


        engine_options = gw.DataGeneratorOptions()
        
        counts_agg = ca.CountsAggregator()
        
        engine_options.aggregators = [counts_agg]

        self.engine_options = engine_options

        dummy_logger = logging.getLogger('dummy')
        dummy_logger.addHandler(logging.NullHandler())

        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(learner_options,
                                                 dummy_logger,
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
                                                 dummy_logger,
                                                 names_files)

        zipcode_files = \
            [('mock_zipcodes', 
              stringio.StringIO(mock_data_files.mock_zipcodes))]
        zipcode_dict = \
            learn_distributions.learn_zipcode_dists(learner_options,
                                                    dummy_logger,
                                                    zipcode_files)
        
        text_files = \
            [('mock_text', 
              stringio.StringIO(mock_data_files.mock_text_files))]
        text_engine = \
            learn_distributions.train_text_engine(learner_options, 
                                                  dummy_logger, 
                                                  text_files)

        streets_files = \
            [('mock street file', 
              stringio.StringIO(mock_data_files.mock_street_names))]
        address_dict = \
                learn_distributions.learn_street_address_dists(learner_options, 
                                                               dummy_logger, 
                                                               streets_files)
        
        dist_holder = \
            learn_distributions.make_distribution_holder(learner_options,
                                                         dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)
        self.dist_holder = dist_holder
        self.data_generator_engine = \
            data_generator_engine.DataGeneratorEngine(engine_options,    
                                                      dist_holder)    




    def test_generate_row_dict(self):
        """
        Test that we can generate row dicts at all.
        """
        row_dict = self.data_generator_engine.generate_row_dict( ('000-000',0) )
        self.assertNotEqual(row_dict, {})
        self.assertIsNotNone(row_dict)

    def test_generate_same_row_dict(self):
        """
        Test that we can generate the same row_dict twice at all.
        """
        row_dict1 = \
            self.data_generator_engine.generate_row_dict( ('000-000',
                                                           13) )
        row_dict2 = \
            self.data_generator_engine.generate_row_dict( ('000-000',
                                                           13) )
        self.assertEqual(row_dict1.keys().sort(),
                         row_dict2.keys().sort(),
                         self.seed_msg)
                         
        for key in row_dict1.keys():
            self.assertEqual(row_dict1[key], row_dict2[key], self.seed_msg)


    def test_generate_same_row_dict_repeated(self):
        """
        Test that we can generate the same row_dict twice over
        multiple runs, and that this remains true as we continue to
        generate multiple rows. For historical reasons, does not 
        include fingerprint (which is covered by separate test).
        """
        num_rows = 200
        for seed in xrange(num_rows):
            row_dict1 = \
                self.data_generator_engine.generate_row_dict( ('000-000',
                                                               seed) )
            row_dict2 = \
                self.data_generator_engine.generate_row_dict( ('000-000',
                                                               seed) )
            self.assertEqual(row_dict1.keys().sort(),
                             row_dict2.keys().sort(),
                             self.seed_msg)                         
            for key in row_dict1.keys():
                self.assertEqual(row_dict1[key], row_dict2[key], self.seed_msg)


    def test_contents_sanity_check(self):
        """
        Test that the rows generated from the distribution pass some
        simple sanity checks.
        """
        
        class GenerateEverything(object):
            def fields_needed(self):
                return sv.VAR_GENERATION_ORDER
            def map(self, row_dict):
                return None
            @staticmethod
            def reduce(r1, r2):
                return None
            def done(self):
                pass
            def start(self):
                pass
        
        engine_options = gw.DataGeneratorOptions()

        gei_agg = GenerateEverything()

        engine_options.aggregators = [gei_agg]
        
        self.data_generator_engine = \
            data_generator_engine.DataGeneratorEngine(engine_options,    
                                                      self.dist_holder)    


        
        num_rows = 200
        for id in xrange(num_rows):
            id_str = '000-%d' % id
            seed = 1000 + id
            row_dict = self.data_generator_engine.generate_row_dict( (id_str,
                                                                      seed) )
            
            spar_vars_to_enum = { sv.VARS.STATE : sv.STATES,
                                 sv.VARS.SEX : sv.SEX,
                                 sv.VARS.RACE : sv.RACE,
                                 sv.VARS.MARITAL_STATUS :
                                    sv.MARITAL_STATUS,
                                 sv.VARS.GRADE_ENROLLED :
                                    sv.GRADE_ENROLLED,
                                 sv.VARS.CITIZENSHIP : sv.CITIZENSHIP,
                                 sv.VARS.MILITARY_SERVICE :
                                    sv.MILITARY_SERVICE,
                                 sv.VARS.LANGUAGE : sv.LANGUAGE}
            for spar_var in spar_vars_to_enum.keys():
                self.assertIn( row_dict[spar_var],
                               spar_vars_to_enum[spar_var].numbers_generator(),
                               self.seed_msg )

            # Note: we're even storing ints as strings in the distribution
            int_data_vars = [sv.VARS.HOURS_WORKED,
                             sv.VARS.SSN,
                             sv.VARS.WEEKS_WORKED]
            for var in int_data_vars:
                self.assertGreaterEqual( long(row_dict[var]), 0, self.seed_msg)


            str_data_vars = [sv.VARS.FIRST_NAME,
                             sv.VARS.LAST_NAME,
                             sv.VARS.ZIP_CODE,
                             sv.VARS.CITY,
                             sv.VARS.STREET_ADDRESS]
            for var in str_data_vars:
                self.assertIsInstance( row_dict[var], str, self.seed_msg)

            #
            # And now for some specialized tests.
            #

            # The following should not have spaces in them
            no_spaces = [sv.VARS.FIRST_NAME,
                         sv.VARS.LAST_NAME]
            for var in no_spaces:
                self.assertNotIn(' ', row_dict[var], self.seed_msg)


            # The following should match particular regular
            # expressions

            self.assertRegexpMatches(row_dict[sv.VARS.SSN],
                                     '\d{9}',
                                     self.seed_msg)
            self.assertRegexpMatches(row_dict[sv.VARS.STREET_ADDRESS],
                                     '\d+ [A-Z ]*(, APT \d+)?',
                                     self.seed_msg)


            # Length-testing
            # NOTE THE MAGIC CONSTANTS!
            self.assertLessEqual( len(row_dict[sv.VARS.NOTES1]), 10000, 
                                  self.seed_msg)
            self.assertLessEqual( len(row_dict[sv.VARS.NOTES2]), 2000,
                                  self.seed_msg)
            self.assertLessEqual( len(row_dict[sv.VARS.NOTES3]), 250,
                                  self.seed_msg)
            self.assertLessEqual( len(row_dict[sv.VARS.NOTES4]), 50,
                                  self.seed_msg)
            self.assertGreaterEqual( len(row_dict[sv.VARS.NOTES1]), 4000, 
                                     self.seed_msg)
            self.assertGreaterEqual( len(row_dict[sv.VARS.NOTES2]), 400,
                                     self.seed_msg)
            self.assertGreaterEqual( len(row_dict[sv.VARS.NOTES3]), 80,
                                     self.seed_msg)
            self.assertGreaterEqual( len(row_dict[sv.VARS.NOTES4]), 10,
                                     self.seed_msg)

            self.assertGreaterEqual( len(row_dict[sv.VARS.XML]), 100, 
                                     self.seed_msg)
            self.assertLessEqual( len(row_dict[sv.VARS.XML]), 10000, 
                                  self.seed_msg)


    def test_map_reduce_done1(self):
        '''
        Test that the map-reduce interface works by calling
        generate_and_aggregate_rows() on a single list of rows and 
        then checking the return value.
        '''
        num_rows = 100
        row_specs = [ ('000-000', seed) for seed in xrange(num_rows) ]
            
        aggregate_results = \
            self.data_generator_engine.generate_and_aggregate_rows( row_specs )

        goal_result = [num_rows]

        self.maxDiff = None
        self.assertListEqual(aggregate_results, goal_result)
        

    def test_map_reduce_done2(self):
        '''
        Test that the map-reduce interface works by calling
        generate_and_aggregate_rows() on multiple lists of rows and 
        then checking the return values.
        '''
        num_rows = 100
        num_iterations = 3
        aggregate_results = []
        for _ in range(num_iterations):
            row_specs = [ ('000-000', seed) for seed in xrange(num_rows) ]
            these_results = \
                self.data_generator_engine.generate_and_aggregate_rows( row_specs )
            aggregate_results.append(these_results)

        goal_result =  [[num_rows] for _ in xrange(num_iterations)]

        self.maxDiff = None
        self.assertListEqual(aggregate_results, goal_result)


    def test_select_fields1(self):
        
        class DummyAggregator(object):
            def __init__(self, fields_needed):
                self.fields = fields_needed
            def fields_needed(self):
                return self.fields
        
        aggregator1 = DummyAggregator(['b', 'c'])
        aggregator2 = DummyAggregator(['c', 'f'])
        aggregator3 = DummyAggregator(['c', 'e'])

        aggregators = [aggregator1, aggregator2, aggregator3]
        
        class DummyDistHolder(object):    
            var_order = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
           
        dh = DummyDistHolder()
        
        fields_to_gen = \
            self.data_generator_engine._select_fields_to_generate(dh,
                                                                  aggregators)
        goal = ['a', 'b', 'c', 'd', 'e', 'f']
        
        self.assertListEqual(fields_to_gen, goal)
        

    def test_select_fields2(self):
        
        class DummyAggregator(object):
            def __init__(self, fields_needed):
                self.fields = fields_needed
            def fields_needed(self):
                return self.fields
        
        aggregator = DummyAggregator([])

        aggregators = [aggregator]
        
        class DummyDistHolder(object):    
            var_order = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
           
        dh = DummyDistHolder()
        
        fields_to_gen = \
            self.data_generator_engine._select_fields_to_generate(dh,
                                                                  aggregators)
        goal = []
        
        self.assertListEqual(fields_to_gen, goal)


    def test_select_fields3(self):
        
        class DummyAggregator(object):
            def __init__(self, fields_needed):
                self.fields = fields_needed
            def fields_needed(self):
                return self.fields
        
        aggregator = DummyAggregator(['z'])

        aggregators = [aggregator]
        
        class DummyDistHolder(object):    
            var_order = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
           
        dh = DummyDistHolder()
        
        with self.assertRaises(AssertionError):
            self.data_generator_engine._select_fields_to_generate(dh,
                                                                  aggregators)
 
