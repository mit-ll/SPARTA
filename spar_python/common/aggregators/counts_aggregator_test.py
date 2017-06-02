# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for data_generator_engine.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 May 2013   jch            Original version
# *****************************************************************


import spar_python.common.aggregators.counts_aggregator as ca
import unittest


class CountsAggregatorTest(unittest.TestCase):
    """
    Test that the CountsAggregator class acts as expected.
    """


    def setUp(self):
        
        self.aggregator = ca.CountsAggregator()


    def test_map(self):
        return_val = self.aggregator.map('foo')
        self.assertEqual(return_val, 1)
        
    def test_reduce(self):
        reduce_val = self.aggregator.reduce(10,5)
        self.assertEqual(reduce_val, 15)
        
    def test_map_reduce(self):
        return_val1 = self.aggregator.map('foo')
        return_val2 = self.aggregator.map('foo')
        return_val3 = self.aggregator.map('foo')
                   
        reduce_val1 = self.aggregator.reduce(return_val1, return_val2)          
        self.assertEqual(reduce_val1, 2)

        reduce_val2 = self.aggregator.reduce(reduce_val1, return_val3)
        self.assertEqual(reduce_val2, 3)          

    def test_fields_needed(self):
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set())


    def test_map_reduce_row_list(self):
        
        num_rows = 100
        rows = [None] * num_rows
        agg_result = self.aggregator.map_reduce_row_list(rows)
        
        self.assertEqual(agg_result, num_rows)
