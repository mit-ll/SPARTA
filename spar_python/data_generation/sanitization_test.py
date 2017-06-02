# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for sanitization
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Oct 2013   jch            Original version
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import StringIO as stringio
import unittest
import logging
#import tempfile
#import multiprocessing
import time
#
#
#
#import generator_workers as gw
#import spar_python.data_generation.generate_data as generate_data
#import spar_python.common.aggregators.counts_aggregator as ca
#from spar_python.common.distributions.distribution_holder import *
#from spar_python.common.distributions.base_distributions import *
#from spar_python.common.distributions.bespoke_distributions import *
import spar_python.data_generation.spar_variables as sv
import spar_python.common.spar_random as spar_random
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import spar_python.data_generation.learn_distributions as learn_distributions
import spar_python.data_generation.sanitization as sanitization
#import spar_python.common.aggregators.base_aggregator \
#    as base_aggregator

class SanitizationTest(unittest.TestCase):

    def setUp(self):
        
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

        class Object(object):
            pass

        
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()


        # Build the distribution-holder
        learner_options = Object()

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
                learn_distributions.learn_street_address_dists(learner_options, 
                                                               self.dummy_logger, 
                                                               streets_files)

   
        
        self.dist_holder = \
            learn_distributions.make_distribution_holder(learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)



    def test_sanitize_data1(self):
        '''
        Test that we have correctly sanitized the distribution holder.
        (Note: depends on the mock-data-files possessing the dirty words.)
        '''

        # sanitize the distribution holder

        sanitization.sanitize_distribution(self.dist_holder)

        # Now test: do we ever generate the last name 'RAW'?
        last_name_dist = self.dist_holder.dist_dict[sv.VARS.LAST_NAME] 
        generated_last_names = set()
        for i in xrange(50000):
            last_name = last_name_dist.generate()
            self.assertNotEqual(last_name, 'RAW', self.seed_msg)
            generated_last_names.add(last_name)
        self.assertIn('RAWLS', generated_last_names, self.seed_msg)


        # And test: we didn't mess up the other distributions, right?
        for i in xrange(5):
            row_dict = {}
            var_order = self.dist_holder.var_order
            dist_dict = self.dist_holder.dist_dict
            for var in var_order:
                dist = dist_dict[var]
                v = dist.generate(row_dict)
                row_dict[var] = v
                
            generated_values = row_dict.values()
            self.assertNotIn('RAW', generated_values, self.seed_msg)
            
    def test_sanitize_data2(self):
        self.dist_holder.dist_dict[sv.VARS.LAST_NAME].add("her|og") # note the pipe!
        with self.assertRaises(AssertionError):
            sanitization.sanitize_distribution(self.dist_holder)
            

    def test_sanitize_data3(self):
        
        zip_code_dist = self.dist_holder.dist_dict[sv.VARS.ZIP_CODE]
        zip_code_dist.add("RAW", 1, sv.STATES.Maine)
        # Zip-codes get the re-map fix, so sanitization should work-- and
        # we should get the zipcode "FOO" in Maine
        sanitization.sanitize_distribution(self.dist_holder)

        zip_code_dist = self.dist_holder.dist_dict[sv.VARS.ZIP_CODE]
        zip_codes = zip_code_dist.support()
        self.assertNotIn("RAW", zip_codes)
        self.assertIn("FOO", zip_codes)

        foo_seen = False
        for _ in xrange(10000):
            zipcode = zip_code_dist.generate({sv.VARS.STATE:sv.STATES.Maine})
            if zipcode == "FOO":
                foo_seen = True
                break
        self.assertTrue(foo_seen)
        
        
            
        