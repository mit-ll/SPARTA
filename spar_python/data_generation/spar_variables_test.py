

# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for spar_variables.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  18 June 2013   jch            Original version
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import re

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


# Note: need this to make mock options
class Options(object):
    pass

class SparVariablesTest(unittest.TestCase):


    def setUp(self):
        
 
        learner_options = Options()
        learner_options.verbose = False
        self.learner_options = learner_options


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
        engine_options.aggregators = [GenerateEverything()]
        
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



    def test_format_row_fields(self):
        """
        Test that we format (selected fields from) a row correctly.
        """
        
        iterations = 100
        for _ in xrange(iterations):

            self.seed = int(time.time())
            self.seed_msg = "Random seed used for this test: %s" % self.seed
            self.longMessage = True

            
            row_dict = self.data_generator_engine.generate_row_dict(('000-000',
                                                                     self.seed))


            # DOB formatting:
            dob = row_dict[sv.VARS.DOB]
            converters = sv.VAR_CONVERTERS[sv.VARS.DOB]
            line_raw_format = converters.to_line_raw(dob)
            
            self.assertRegexpMatches(line_raw_format,
                                     r'\d{4}-\d{2}-\d{2}',
                                     self.seed_msg)

            # text-field formatting
            
            raw_format_regexp = re.compile('^RAW\n(\d*)\n(.*)ENDRAW$',
                                           re.DOTALL) #So that . matches \n too
            
            for field in [sv.VARS.NOTES1,
                          sv.VARS.NOTES2,
                          sv.VARS.NOTES3,
                          sv.VARS.NOTES4]:
                
                field_val = row_dict[field]
                converters = sv.VAR_CONVERTERS[field]
                field_raw = converters.to_line_raw(field_val)
                match_object = raw_format_regexp.match(field_raw)
                # test that the line-raw string has the right format
                # and the right stated length
                self.assertIsNotNone(match_object)
                stated_len = int(match_object.group(1))
                actual_len = len(match_object.group(2))
                self.assertEqual(stated_len, actual_len)
    
            # Fingerprint formatting            
            field_val = row_dict[sv.VARS.FINGERPRINT]
            converters = sv.VAR_CONVERTERS[sv.VARS.FINGERPRINT]
            field_raw = converters.to_line_raw(field_val)
            # test that the line-raw string has the right format
            # and the right stated length
            match_object = raw_format_regexp.match(field_raw)
            self.assertIsNotNone(match_object)
            stated_len = int(match_object.group(1))
            actual_len = len(match_object.group(2))
            self.assertEqual(stated_len, actual_len)
