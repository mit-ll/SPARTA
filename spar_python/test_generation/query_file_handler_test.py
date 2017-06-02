# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Test for query file handler which is 
#                      used for test script and query file 
#                      generation
# *****************************************************************
import sys
import string
import os
import unittest
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.test_generation.query_file_handler as qfh

                                                              
class QueryFileHandlerTest(unittest.TestCase):
    
    def setUp(self):
        doing_select_star = True
        timing = {'performer': 'IBM1', 'cost_per_match': '0.005', 'db_num_rows': '33333', 'cat': 'P1', 'doing_select_star': '1', 'fixed_cost_per_query': '0', 'r_term': 'first_term', 'db_num_rows_desc': '10^5'}
        self.query_file_handler = qfh.QueryFileHandler("UNITTESTSPECIAL",
                                                       11122, 33333, 
                                                       "11122_33333",
                                                       "IBM1", "P1",
                                                       "eq-and", 
                                                       doing_select_star,
                                                       30, [timing], 1)

    def test_get_cat(self):
        cat = self.query_file_handler.get_cat()
        self.assertEqual(cat, "P1")

    def test_get_subcat(self):
        subcat = self.query_file_handler.get_subcat()
        self.assertEqual(subcat, "eq-and")

    def test_get_doing_select_star(self):
        val = self.query_file_handler.get_doing_select_star()
        self.assertEqual(val, True)

    def test_get_performer(self):
        val = self.query_file_handler.get_performer()
        self.assertEqual(val, "IBM1")
    
    def test_estimate_time(self):
        num_matches = 10000
        p1_num_match_first_term = 10000
        p9_matching_record_counts = None
        val = self.query_file_handler._estimate_time(num_matches,
                                                     p1_num_match_first_term,
                                                     p9_matching_record_counts)
        self.assertEqual(val, 50.0)

    def test_make_query_filename(self):
        matches_lbound = 1
        matches_ubound = 10
        description = "smoketest"
        filename = self.query_file_handler._make_query_filename(matches_lbound,
                                                                matches_ubound,
                                                                qfh.LATENCY,
                                                                description)
        self.assertEqual(filename, 
                         'UNITTESTSPECIAL/IBM1_11122_33333_1_P1_eq-and_1_10'
                         '_latency_select_star_smoketest.q')

