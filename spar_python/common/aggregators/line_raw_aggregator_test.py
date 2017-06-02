# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            omd
#  Description:        Unit tests for LineRawAggregator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Oct 2012   omd            Original version
# *****************************************************************

import unittest

import line_raw_aggregator as lra
import cStringIO

class LineRawAggregatorTest(unittest.TestCase):
    
    


    def test_fields_needed(self):
        outfile = cStringIO.StringIO()
        var_order = [2,1,0]

        aggregator = lra.LineRawHandleAggregator(outfile, var_order = var_order)
        fn = aggregator.fields_needed()
        fn_set = set(fn)
        fn_goal = set(var_order)
        self.assertSetEqual(fn_set, fn_goal)
    
    def test_text_line_mode(self):
        """Make sure we can write data if it's all just plain-text line mode
        stuff."""
        outfile = cStringIO.StringIO()
        var_order = [2,1,0]

        
        # Write out in the order 2, 1, 0. In a normal program those constants
        # would come from an enum indicating the order in which the fields
        # appear in schema
        aggregator = lra.LineRawHandleAggregator(outfile, var_order = var_order)

        aggregator.map({0: 'world', 1: 'there', 2: 'hello'})
        aggregator.map({0: 'good', 1: 'is', 2: 'this'})

        self.assertEqual(outfile.getvalue(),
                'INSERT\nhello\nthere\nworld\nENDINSERT\n'
                'INSERT\nthis\nis\ngood\nENDINSERT\n')

    def test_numbers_line_mode(self):
        """Make sure we can convert numbers correctly in line mode."""
        outfile = cStringIO.StringIO()
        var_order = [0,1]
        aggregator = lra.LineRawHandleAggregator(outfile, var_order = var_order)
        aggregator.map({0: 'hello', 1: 108})
        aggregator.map({0: 0.27, 1: '2012-10-23'})

        self.assertEqual(outfile.getvalue(),
                'INSERT\nhello\n108\nENDINSERT\n'
                'INSERT\n0.27\n2012-10-23\nENDINSERT\n')


    def test_map_reduce(self):
        """
        
        Ensure that we can use the map-reduce without error.
               
        """
        outfile = cStringIO.StringIO()
        var_order = [2,1,0]

        
        # Write out in the order 2, 1, 0. In a normal program those constants
        # would come from an enum indicating the order in which the fields
        # appear in schema
        aggregator = lra.LineRawHandleAggregator(outfile, var_order = var_order)

        return_val_1 = aggregator.map({0: 'world', 1: 'there', 2: 'hello'})
        return_val_2 = aggregator.map({0: 'good', 1: 'is', 2: 'this'})

        self.assertIsNone(return_val_1)
        self.assertIsNone(return_val_2)
        self.assertEqual(outfile.getvalue(),
                'INSERT\nhello\nthere\nworld\nENDINSERT\n'
                'INSERT\nthis\nis\ngood\nENDINSERT\n')

        reduce_val = aggregator.reduce(return_val_1, return_val_2)
        self.assertIsNone(reduce_val)


    def test_map_reduce_row_list(self):
        """
        
        Ensure that map_reduce_row_list() works as expected
        """
        outfile = cStringIO.StringIO()
        var_order = [2,1,0]

        
        # Write out in the order 2, 1, 0. In a normal program those constants
        # would come from an enum indicating the order in which the fields
        # appear in schema

        aggregator = lra.LineRawHandleAggregator(outfile, var_order = var_order)

        rows = [{0: 'world', 1: 'there', 2: 'hello'},
                {0: 'good', 1: 'is', 2: 'this'}]
        

        return_val = aggregator.map_reduce_row_list(rows)

        self.assertIsNone(return_val)
        self.assertEqual(outfile.getvalue(),
                'INSERT\nhello\nthere\nworld\nENDINSERT\n'
                'INSERT\nthis\nis\ngood\nENDINSERT\n')
