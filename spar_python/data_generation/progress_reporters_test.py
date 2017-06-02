# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for progress_informers.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  19 Oct 2012  jch            Original Version
# *****************************************************************


import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)



import spar_python.data_generation.progress_reporters as progress_reporters
import logging
import unittest

class RowAggregatorProgressReporterTest(unittest.TestCase): 

    

    def get_basic_ripr(self, num_rows):
        # set-up
        dummy_logger = logging.getLogger('dummy')
        ripr = \
            progress_reporters.RowAggregatorProgressReporter(dummy_logger, 
                                                              num_rows)
        return ripr

    def test_add(self):
        ripr = self.get_basic_ripr(100)
        ripr.add(1)


    def test_add_list(self):
        ripr = self.get_basic_ripr(100)
        success_result = (1, 2)
        ripr.add_list( [ success_result, success_result] )

    def test_done(self):
        ripr = self.get_basic_ripr(100)
        success_result = (1, 2)
        ripr.add_list( [ success_result, success_result] )
        ripr.done()

