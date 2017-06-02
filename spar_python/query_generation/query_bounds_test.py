# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Ariel
#  Description:        Tests for the query ids classes
# *****************************************************************

import os
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.query_generation.query_bounds as qbs
import unittest


class QueryIdsResultTest(unittest.TestCase):

    def setUp(self):
        pass
    
    def testRSSLower(self):
        qbs.set_result_set_size_range_lower('one', 10)
        qbs.set_result_set_size_range_lower('two', 100)
        qbs.set_result_set_size_range_lower('one', 1)
        qbs.set_result_set_size_range_lower('two', 1000)
        self.assertEqual(qbs.get_rss_lower('one'), 1)
        self.assertEqual(qbs.get_rss_lower('two'), 100)
    
    def testRSSUpper(self):
        qbs.set_result_set_size_range_upper('one', 10)
        qbs.set_result_set_size_range_upper('two', 100)
        qbs.set_result_set_size_range_upper('one', 1)
        qbs.set_result_set_size_range_upper('two', 1000)
        self.assertEqual(qbs.get_rss_upper('one'), 10)
        self.assertEqual(qbs.get_rss_upper('two'), 1000)
    
    def testRSStmLower(self):
        qbs.set_tm_result_set_size_range_lower('one', 10)
        qbs.set_tm_result_set_size_range_lower('two', 100)
        qbs.set_tm_result_set_size_range_lower('one', 1)
        qbs.set_tm_result_set_size_range_lower('two', 1000)
        self.assertEqual(qbs.get_tm_rss_lower('one'), 1)
        self.assertEqual(qbs.get_tm_rss_lower('two'), 100)
        
    def testRSStmUpper(self):
        qbs.set_tm_result_set_size_range_upper('one', 10)
        qbs.set_tm_result_set_size_range_upper('two', 100)
        qbs.set_tm_result_set_size_range_upper('one', 1)
        qbs.set_tm_result_set_size_range_upper('two', 1000)
        self.assertEqual(qbs.get_tm_rss_upper('one'), 10)
        self.assertEqual(qbs.get_tm_rss_upper('two'), 1000)