# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jill
#  Description:        Tests for query_aggregator.py
# *****************************************************************

import os
import sys
import datetime
import collections

this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import spar_python.data_generation.spar_variables as sv
import spar_python.query_generation.query_schema as qs
import spar_python.report_generation.ta1.ta1_schema as rdb
import xml.etree.cElementTree as ElementTree
from spar_python.common.distributions.xml_generator import \
    (XmlGenerator, GeneratedXml)

import spar_python.common.aggregators.query_aggregator as qa
from spar_python.common.distributions.generated_text import GeneratedText
import unittest
import copy
import spar_python.query_generation.query_bounds as qbs


def compare_results(r1, r2):
        '''
        Helper function to compare two results such that the order of the results 
        list does not matter
        '''
        result1 = copy.deepcopy(r1)
        result2 = copy.deepcopy(r2)
        result1[rdb.DBF_MATCHINGRECORDIDS] = set(result1[rdb.DBF_MATCHINGRECORDIDS])
        result2[rdb.DBF_MATCHINGRECORDIDS] = set(result2[rdb.DBF_MATCHINGRECORDIDS])
        return result1 == result2
    
class EqualityQueryAggregatorTest(unittest.TestCase):
    """
    Test that the EqualityQueryAggregator class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''
        qbs.set_result_set_size_range_upper(1, 10)
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'fname',
                   qs.QRY_VALUE : 'nick',
                   qs.QRY_ENUM : 1 }
        self.aggregator = qa.EqualityQueryAggregator(query1)


    
    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('fname'))
        self.assertEqual(self.aggregator._value, 'NICK')

    def test_map(self):
        ''' test map function '''
        row = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'nick' }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val,goal), True)

        row = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'notnick', qs.QRY_VALID: True }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val,goal), True)

    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)
        
    def test_map_reduce_no_match(self):
        ''' test map and reduce functions together when there is no match '''
        row1 = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'john' }
        row2 = { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'jill' }
        row3 = { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'sam' }
        row4 = { sv.VARS.ID : 4, sv.VARS.FIRST_NAME : 'jane' }

        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }

        map_val1 = self.aggregator.map(row1)
        self.assertEqual(map_val1, goal)
        map_val2 = self.aggregator.map(row2)
        self.assertEqual(map_val2, goal)
        map_val3 = self.aggregator.map(row3)
        self.assertEqual(map_val3, goal)
        map_val4 = self.aggregator.map(row4)
        self.assertEqual(map_val4, goal)
                   
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(reduce_val1, goal)

        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)          
        self.assertEqual(reduce_val2, goal)

        reduce_val3 = self.aggregator.reduce(reduce_val2, map_val4)
        self.assertEqual(reduce_val3, goal)

    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'nick' }
        row2 = { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'jill' }
        row3 = { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'nick' }
        row4 = { sv.VARS.ID : 4, sv.VARS.FIRST_NAME : 'nick' }
        map_val1 = self.aggregator.map(row1)
        map_val2 = self.aggregator.map(row2)
        map_val3 = self.aggregator.map(row3)
        map_val4 = self.aggregator.map(row4)
                   
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)

        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = self.aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)

    def test_map_reduce_row_list(self):
        """
        Test the map_reduce_row_list() method.
        """
        ''' test map and reduce functions together '''
        rows = [{ sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'nick' },
                { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'jill' },
                { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'nick' },
                { sv.VARS.ID : 4, sv.VARS.FIRST_NAME : 'nick' }]
                
        result_val = self.aggregator.map_reduce_row_list(rows)   
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(result_val, goal), True)
        

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.FIRST_NAME]))

    def test_match_row(self):
        ''' test match_row for different field types '''
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'foo',
                  qs.QRY_VALUE : 501 }
        aggregator = qa.EqualityQueryAggregator(query)

        # Test integer
        row1 = { sv.VARS.ID : 1, sv.VARS.FOO : 500 }
        row2 = { sv.VARS.ID : 2, sv.VARS.FOO : 501 }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)

        # Test datetime.date
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'dob',
                  qs.QRY_VALUE :  datetime.date(2013, 8, 1) }
        aggregator = qa.EqualityQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.DOB : datetime.date(2013, 8, 26) }
        row2 = { sv.VARS.ID : 2, sv.VARS.DOB : datetime.date(2013, 8, 1) }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        
        # Test enum
        german_str = sv.LANGUAGE.to_string(sv.LANGUAGE.GERMAN).upper()
        query = { qs.QRY_QID : 3,
                  qs.QRY_FIELD : 'language',
                  qs.QRY_VALUE :  german_str }
        aggregator = qa.EqualityQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.LANGUAGE : sv.LANGUAGE.DUTCH }
        row2 = { sv.VARS.ID : 2, sv.VARS.LANGUAGE : sv.LANGUAGE.GERMAN }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)


class NotEqualQATest(unittest.TestCase):
    """
    Test that the NotEqualQA class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'fname',
                   qs.QRY_VALUE : 'nick' }
        self.aggregator = qa.NotEqualQA(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('fname'))
        self.assertEqual(self.aggregator._value, 'NICK')

    def test_map(self):
        ''' test map function '''
        row = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'notnick' }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        row = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'nick' }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'notnick' }
        row2 = { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'nick' }
        row3 = { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'jill' }
        row4 = { sv.VARS.ID : 4, sv.VARS.FIRST_NAME : 'notnick' }
        map_val1 = self.aggregator.map(row1)
        map_val2 = self.aggregator.map(row2)
        map_val3 = self.aggregator.map(row3)
        map_val4 = self.aggregator.map(row4)
                   
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)

        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = self.aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)

    def test_map_reduce_row_list(self):
        rows = [{ sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'notnick' },
                { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'nick' },
                { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'jill' },
                { sv.VARS.ID : 4, sv.VARS.FIRST_NAME : 'notnick' }]

        reduce_val = self.aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)


    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.FIRST_NAME]))

    def test_match_row(self):
        ''' test match_row for different field types '''
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'foo',
                  qs.QRY_VALUE : 501 }
        aggregator = qa.NotEqualQA(query)

        # Test integer
        row1 = { sv.VARS.ID : 1, sv.VARS.FOO : 501 }
        row2 = { sv.VARS.ID : 2, sv.VARS.FOO : 500 }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)

        # Test datetime.date
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'dob',
                  qs.QRY_VALUE :  datetime.date(2013, 8, 1) }
        aggregator = qa.NotEqualQA(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.DOB : datetime.date(2013, 8, 1) }
        row2 = { sv.VARS.ID : 2, sv.VARS.DOB : datetime.date(2013, 8, 26) }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        
        # Test enum
        german_str = sv.LANGUAGE.to_string(sv.LANGUAGE.GERMAN)
        query = { qs.QRY_QID : 3,
                  qs.QRY_FIELD : 'language',
                  qs.QRY_VALUE :  german_str }
        aggregator = qa.NotEqualQA(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.LANGUAGE : sv.LANGUAGE.DUTCH }
        row2 = { sv.VARS.ID : 2, sv.VARS.LANGUAGE : sv.LANGUAGE.GERMAN }
        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , False)


class RangeQueryAggregatorTest(unittest.TestCase):
    """
    Test that the RangeQueryAggregator class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'foo',
                   qs.QRY_LBOUND : 100,
                   qs.QRY_UBOUND : 500 }
        self.aggregator = qa.RangeQueryAggregator(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('foo'))
        self.assertEqual(self.aggregator._lbound, 100)
        self.assertEqual(self.aggregator._ubound, 500)

    def test_map(self):
        ''' test map function '''
        row = { sv.VARS.ID : 1, sv.VARS.FOO : 205 }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        row = { sv.VARS.ID : 1, sv.VARS.FOO : 5 }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.FOO : 100 }
        row2 = { sv.VARS.ID : 2, sv.VARS.FOO : 5 }
        row3 = { sv.VARS.ID : 3, sv.VARS.FOO : 500 }
        row4 = { sv.VARS.ID : 4, sv.VARS.FOO : 499 }

        map_val1 = self.aggregator.map(row1)
        map_val2 = self.aggregator.map(row2)
        map_val3 = self.aggregator.map(row3)
        map_val4 = self.aggregator.map(row4)
                   
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)
        
        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = self.aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)

    def test_map_reduce_row_list(self):
        rows = [{ sv.VARS.ID : 1, sv.VARS.FOO : 100 },
               { sv.VARS.ID : 2, sv.VARS.FOO : 5 },
               { sv.VARS.ID : 3, sv.VARS.FOO : 500 },
               { sv.VARS.ID : 4, sv.VARS.FOO : 499 }]


        reduce_val = self.aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.FOO]))

    def test_match_row(self):
        ''' test match_row for different field types '''
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'fname',
                  qs.QRY_LBOUND : 'b',
                  qs.QRY_UBOUND : 'd' }
        aggregator = qa.RangeQueryAggregator(query)

        # test string
        row1 = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'a' }
        row2 = { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'b' }
        row3 = { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'c' }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row3)
        self.assertEqual(match , True)
        
        # Test datetime.date
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'dob',
                  qs.QRY_LBOUND :  datetime.date(2013, 8, 1),
                  qs.QRY_UBOUND :  datetime.date(2013, 8, 27) }
        aggregator = qa.RangeQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.DOB : datetime.date(2013, 8, 26) }
        row2 = { sv.VARS.ID : 2, sv.VARS.DOB : datetime.date(2013, 8, 1) }
        row3 = { sv.VARS.ID : 3, sv.VARS.DOB : datetime.date(2013, 9, 1) }
        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match = aggregator.match_row(row3)
        self.assertEqual(match , False)

        # Test enum
        # to match SQL behavior, compares the lowercase ENUM string value
        # german <= row <= pidgin
        german_str = sv.LANGUAGE.to_string(sv.LANGUAGE.GERMAN)
        pidgin_str = sv.LANGUAGE.to_string(sv.LANGUAGE.PIDGIN)
        query = { qs.QRY_QID : 3,
                  qs.QRY_FIELD : 'language',
                  qs.QRY_LBOUND : german_str,
                  qs.QRY_UBOUND : pidgin_str }
        aggregator = qa.RangeQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.LANGUAGE : sv.LANGUAGE.PIDGIN }
        row2 = { sv.VARS.ID : 2, sv.VARS.LANGUAGE : sv.LANGUAGE.GERMAN }
        row3 = { sv.VARS.ID : 3, sv.VARS.LANGUAGE : sv.LANGUAGE.YIDDISH }
        row4 = { sv.VARS.ID : 4, sv.VARS.LANGUAGE : sv.LANGUAGE.DUTCH }
        row5 = { sv.VARS.ID : 5, sv.VARS.LANGUAGE : sv.LANGUAGE.JAPANESE }
        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row3)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row4)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row5)
        self.assertEqual(match , True)

class GreaterThanQueryAggregatorTest(unittest.TestCase):
    """
    Test that the GreaterThanQueryAggregator class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'foo',
                   qs.QRY_VALUE : 100 }
        self.aggregator = qa.GreaterThanQueryAggregator(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('foo'))
        self.assertEqual(self.aggregator._value, 100)

    def test_map(self):
        ''' test map function '''
        row = { sv.VARS.ID : 1, sv.VARS.FOO : 205 }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        row = { sv.VARS.ID : 1, sv.VARS.FOO : 5 }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.FOO : 100 }
        row2 = { sv.VARS.ID : 2, sv.VARS.FOO : 5 }
        row3 = { sv.VARS.ID : 3, sv.VARS.FOO : 500 }
        row4 = { sv.VARS.ID : 4, sv.VARS.FOO : 499 }

        map_val1 = self.aggregator.map(row1)
        map_val2 = self.aggregator.map(row2)
        map_val3 = self.aggregator.map(row3)
        map_val4 = self.aggregator.map(row4)
                   
        # map_val2 is not a match 
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)

        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = self.aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)

    def test_map_reduce_row_list(self):
        rows = [{ sv.VARS.ID : 1, sv.VARS.FOO : 100 },
                { sv.VARS.ID : 2, sv.VARS.FOO : 5 },
                { sv.VARS.ID : 3, sv.VARS.FOO : 500 },
                { sv.VARS.ID : 4, sv.VARS.FOO : 499 }]

        reduce_val = self.aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.FOO]))

    def test_match_row(self):
        ''' test match_row for different field types '''
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'fname',
                  qs.QRY_VALUE : 'b',
                  qs.QRY_LBOUND : 'b',
                  qs.QRY_UBOUND : 'z' }
        aggregator = qa.GreaterThanQueryAggregator(query)

        # test string
        row1 = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'a' }
        row2 = { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'b' }
        row3 = { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'c' }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row3)
        self.assertEqual(match , True)
        
        # Test datetime.date
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'dob',
                  qs.QRY_VALUE :  datetime.date(2013, 8, 26) }
        aggregator = qa.GreaterThanQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.DOB : datetime.date(2013, 8, 26) }
        row2 = { sv.VARS.ID : 2, sv.VARS.DOB : datetime.date(2013, 9, 1) }
        row3 = { sv.VARS.ID : 3, sv.VARS.DOB : datetime.date(2013, 8, 1) }
        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match = aggregator.match_row(row3)
        self.assertEqual(match , False)

        # Test enum
        # to match SQL behavior, compares the lowercase ENUM string value
        # row >= german
        german_str = sv.LANGUAGE.to_string(sv.LANGUAGE.GERMAN)
        query = { qs.QRY_QID : 3,
                  qs.QRY_FIELD : 'language',
                  qs.QRY_VALUE : german_str }
        aggregator = qa.GreaterThanQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.LANGUAGE : sv.LANGUAGE.GERMAN }
        row2 = { sv.VARS.ID : 2, sv.VARS.LANGUAGE : sv.LANGUAGE.DUTCH }
        row3 = { sv.VARS.ID : 3, sv.VARS.LANGUAGE : sv.LANGUAGE.JAPANESE }

        match = aggregator.match_row(row1)
        self.assertEqual(match , True )
        match  = aggregator.match_row(row2)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row3)
        self.assertEqual(match , True)


class LessThanQueryAggregatorTest(unittest.TestCase):
    """
    Test that the LessThanQueryAggregator class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'foo',
                   qs.QRY_VALUE : 500 }
        self.aggregator = qa.LessThanQueryAggregator(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('foo'))
        self.assertEqual(self.aggregator._value, 500)

    def test_map(self):
        ''' test map function '''
        row = { sv.VARS.ID : 1, sv.VARS.FOO : 205 }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        row = { sv.VARS.ID : 1, sv.VARS.FOO : 501 }
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = self.aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.FOO : 100 }
        row2 = { sv.VARS.ID : 2, sv.VARS.FOO : 501 }
        row3 = { sv.VARS.ID : 3, sv.VARS.FOO : 500 }
        row4 = { sv.VARS.ID : 4, sv.VARS.FOO : 499 }

        map_val1 = self.aggregator.map(row1)
        map_val2 = self.aggregator.map(row2)
        map_val3 = self.aggregator.map(row3)
        map_val4 = self.aggregator.map(row4)
                   
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)

        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = self.aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)

    def test_map_reduce_row_list(self):
        rows = [{ sv.VARS.ID : 1, sv.VARS.FOO : 100 },
                { sv.VARS.ID : 2, sv.VARS.FOO : 501 },
                { sv.VARS.ID : 3, sv.VARS.FOO : 500 },
                { sv.VARS.ID : 4, sv.VARS.FOO : 499 }]

        reduce_val = self.aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)


    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.FOO]))

    def test_match_row(self):
        ''' test match_row for different field types '''
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'fname',
                  qs.QRY_VALUE : 'b',
                  qs.QRY_UBOUND : 'b',
                  qs.QRY_LBOUND : 'a' }
        aggregator = qa.LessThanQueryAggregator(query)

        # test string
        row1 = { sv.VARS.ID : 1, sv.VARS.FIRST_NAME : 'a' }
        row2 = { sv.VARS.ID : 2, sv.VARS.FIRST_NAME : 'b' }
        row3 = { sv.VARS.ID : 3, sv.VARS.FIRST_NAME : 'c' }
        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row3)
        self.assertEqual(match , False)
        
        # Test datetime.date
        query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'dob',
                  qs.QRY_VALUE :  datetime.date(2013, 8, 1) }
        aggregator = qa.LessThanQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.DOB : datetime.date(2013, 8, 26) }
        row2 = { sv.VARS.ID : 2, sv.VARS.DOB : datetime.date(2013, 8, 1) }
        row3 = { sv.VARS.ID : 3, sv.VARS.DOB : datetime.date(2013, 7, 1) }
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match = aggregator.match_row(row3)
        self.assertEqual(match , True)
        
        # Test enum
        # to match SQL behavior, compares the lowercase ENUM string value
        # row <= german
        german_str = sv.LANGUAGE.to_string(sv.LANGUAGE.GERMAN)
        query = { qs.QRY_QID : 3,
                  qs.QRY_FIELD : 'language',
                  qs.QRY_VALUE : german_str }
        aggregator = qa.LessThanQueryAggregator(query)
        row1 = { sv.VARS.ID : 1, sv.VARS.LANGUAGE : sv.LANGUAGE.GERMAN }
        row2 = { sv.VARS.ID : 2, sv.VARS.LANGUAGE : sv.LANGUAGE.DUTCH }
        row3 = { sv.VARS.ID : 3, sv.VARS.LANGUAGE : sv.LANGUAGE.JAPANESE }

        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row3)
        self.assertEqual(match , False)


class P3P4QueryAggregatorTest(unittest.TestCase):
    """
    Test that the P3P4QueryAggregator class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'notes1',
                   qs.QRY_SEARCHFOR : 'dogs',
                   qs.QRY_CAT : 'P3'}
        self.aggregator = qa.P3P4QueryAggregator(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('notes1'))
        self.assertEqual(self.aggregator._search_for, 'DOGS')

    def test_map(self):
        ''' test map function '''
        notes = GeneratedText(['Dogs', ' ', 'running', ' ', 'ALL', ' ', 'plaCes'],
                              ['DOG', None, 'RUN', None, None, None, 'PLACE'],
                              ['DOGS', ' ', 'RUNNING', ' ', 'ALL', ' ', 'PLACES'],
                              )
        row = { sv.VARS.ID : 1, sv.VARS.NOTES1 : notes }

        # Test matches on dog
        query = { qs.QRY_CAT : 'P3',
                  qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'dogs' }
        aggregator = qa.P3P4QueryAggregator(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        query[qs.QRY_SEARCHFOR] = 'cats'
        aggregator = qa.P3P4QueryAggregator(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        query[qs.QRY_CAT] = 'P4'
        query[qs.QRY_SEARCHFOR] = 'dogs'
        aggregator = qa.P3P4QueryAggregator(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        query[qs.QRY_SEARCHFOR] = 'dog'
        aggregator = qa.P3P4QueryAggregator(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        # Test matches on run
        query = { qs.QRY_CAT : 'P3',
                  qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'running' }
        aggregator = qa.P3P4QueryAggregator(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        query[qs.QRY_CAT] = 'P4'
        aggregator = qa.P3P4QueryAggregator(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        query[qs.QRY_SEARCHFOR] = 'run'
        aggregator = qa.P3P4QueryAggregator(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        notes1 = \
            GeneratedText(['Dogs', ' ', 'running', ' ', 'ALL', ' ', 'plaCes'],
                          ['DOG', None, 'RUN', None, None, None, 'PLACE'],
                          ['DOGS', ' ', 'RUNNING', ' ', 'ALL', ' ', 'PLACES'])

        notes2 = \
            GeneratedText(['Cats', ' ', 'sitting', ' ', 'ALL', ' ', 'plaCes'],
                          ['CAT', None, 'SIT', None, None, None, 'PLACE'],
                          ['CATS', ' ', 'SITTING', ' ', 'ALL', ' ', 'PLACES'])
                   
        notes3 = \
            GeneratedText(['Sam', ' ', 'plays', ' ', 'with', ' ', 'dogs'],
                          [None, None, 'PLAY', None, None, None, 'DOG'],
                          ['SAM', ' ', 'PLAYS', ' ', 'WITH', ' ', 'DOGS'])

        notes4 = \
            GeneratedText(['The', ' ', 'dogs', ' ', 'ALL', ' ', 'sit'],
                          [None, None, 'DOG', None, None, None, 'SIT'],
                          ['THE', ' ', 'DOGS', ' ', 'ALL', ' ', 'SIT'])
        
        row1 = { sv.VARS.ID : 1, sv.VARS.NOTES1 : notes1 }
        row2 = { sv.VARS.ID : 2, sv.VARS.NOTES1 : notes2 }
        row3 = { sv.VARS.ID : 3, sv.VARS.NOTES1 : notes3 }
        row4 = { sv.VARS.ID : 4, sv.VARS.NOTES1 : notes4 }

        # P3
        query = { qs.QRY_CAT : 'P3',
                  qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'dogs' }
        aggregator = qa.P3P4QueryAggregator(query)
        map_val1 = aggregator.map(row1)
        map_val2 = aggregator.map(row2)
        map_val3 = aggregator.map(row3)
        map_val4 = aggregator.map(row4)
                   
        reduce_val1 = aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)

        reduce_val2 = aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)

        # P4
        query = { qs.QRY_CAT : 'P4',
                  qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'dog' }
        aggregator = qa.P3P4QueryAggregator(query)
        map_val1 = aggregator.map(row1)
        map_val2 = aggregator.map(row2)
        map_val3 = aggregator.map(row3)
        map_val4 = aggregator.map(row4)
                   
        reduce_val1 = aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)

        reduce_val2 = aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)


    def test_map_reduce_row_list(self):
        notes1 = \
            GeneratedText(['Dogs', ' ', 'running', ' ', 'ALL', ' ', 'plaCes'],
                          ['DOG', None, 'RUN', None, None, None, 'PLACE'],
                          ['DOGS', ' ', 'RUNNING', ' ', 'ALL', ' ', 'PLACES'])

        notes2 = \
            GeneratedText(['Cats', ' ', 'sitting', ' ', 'ALL', ' ', 'plaCes'],
                          ['CAT', None, 'SIT', None, None, None, 'PLACE'],
                          ['CATS', ' ', 'SITTING', ' ', 'ALL', ' ', 'PLACES'])
                   
        notes3 = \
            GeneratedText(['Sam', ' ', 'plays', ' ', 'with', ' ', 'dogs'],
                          [None, None, 'PLAY', None, None, None, 'DOG'],
                          ['SAM', ' ', 'PLAYS', ' ', 'WITH', ' ', 'DOGS'])

        notes4 = \
            GeneratedText(['The', ' ', 'dogs', ' ', 'ALL', ' ', 'sit'],
                          [None, None, 'DOG', None, None, None, 'SIT'],
                          ['THE', ' ', 'DOGS', ' ', 'ALL', ' ', 'SIT'])
        
        rows = [{ sv.VARS.ID : 1, sv.VARS.NOTES1 : notes1 },
                { sv.VARS.ID : 2, sv.VARS.NOTES1 : notes2 },
                { sv.VARS.ID : 3, sv.VARS.NOTES1 : notes3 },
                { sv.VARS.ID : 4, sv.VARS.NOTES1 : notes4 }]

        # P3
        query = { qs.QRY_CAT : 'P3',
                  qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'dogs' }
        aggregator = qa.P3P4QueryAggregator(query)
       
        reduce_val = aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)

        # P4
        query = { qs.QRY_CAT : 'P4',
                  qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'dog' }
        aggregator = qa.P3P4QueryAggregator(query)

        reduce_val = aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.NOTES1]))

    def test_match_row(self):
        ''' test match_row '''
        notes = GeneratedText(['The', ' ', 'dogs', ' ', 'ALL', ' ', 'sit'],
                              [None, None, 'DOG', None, None, None, 'SIT'],
                              ['THE', ' ', 'DOGS', ' ', 'ALL', ' ', 'SIT'])
        row1 = { sv.VARS.ID : 1, sv.VARS.NOTES1 : notes }
        query = { qs.QRY_CAT : 'P3',
                  qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'all' }

        # P3
        aggregator = qa.P3P4QueryAggregator(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, True)

        query[qs.QRY_SEARCHFOR] = 'cats'
        aggregator = qa.P3P4QueryAggregator(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, False)

        # P4
        query[qs.QRY_CAT] = 'P4'
        query[qs.QRY_SEARCHFOR] = 'all'
        aggregator = qa.P3P4QueryAggregator(query)
        match  = aggregator.match_row(row1)
        self.assertEqual(match, False)
        
        query[qs.QRY_SEARCHFOR] = 'dog'
        aggregator = qa.P3P4QueryAggregator(query)
        match  = aggregator.match_row(row1)
        self.assertEqual(match, True)
        

class SearchQABaseTest(unittest.TestCase):
    """
    Test that the SearchQABaseTest class acts as expected 
    Since the is_match functions are tested separately 
    this test will just check for match and no match.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'notes1',
                   qs.QRY_SEARCHFOR : 'dogs' }
        self.aggregator = qa.P7InitialQA(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('notes1'))
        self.assertEqual(self.aggregator._value, 'DOGS')

    def test_map(self):
        ''' test map function '''
        notes = \
            GeneratedText(['Dogs', ' ', 'running', ' ', 'ALL', ' ', 'plaCes'],
                          ['DOG',  None, 'RUN', None, None,  None, 'PLACE'],
                          ['DOGS', ' ', 'RUNNING', ' ', 'ALL', ' ', 'PLACES'])
        row = { sv.VARS.ID : 1, sv.VARS.NOTES1 : notes }

        # Test match
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'ogs running all places' }
        aggregator = qa.P7InitialQA(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        # Test no match
        query[qs.QRY_SEARCHFOR] = 'ogs running all placex'
        aggregator = qa.P7InitialQA(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

 
    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        notes1 = \
            GeneratedText(['fred', ' ', 'wIth', ' ', 'dOgs', ' ', 'today'],
                          [None, None, None, None, 'DOG', None, 'TODAY'],
                          ['FRED', ' ', 'WITH', ' ', 'DOGS', ' ', 'TODAY'],)
        notes2 = \
            GeneratedText(['Cats', ' ' , 'sitting', ' ', 'ALL', ' ', 'plaCes'],
                          ['CAT', None, 'SIT', None, None, None, 'PLACE'],
                          ['CATS', ' ' , 'SITTING', ' ', 'ALL', ' ', 'PLACES'],)
        notes3 = \
            GeneratedText(['Sam', ' ', 'plays', ' ', 'with', ' ', 'dogs', ' ', 'today'],
                          [None, None, 'PLAY', None, None, None, 'DOG', None, 'TODAY'],
                          ['SAM', ' ', 'PLAYS', ' ', 'WITH', ' ', 'DOGS', ' ', 'TODAY'])
        notes4 = \
            GeneratedText(['Cats', ' ', 'sit', ' ', 'WITH', ' ', 'dogs', ' ', 'today'],
                          ['CAT', None, 'SIT', None, None, None, 'DOG', None, 'TODAY'],
                          ['CATS', ' ', 'SIT', ' ', 'WITH', ' ', 'DOGS', ' ', 'TODAY'])
        
        row1 = { sv.VARS.ID : 1, sv.VARS.NOTES1 : notes1 }
        row2 = { sv.VARS.ID : 2, sv.VARS.NOTES1 : notes2 }
        row3 = { sv.VARS.ID : 3, sv.VARS.NOTES1 : notes3 }
        row4 = { sv.VARS.ID : 4, sv.VARS.NOTES1 : notes4 }

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'with dogs' }
        aggregator = qa.P7BothQA(query)
        map_val1 = aggregator.map(row1)
        map_val2 = aggregator.map(row2)
        map_val3 = aggregator.map(row3)
        map_val4 = aggregator.map(row4)
                   
        reduce_val1 = aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(compare_results(reduce_val1, map_val1), True)

        reduce_val2 = aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val2, goal), True)

        reduce_val3 = aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val3, goal), True)

    def test_map_reduce_row_list(self):
        notes1 = \
            GeneratedText(['fred', ' ', 'wIth', ' ', 'dOgs', ' ', 'today'],
                          [None, None, None, None, 'DOG', None, 'TODAY'],
                          ['FRED', ' ', 'WITH', ' ', 'DOGS', ' ', 'TODAY'],)
        notes2 = \
            GeneratedText(['Cats', ' ' , 'sitting', ' ', 'ALL', ' ', 'plaCes'],
                          ['CAT', None, 'SIT', None, None, None, 'PLACE'],
                          ['CATS', ' ' , 'SITTING', ' ', 'ALL', ' ', 'PLACES'],)
        notes3 = \
            GeneratedText(['Sam', ' ', 'plays', ' ', 'with', ' ', 'dogs', ' ', 'today'],
                          [None, None, 'PLAY', None, None, None, 'DOG', None, 'TODAY'],
                          ['SAM', ' ', 'PLAYS', ' ', 'WITH', ' ', 'DOGS', ' ', 'TODAY'])
        notes4 = \
            GeneratedText(['Cats', ' ', 'sit', ' ', 'WITH', ' ', 'dogs', ' ', 'today'],
                          ['CAT', None, 'SIT', None, None, None, 'DOG', None, 'TODAY'],
                          ['CATS', ' ', 'SIT', ' ', 'WITH', ' ', 'DOGS', ' ', 'TODAY'])
        
        rows = [{ sv.VARS.ID : 1, sv.VARS.NOTES1 : notes1 },
                { sv.VARS.ID : 2, sv.VARS.NOTES1 : notes2 },
                { sv.VARS.ID : 3, sv.VARS.NOTES1 : notes3 },
                { sv.VARS.ID : 4, sv.VARS.NOTES1 : notes4 }]

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'with dogs' }
        aggregator = qa.P7BothQA(query)

        reduce_val = aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertEqual(compare_results(reduce_val, goal), True)

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.NOTES1]))

    def test_match_row(self):
        ''' test match_row '''
        notes = \
            GeneratedText(['The', ' ', 'dogs', ' ', 'ALL', ' ', 'sit'],
                          [None, None, 'DOG', None, None, None, 'SIT'],
                          ['THE', ' ', 'DOGS', ' ', 'ALL', ' ', 'SIT'],
                          )
        row1 = { sv.VARS.ID : 1, sv.VARS.NOTES1 : notes }
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'notes1',
                  qs.QRY_SEARCHFOR : 'the dogs all s' }

        # match
        aggregator = qa.P7FinalQA(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, True)

        # not match
        query[qs.QRY_SEARCHFOR] = 'the dogs sometimes sit'
        aggregator = qa.P7FinalQA(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, False)




class SearchNumQABaseTest(unittest.TestCase):
    """
    Test that the SearchNumQABase class acts as expected 
    Since the is_match functions are tested separately
    this test will just check for match and no match.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'address',
                   qs.QRY_SEARCHFOR : 'dogs',
                   qs.QRY_SEARCHDELIMNUM : 1}
        self.aggregator = qa.SearchInitialNumQA(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('address'))
        self.assertEqual(self.aggregator._value, 'DOGS')
        self.assertEqual(self.aggregator._num, 1)

    def test_map(self):
        ''' test map function '''
        row = { sv.VARS.ID : 1, 
                sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }

        # Test match
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHDELIMNUM: 1,
                  qs.QRY_SEARCHFOR : '8021 Wilshire drive Eas' }
        aggregator = qa.SearchFinalNumQA(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertEqual(compare_results(map_val, goal), True)

        # Test no match
        query[qs.QRY_SEARCHFOR] = '8021 Wilshire drive Wes'
        aggregator = qa.SearchFinalNumQA(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertTrue(compare_results(map_val, goal))

 
    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''        
        row1 = { sv.VARS.ID : 1, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        row2 = { sv.VARS.ID : 2, 
                 sv.VARS.STREET_ADDRESS : '8121 Wilshire Drive East' }
        row3 = { sv.VARS.ID : 3, 
                 sv.VARS.STREET_ADDRESS : '2021 Wilshire Drive East' }
        row4 = { sv.VARS.ID : 4, 
                 sv.VARS.STREET_ADDRESS : '3021 Wilshire Drive East' }

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHDELIMNUM : 1,
                  qs.QRY_SEARCHFOR : '021 Wilshire drive East' }
        aggregator = qa.SearchInitialNumQA(query)
        map_val1 = aggregator.map(row1)
        map_val2 = aggregator.map(row2)
        map_val3 = aggregator.map(row3)
        map_val4 = aggregator.map(row4)
                   
        reduce_val1 = aggregator.reduce(map_val1, map_val2)          
        self.assertTrue(compare_results(reduce_val1, map_val1))

        reduce_val2 = aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val2, goal))

        reduce_val3 = aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val3, goal))

    def test_map_reduce_row_list(self):
        row1 = { sv.VARS.ID : 1, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        row2 = { sv.VARS.ID : 2, 
                 sv.VARS.STREET_ADDRESS : '8121 Wilshire Drive East' }
        row3 = { sv.VARS.ID : 3, 
                 sv.VARS.STREET_ADDRESS : '2021 Wilshire Drive East' }
        row4 = { sv.VARS.ID : 4, 
                 sv.VARS.STREET_ADDRESS : '3021 Wilshire Drive East' }

        rows = [row1, row2, row3, row4]

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHDELIMNUM : 1,
                  qs.QRY_SEARCHFOR : '021 Wilshire drive East' }
        aggregator = qa.SearchInitialNumQA(query)

        reduce_val = aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.STREET_ADDRESS]))

    def test_match_row(self):
        ''' test match_row '''
        row1 = { sv.VARS.ID : 1,
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHDELIMNUM: 1,
                  qs.QRY_SEARCHFOR : '021 Wilshire drive East' }

        # match
        aggregator = qa.SearchInitialNumQA(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, True)

        # not match
        query[qs.QRY_SEARCHFOR] = '021 Wilshire drive West'
        aggregator = qa.SearchInitialNumQA(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, False)



class SearchMultipleNumQABaseTest(unittest.TestCase):
    """
    Test that the SearchMultipleNumQABase class acts as expected.
    Since the is_match functions are tested separately
    this test will just check for match and no match.
    """

    def setUp(self):
        ''' initialize test '''
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'address',
                   qs.QRY_SEARCHDELIMNUM : 1,
                   qs.QRY_SEARCHFORLIST : ['dogs', 'cats'] }
        self.aggregator = qa.SearchMultipleNumQA(query1)

    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('address'))
        self.assertEqual(self.aggregator._value_list, ['DOGS', 'CATS'])
        self.assertEqual(self.aggregator._num, 1)

    def test_map(self):
        ''' test map function '''
        row = { sv.VARS.ID : 1, 
                sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        # Test match
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                   qs.QRY_SEARCHDELIMNUM : 19,
                   qs.QRY_SEARCHFORLIST : ['8', 'East'] }
        aggregator = qa.SearchFinalMultipleNumQA(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertTrue(compare_results(map_val, goal))

        # Test no match  (nothing missing)
        query[qs.QRY_SEARCHFORLIST] = ['8021 Wilshirex ', 'drive East']
        aggregator = qa.SearchBothMultipleNumQA(query)
        goal =  { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [],  qs.QRY_VALID: True }
        map_val = aggregator.map(row)
        self.assertTrue(compare_results(map_val, goal))

 
    def test_reduce(self):
        ''' test reduce function '''
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [5], qs.QRY_VALID: True }
        reduce_val = self.aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 5], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''        
        row1 = { sv.VARS.ID : 1, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        row2 = { sv.VARS.ID : 2, 
                 sv.VARS.STREET_ADDRESS : '8125 Wilshire Drive East' }
        row3 = { sv.VARS.ID : 3, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        row4 = { sv.VARS.ID : 4, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHFORLIST : ['21', 'Wilshire', 'Drive East'],
                  qs.QRY_SEARCHDELIMNUM : 1 }
        aggregator = qa.SearchInitialMultipleNumQA(query)
        map_val1 = aggregator.map(row1)
        map_val2 = aggregator.map(row2)
        map_val3 = aggregator.map(row3)
        map_val4 = aggregator.map(row4)
                   
        reduce_val1 = aggregator.reduce(map_val1, map_val2)          
        self.assertTrue(compare_results(reduce_val1, map_val1))

        reduce_val2 = aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val2, goal))

        reduce_val3 = aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val3, goal))

    def test_map_reduce_row_list(self):
        row1 = { sv.VARS.ID : 1, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        row2 = { sv.VARS.ID : 2, 
                 sv.VARS.STREET_ADDRESS : '8125 Wilshire Drive East' }
        row3 = { sv.VARS.ID : 3, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        row4 = { sv.VARS.ID : 4, 
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }

        rows = [row1, row2, row3, row4]

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHFORLIST : ['21', 'Wilshire', 'Drive East'],
                  qs.QRY_SEARCHDELIMNUM : 1 }
        aggregator = qa.SearchInitialMultipleNumQA(query)
        
        reduce_val = aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.STREET_ADDRESS]))

    def test_match_row(self):
        ''' test match_row '''
        row1 = { sv.VARS.ID : 1,
                 sv.VARS.STREET_ADDRESS : '8021 Wilshire Drive East' }
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHFORLIST : ['8021 Wilsh', 'East'] ,
                  qs.QRY_SEARCHDELIMNUM : 10}

        # match
        aggregator = qa.SearchMultipleNumQA(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, True)

        # not match
        query[qs.QRY_SEARCHFORLIST] = ['West']
        aggregator = qa.SearchMultipleNumQA(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match, False)




class SearchIsMatchTest(unittest.TestCase):
    """
    Test different implementations of is_match
    """

    # 
    # SearchQABase Base Class
    # 

    # P7InitialQA
    def test_is_match_p7_initial(self):
        ''' test specific version of is_match '''
        # p7 initial
        data = "aanron"
        test_values = [ ('anron', True), ('nron', True), ('n', True), 
                        ('aanron',True), ('samantha', False), 
                        ('sam', False) ]
        for (value, answer) in test_values:
            is_match_fn = qa.P7InitialQA.is_match
            self.assertEqual(is_match_fn(value, data), answer)

    # P7FinalQA
    def test_is_match_p7_final(self):
        ''' test specific version of is_match '''
        # P7 final
        data = "aanron"
        test_values = [ ('aanron', True), ('aaanron', False), 
                        ('aanro', True), ('aanr', True), ('a', True), 
                        ('aa', True), ('Samantha', False), ('Sam', False) ]
        for (value, answer) in test_values:
            is_match_fn = qa.P7FinalQA.is_match
            self.assertEqual(is_match_fn(value, data), answer)

    # P7BothQA
    def test_is_match_p7_both(self):
        ''' test specific version of is_match '''
        # P7 both (provide middle)
        data = "aanron"
        test_values = [ ('aanron', True), ('aaanron', False), 
                        ('aanro', True), ('aanr', True), ('anro', True),
                        ('an', True), ('r', True), ('n', True),
                        ('x', False) ]
        for (value, answer) in test_values:
            is_match_fn = qa.P7BothQA.is_match
            self.assertEqual(is_match_fn(value, data), answer)



    # 
    # SearchNumQABase Base Class
    # 

    # SearchInitialNumQA
    def test_is_match_initial_num(self):
        ''' test specific version of is_match '''
        data = "aanron"
        test_values = [ ('anron', 1, True), ('nron', 1, False), 
                        ('n', 1, False), 
                        ('aanron', 1, False), ('samantha', 1, False), 
                        ('sam', 1, False),
                        ('nron', 2, True), ('ron', 1, False), ('n', 1, False), 
                        ('aanron', 2, False), ('samantha', 20, False), 
                        ('sam', 20, False)]
        is_match_fn = qa.SearchInitialNumQA.is_match
        for (value, num, answer) in test_values:
            self.assertEqual(is_match_fn(value, num, data), answer) 

    # SearchFinalNumQA
    def test_is_match_final_num(self):
        ''' test specific version of is_match '''
        data = "aanron"
        test_values = [ ('aanron', 1, False), ('aaanron', 1, False),
                        ('aanro', 1, True), ('aanr', 1, False), 
                        ('a', 1, False), 
                        ('aa', 1, False), ('Samantha', 1, False), 
                        ('Sam', 1, False),
                        ('aanron', 2, False), ('aaanron', 2, False),
                        ('aanr', 2, True), ('aanro', 2, False), 
                        ('a', 2, False), 
                        ('aa', 2, False), ('Samantha', 20, False), 
                        ('Sam', 20, False) ]
        is_match_fn = qa.SearchFinalNumQA.is_match
        for (value, num, answer) in test_values:
            self.assertEqual(is_match_fn(value, num, data), answer)



    #
    # SearchMultipleNumQABase Base Class and methods:
    #   multiple_num_helper reverse_multiple_num_helper
    #

    # Test multiple_num_helper
    def test_is_match_multiple_num_helper(self):
        ''' test specific version of is_match '''
        data = "428 Wilshire Drive East"
        test_values = [ \
            (['428 Wilshire Drive','ast'], 2, (True, False)), 
            (['428 Wilshire Drive','ast'], 1, (False, False)), 
            
            (['1428 Wilshire Drive','ast'], 2, (False, False)), 
            (['428 Wilshire Drive','astt'], 2, (False, False)), 
            (['428 Wilshire Drive','as'], 2, (True, True)), 
            
            (['428 Wilshir', 'Drive', 'ast'], 2, (True, False)), 
            (['428 Wilshir', 'Drive', 'ast'], 1, (False, False)), 
            (['428 Wilshi', 'Driv', 'ast'], 3, (True, False)), 
            
            (['428 Wilshire Drive','ast West'], 2, (False, False)), 
            (['428 Wilshire Driveway','ast'], 2, (False, False)), 
            
            (['4', ' Wilshire','rive','ast'], 2, (True, False)), 

            (['428 Wilshire Drive in the beautiful part','ast'], 2, \
                 (False, False)), 
            (['428 Wilshire Drive','somewhere in the forest of trees ast'], \
                 2, (False, False)), 
            (['428 Wilshire Drive','ast'], 30, (False, False)) ]
        is_match_fn = qa.SearchMultipleNumQABase.multiple_num_helper
        for (value_list, num, answer) in test_values:
            self.assertEqual(is_match_fn(value_list, num, data), answer)

    # Test reverse_multiple_num_helper
    def test_is_match_reverse_multiple_num_helper(self):
        ''' test specific version of is_match '''
        data = "428 Wilshire Drive East"
        test_values = [ \
            (['428 Wilshire Drive','ast'], 2, (True, False)), 
            (['428 Wilshire Drive','ast'], 1, (False, False)), 
            
            (['1428 Wilshire Drive','ast'], 2, (False, False)), 
            (['428 Wilshire Drive','astt'], 2, (False, False)), 
            (['8 Wilshire Drive','ast'], 2, (True, True)), 
            
            (['428 Wilshir', 'Drive', 'ast'], 2, (True, False)), 
            (['428 Wilshir', 'Drive', 'ast'], 1, (False, False)), 
            (['428 Wilshi', 'Driv', 'ast'], 3, (True, False)), 
            
            (['428 Wilshire Drive','ast West'], 2, (False, False)), 
            (['428 Wilshire Driveway','ast'], 2, (False, False)), 
            
            (['4', ' Wilshire','rive','ast'], 2, (True, False)), 

            (['428 Wilshire Drive in the beautiful part','ast'], 2, \
                 (False, False)), 
            (['428 Wilshire Drive','somewhere in the forest of trees ast'], 2, \
                 (False, False)), 
            (['428 Wilshire Drive','ast'], 30, (False, False)) ]
        is_match_fn = qa.SearchMultipleNumQABase.reverse_multiple_num_helper
        for (value_list, num, answer) in test_values:
            self.assertTrue(is_match_fn(value_list, num, data), answer)

    # SearchMultipleNumQA
    def test_is_match_multiple_num(self):
        ''' test specific version of is_match '''
        data = "aanron"
        test_values = [ (['aanron', 'n'], False), 
                        (['aaanron', 'ron'], False), 
                        (['aanr', 'n'], True), 
                        (['aan', 'n'], False), 
                        (['aan', 'on'], True), (['a', 'nron'], True), 
                        (['aan', 'o'], False), (['a', 'nro'], False), 
                        (['aan', 'nn'], False), (['aan', 'nn'], False), 
                        (['b', 'nron'], False)]
        is_match_fn = qa.SearchMultipleNumQA.is_match
        for (value_list, answer) in test_values:
            assert (is_match_fn(value_list, 1, data) == answer)

    # SearchBothMultipleNumQA
    def test_is_match_both_multiple_num(self):
        ''' test specific version of is_match '''
        data = "428 Wilshire Drive East"
        test_values = [ \
            (['428 Wilshire Drive East'], 2, True), 
            (['428 Wilshire Drive West'], 2, False), 

            (['428 Wilshire Drive','ast'], 2, True), 
            (['428 Wilshire Drive','ast'], 1, False), 
            
            (['28 Wilshire Drive','ast'], 2, True), 
            (['428 Wilshire Drive','as'], 2, True), 
            (['1428 Wilshire Drive','ast'], 2, False), 
            (['428 Wilshire Drive','astt'], 2, False), 
            
            (['428 Wilshir', 'Drive', 'ast'], 2, True), 
            (['428 Wilshir', 'Drive', 'ast'], 1, False), 
            (['428 Wilshi', 'Driv', 'ast'], 3, True), 
            
            (['28 Wilshi', 'Driv', 'ast'], 3, True), 
            (['428 Wilshi', 'Driv', 'as'], 3, True), 
            (['28 Wilshi', 'Driv', 'as'], 3, True), 
            
            (['428 Wilshire Drive','ast West'], 2, False), 
            (['428 Wilshire Driveway','ast'], 2, False), 
            
            (['4', ' Wilshire','rive','ast'], 2, True), 
            
            (['428 Wilshire Drive in the beautiful part','ast'], 2, False), 
            (['428 Wilshire Drive','somewhere in the forest of trees ast'], \
                 2, False), 
            (['428 Wilshire Drive','ast'], 30, False) ]
        is_match_fn = qa.SearchBothMultipleNumQA.is_match
        for (value_list, num, answer) in test_values:
            assert (is_match_fn(value_list, num, data) == answer)

    # SearchInitialMultipleNumQA
    def test_is_match_initial_multple_num(self):
        ''' test specific version of is_match '''
        data = "aanron"
        test_values = [ (['aanron'], 1, True), 
                        (['a','n', 'on'], 1, True), 
                        (['aa', 'on'], 2, True), 
                        (['an', 'n'], 2, True), 
                        (['n', 'on'], 1, True), 
                        (['n', 'n'], 2, True), 
                        (['a','n', 'x'], 1, False), 
                        (['aanron', 'n'], 1, False), 
                        (['r', 'n'], 1, True), 
                        (['aan', 'on'], 1, True),
                        (['aan', 'o'], 20, False),
                        (['aan', 'nn'], 2, False),
                        (['b', 'nron'], 1, False)]
        is_match_fn = qa.SearchInitialMultipleNumQA.is_match
        for (value_list, num, answer) in test_values:
            assert (is_match_fn(value_list, num, data) == answer)

    # SearchFinalMultipleNumQA
    def test_is_match_final_multiple_num(self):
        ''' test specific version of is_match '''
        data = "aanron"
        test_values = [ (['aanron'], 1, True), 
                        (['a','n', 'o'], 1, True), 
                        (['aan', 'o'], 1, True), 
                        (['aan', 'n'], 2, True), 
                        (['aa', 'n'], 3, True), 
                        (['a','n', 'x'], 1, False), 
                        (['aanron', 'n'], 1, False), 
                        (['a', 'on'], 1, False),
                        (['a', 'o'], 20, False),
                        (['a', 'nn'], 2, False),
                        (['n', 'nr'], 1, False)]
        is_match_fn = qa.SearchFinalMultipleNumQA.is_match
        for (value_list, num, answer) in test_values:
            assert (is_match_fn(value_list, num, data) == answer)
    









class GenChooseAggregatorTest(unittest.TestCase):
    """
    Test that the GenChooseAggregator class acts as expected.
    """

    def setUp(self):
        query1 = { qs.QRY_QID : 1,
                   qs.QRY_FIELD : 'fname',
                   qs.QRY_VALUE : 'nick' }
        eqAgg1 = qa.EqualityQueryAggregator(query1)

        query2 = { qs.QRY_QID : 2,
                   qs.QRY_FIELD : 'fname',
                   qs.QRY_VALUE : 'jane' }
        eqAgg2 = qa.EqualityQueryAggregator(query2)

        query3 = { qs.QRY_QID : 3,
                   qs.QRY_FIELD : 'lname',
                   qs.QRY_VALUE : 'smith' }
        eqAgg3 = qa.EqualityQueryAggregator(query3)

        query4 = { qs.QRY_QID : 4,
                   qs.QRY_FIELD : 'lname',
                   qs.QRY_VALUE : 'jones' }
        eqAgg4 = qa.EqualityQueryAggregator(query4)
        self.aggs = [ eqAgg1, eqAgg2, eqAgg3, eqAgg4 ]
        self.aggregator = qa.GenChooseAggregator(self.aggs)

        self.rows = {}
        self.rows[10] = { sv.VARS.ID : 10, 
                          sv.VARS.FIRST_NAME : 'jill',
                          sv.VARS.LAST_NAME : 'baker'}
        self.rows[11] = { sv.VARS.ID : 11, 
                          sv.VARS.FIRST_NAME : 'nick',
                          sv.VARS.LAST_NAME : 'jones'}
        self.rows[12] = { sv.VARS.ID : 12, 
                          sv.VARS.FIRST_NAME : 'jane',
                          sv.VARS.LAST_NAME : 'jones'}

        #
        # Map Answers
        #
        # For row ID=10
        self.map_golden = {}
        self.map_golden[10] = \
            { qs.QRY_SUBRESULTS : [ \
                { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                { qs.QRY_QID : 2, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                { qs.QRY_QID : 3, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                { qs.QRY_QID : 4, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True } ] }
            
        # For row ID=11        
        self.map_golden[11] = \
            { qs.QRY_SUBRESULTS: [ \
                { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [11], qs.QRY_VALID: True },
                { qs.QRY_QID : 2, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                { qs.QRY_QID : 3, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                { qs.QRY_QID : 4, rdb.DBF_MATCHINGRECORDIDS : [11], qs.QRY_VALID: True } ] }
        
        # For row ID=12
        self.map_golden[12] = \
            { qs.QRY_SUBRESULTS: [ \
                { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                { qs.QRY_QID : 2, rdb.DBF_MATCHINGRECORDIDS : [12], qs.QRY_VALID: True },
                { qs.QRY_QID : 3, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                { qs.QRY_QID : 4, rdb.DBF_MATCHINGRECORDIDS : [12], qs.QRY_VALID: True } ] }
        
        #
        # Reduce Results
        #
        self.reduce_golden = [] 
        # For row IDs 10 and 11
        self.reduce_golden.append( \
            { qs.QRY_SUBRESULTS: [ \
                    { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [11], qs.QRY_VALID: True },
                    { qs.QRY_QID : 2, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                    { qs.QRY_QID : 3, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                    { qs.QRY_QID : 4, rdb.DBF_MATCHINGRECORDIDS : [11], qs.QRY_VALID: True } ] } )

        # For row IDs 10, 11 and 12
        self.reduce_golden.append( \
            { qs.QRY_SUBRESULTS: [ \
                    { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [11], qs.QRY_VALID: True },
                    { qs.QRY_QID : 2, rdb.DBF_MATCHINGRECORDIDS : [12], qs.QRY_VALID: True },
                    { qs.QRY_QID : 3, rdb.DBF_MATCHINGRECORDIDS : [], qs.QRY_VALID: True },
                    { qs.QRY_QID : 4, rdb.DBF_MATCHINGRECORDIDS : [11,12], qs.QRY_VALID: True } ] } )


    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(len(self.aggs), 4)

    def test_map(self):
        ''' test map function '''
        for row_num in [10, 11, 12]:
            map_val = self.aggregator.map(self.rows[row_num])
            self.assertEqual(map_val, self.map_golden[row_num])

    def test_reduce(self):
        ''' test reduce function '''
        reduce_val = self.aggregator.reduce(self.map_golden[10], 
                                            self.map_golden[11])
        self.assertEqual(reduce_val, self.reduce_golden[0])

        reduce_val = self.aggregator.reduce(reduce_val, self.map_golden[12])
        self.assertEqual(reduce_val, self.reduce_golden[1])
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''        

        map_val1 = self.aggregator.map(self.rows[10])
        map_val2 = self.aggregator.map(self.rows[11])
        map_val3 = self.aggregator.map(self.rows[12])
                   
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(reduce_val1, self.reduce_golden[0])

        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)
        self.assertEqual(reduce_val2, self.reduce_golden[1])


    def test_map_reduce_row_list(self):
    
        rows = [self.rows[i] for i in [10, 11]]
        reduce_val = self.aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val, self.reduce_golden[0])

        rows = [self.rows[i] for i in [10, 11, 12]]
        reduce_val = self.aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val, self.reduce_golden[1])

    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        self.assertSetEqual(set(fn), 
                            set([sv.VARS.LAST_NAME, sv.VARS.FIRST_NAME]))





class SearchFishingAggregatorTest(unittest.TestCase):
    """
    Test that the SearchFishingQA class acts as expected.
    """

    def setUp(self):

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'address',
                  qs.QRY_SEARCHFOR : 'Peach' }
        self.aggregator = qa.SearchFishingQA(query)

        self.rows = {}
        self.rows[10] = { sv.VARS.ID : 10, 
                          sv.VARS.STREET_ADDRESS : 'Jill Lane' }
        self.rows[11] = { sv.VARS.ID : 11, 
                          sv.VARS.STREET_ADDRESS : '1 Peach Road' }
        self.rows[12] = { sv.VARS.ID : 12, 
                          sv.VARS.STREET_ADDRESS : '44 Peach Tree Lane' }
        self.rows[13] = { sv.VARS.ID : 13, 
                          sv.VARS.STREET_ADDRESS : '1 peach road' }

        #
        # Map Answers
        #
        # For row ID=10
        self.map_golden = {}
        self.map_golden[10] = \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : collections.defaultdict(list), 
              qs.QRY_VALID: True } 
            
        # For row ID=11        
        dict11 = collections.defaultdict(list)
        dict11['1 PEACH ROAD'] = [11]
        self.map_golden[11] = \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict11, qs.QRY_VALID: True}
        
        # For row ID=12
        dict12 = collections.defaultdict(list)
        dict12['44 PEACH TREE LANE'] = [12]
        self.map_golden[12] = \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict12, qs.QRY_VALID: True}

        # For row ID=13
        dict13 = collections.defaultdict(list)
        dict13['1 PEACH ROAD'] = [13]
        self.map_golden[13] = \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict13, qs.QRY_VALID: True}


        #
        # Reduce Results
        #
        self.reduce_golden = [] 
        # For row IDs 10 and 11
        dict14 = collections.defaultdict(list)
        dict14['1 PEACH ROAD'] = [11]
        self.reduce_golden.append( \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict14, qs.QRY_VALID: True } )

        # For row IDs 10, 11 and 12
        dict15 = collections.defaultdict(list)
        dict15['1 PEACH ROAD'] = [11]
        self.reduce_golden.append( \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict15, qs.QRY_VALID: True } )

        # For row IDs 10, 11, 12 and 13
        dict16 = collections.defaultdict(list)
        dict16['1 PEACH ROAD'] = [11,13]
        self.reduce_golden.append( \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict16, qs.QRY_VALID: True } )


    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.aggregator._qid, 1)
        self.assertEqual(self.aggregator._field, sv.sql_name_to_enum('address'))
        self.assertEqual(self.aggregator._value, 'PEACH')

    def test_map(self):
        ''' test map function '''
        for row_num in [10, 11, 12, 13]:
            map_val = self.aggregator.map(self.rows[row_num])
            self.assertEqual(map_val, self.map_golden[row_num])

    def test_reduce(self):
        ''' test reduce function '''
        reduce_val = self.aggregator.reduce(self.map_golden[10], 
                                            self.map_golden[11])
        self.assertEqual(reduce_val, self.reduce_golden[0])

        reduce_val = self.aggregator.reduce(reduce_val, self.map_golden[12])
        self.assertEqual(reduce_val, self.reduce_golden[1])
        
        reduce_val = self.aggregator.reduce(reduce_val, self.map_golden[13])
        self.assertEqual(reduce_val, self.reduce_golden[2])
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''        

        map_val1 = self.aggregator.map(self.rows[10])
        map_val2 = self.aggregator.map(self.rows[11])
        map_val3 = self.aggregator.map(self.rows[12])
        map_val4 = self.aggregator.map(self.rows[13])
                   
        reduce_val1 = self.aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(reduce_val1, self.reduce_golden[0])

        reduce_val2 = self.aggregator.reduce(reduce_val1, map_val3)
        self.assertEqual(reduce_val2, self.reduce_golden[1])

        reduce_val3 = self.aggregator.reduce(reduce_val2, map_val4)

        self.assertEqual(reduce_val3, self.reduce_golden[2])

    def test_map_reduce_row_list(self):
    
        rows = [self.rows[i] for i in [10,11]]
        reduce_val = self.aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val, self.reduce_golden[0])

        rows = [self.rows[i] for i in [10,11,12]]
        reduce_val = self.aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val, self.reduce_golden[1])

        rows = [self.rows[i] for i in [10,11,12, 13]]
        reduce_val = self.aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val, self.reduce_golden[2])


    def test_fields_needed(self):
        ''' test fields_needed function '''
        fn = self.aggregator.fields_needed()
        self.assertSetEqual(set(fn), 
                            set([sv.VARS.STREET_ADDRESS]))




class RangeFishingAggregatorTest(unittest.TestCase):
    """
    Test that the RangeFishingQA class acts as expected.
    """

    def setUp(self):

        dob_query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'dob',
                  qs.QRY_LBOUND : datetime.date(2013, 1, 18),
                  qs.QRY_UBOUND : datetime.date(2013, 9, 18) }
        foo_query = { qs.QRY_QID : 2,
                  qs.QRY_FIELD : 'foo',
                  qs.QRY_LBOUND : 99,
                  qs.QRY_UBOUND : 123456789 }
        self.dob_aggregator = qa.RangeFishingQA(dob_query)
        self.foo_aggregator = qa.RangeFishingQA(foo_query)

        self.rows = {}
        self.rows[10] = { sv.VARS.ID : 10,
                          sv.VARS.FOO : 123456789,
                          sv.VARS.DOB : datetime.date(2000, 1, 18) }
        self.rows[11] = { sv.VARS.ID : 11, 
                          sv.VARS.FOO : 1,
                          sv.VARS.DOB : datetime.date(2013, 3, 18) }
        self.rows[12] = { sv.VARS.ID : 12, 
                          sv.VARS.FOO : 123456789,
                          sv.VARS.DOB : datetime.date(2013, 9, 18) }
        self.rows[13] = { sv.VARS.ID : 13, 
                          sv.VARS.FOO : 100,
                          sv.VARS.DOB : datetime.date(2013, 3, 18) }

        #
        # Map Answers
        #

        # FOO
        # For row ID=10
        dict1 = collections.defaultdict(list)
        dict1[123456789] = [10]
        self.foo_map_golden = {}
        self.foo_map_golden[10] = \
            { qs.QRY_QID : 2, qs.QRY_VALID: True,
              qs.QRY_FISHING_MATCHES_FOUND : dict1} 
            
        # For row ID=11        
        dict2 = collections.defaultdict(list)
        self.foo_map_golden[11] = \
            { qs.QRY_QID : 2, qs.QRY_VALID: True,
              qs.QRY_FISHING_MATCHES_FOUND : dict2 }
        
        # For row ID=12
        dict3 = collections.defaultdict(list)
        dict3[123456789] = [12]
        self.foo_map_golden[12] = \
            { qs.QRY_QID : 2,  qs.QRY_VALID: True,
              qs.QRY_FISHING_MATCHES_FOUND : dict3 }

        # For row ID=13
        dict4 = collections.defaultdict(list)
        dict4[100] = [13]
        self.foo_map_golden[13] = \
            { qs.QRY_QID : 2,  qs.QRY_VALID: True,
              qs.QRY_FISHING_MATCHES_FOUND : dict4 }

        # DOB
        # For row ID=10
        dict5 = collections.defaultdict(list)
        self.dob_map_golden = {}
        self.dob_map_golden[10] = \
            { qs.QRY_QID : 1, qs.QRY_VALID: True, 
              qs.QRY_FISHING_MATCHES_FOUND : dict5 } 
            
        # For row ID=11        
        dict6 = collections.defaultdict(list)
        dict6[datetime.date(2013, 3, 18)] = [11]
        self.dob_map_golden[11] = \
            { qs.QRY_QID : 1, qs.QRY_VALID: True, 
              qs.QRY_FISHING_MATCHES_FOUND : dict6}
        
        # For row ID=12
        dict7 = collections.defaultdict(list)
        dict7[datetime.date(2013, 9, 18)] = [12]
        self.dob_map_golden[12] = \
            { qs.QRY_QID : 1, qs.QRY_VALID: True, 
              qs.QRY_FISHING_MATCHES_FOUND : dict7}

        # For row ID=13
        dict8 = collections.defaultdict(list)
        dict8[datetime.date(2013, 3, 18)] = [13]
        self.dob_map_golden[13] = \
            { qs.QRY_QID : 1,  qs.QRY_VALID: True,
              qs.QRY_FISHING_MATCHES_FOUND : dict8}



        #
        # Reduce Results
        #

        # FOO
        self.foo_reduce_golden = [] 
        # For row IDs 10 and 11
        dict_a = collections.defaultdict(list)
        dict_a[123456789] = [10]
        self.foo_reduce_golden.append( \
            { qs.QRY_QID : 2, 
              qs.QRY_FISHING_MATCHES_FOUND : dict_a,
              qs.QRY_VALID: True})
        # For row IDs 10, 11 and 12
        dict_b = collections.defaultdict(list)
        dict_b[123456789] = [10, 12]
        self.foo_reduce_golden.append( \
            { qs.QRY_QID : 2, 
              qs.QRY_FISHING_MATCHES_FOUND : dict_b,
              qs.QRY_VALID: True} )

        # For row IDs 10, 11, 12 and 13
        dict_c = collections.defaultdict(list)
        dict_c[100] = [13]
        self.foo_reduce_golden.append( \
            { qs.QRY_QID : 2, 
              qs.QRY_FISHING_MATCHES_FOUND : dict_c,
              qs.QRY_VALID: True})

        # DOB
        self.dob_reduce_golden = [] 
        # For row IDs 10 and 11
        dict_d = collections.defaultdict(list)
        dict_d[datetime.date(2013, 3, 18)] = [11]
        self.dob_reduce_golden.append( \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict_d, 
              qs.QRY_VALID: True} )

        # For row IDs 10, 11 and 12
        dict_e = collections.defaultdict(list)
        dict_e[datetime.date(2013, 3, 18)] = [11]
        self.dob_reduce_golden.append( \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict_e,
              qs.QRY_VALID: True} )

        # For row IDs 10, 11, 12 and 13
        dict_f = collections.defaultdict(list)
        dict_f[datetime.date(2013, 3, 18)] = [11, 13]
        self.dob_reduce_golden.append( \
            { qs.QRY_QID : 1, 
              qs.QRY_FISHING_MATCHES_FOUND : dict_f,
              qs.QRY_VALID: True} )


    def test_constructor(self):
        ''' test constructor '''
        self.assertEqual(self.dob_aggregator._qid, 1)
        self.assertEqual(self.dob_aggregator._field, sv.sql_name_to_enum('dob'))
        self.assertEqual(self.dob_aggregator._lbound, datetime.date(2013, 1, 18))
        self.assertEqual(self.dob_aggregator._ubound, datetime.date(2013, 9, 18))

        self.assertEqual(self.foo_aggregator._qid, 2)
        self.assertEqual(self.foo_aggregator._field, sv.sql_name_to_enum('foo'))
        self.assertEqual(self.foo_aggregator._lbound, 99)
        self.assertEqual(self.foo_aggregator._ubound, 123456789)


    def test_map_dob(self):
        ''' test map function for dob '''
        for row_num in [10, 11, 12, 13]:
            dob_map_val = self.dob_aggregator.map(self.rows[row_num])
            self.assertEqual(dob_map_val, self.dob_map_golden[row_num])


    def test_map_foo(self):
        ''' test map function for foo'''
        for row_num in [10, 11, 12, 13]:
            foo_map_val = self.foo_aggregator.map(self.rows[row_num])
            self.assertEqual(foo_map_val, self.foo_map_golden[row_num])


    def test_reduce_dob(self):
        ''' test reduce function for dob '''
        reduce_val = self.dob_aggregator.reduce(self.dob_map_golden[10], 
                                            self.dob_map_golden[11])
        self.assertEqual(reduce_val, self.dob_reduce_golden[0])

        reduce_val = self.dob_aggregator.reduce(reduce_val, 
                                                self.dob_map_golden[12])
        self.assertEqual(reduce_val, self.dob_reduce_golden[1])
        
        reduce_val = self.dob_aggregator.reduce(reduce_val, 
                                                self.dob_map_golden[13])
        self.assertEqual(reduce_val, self.dob_reduce_golden[2])
        
    def test_reduce_foo(self):
        ''' test reduce function for foo'''
        reduce_val = self.foo_aggregator.reduce(self.foo_map_golden[10], 
                                            self.foo_map_golden[11])
        self.assertEqual(reduce_val, self.foo_reduce_golden[0])

        reduce_val = self.foo_aggregator.reduce(reduce_val, 
                                                self.foo_map_golden[12])
        self.assertEqual(reduce_val, self.foo_reduce_golden[1])
        
        reduce_val = self.foo_aggregator.reduce(reduce_val, 
                                                self.foo_map_golden[13])
        self.assertEqual(reduce_val, self.foo_reduce_golden[2])
        
    def test_map_reduce_dob(self):
        ''' test map and reduce functions together for dob '''        
        map_val1 = self.dob_aggregator.map(self.rows[10])
        map_val2 = self.dob_aggregator.map(self.rows[11])
        map_val3 = self.dob_aggregator.map(self.rows[12])
        map_val4 = self.dob_aggregator.map(self.rows[13])
                   
        reduce_val1 = self.dob_aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(reduce_val1, self.dob_reduce_golden[0])

        reduce_val2 = self.dob_aggregator.reduce(reduce_val1, map_val3)
        self.assertEqual(reduce_val2, self.dob_reduce_golden[1])

        reduce_val3 = self.dob_aggregator.reduce(reduce_val2, map_val4)
        self.assertEqual(reduce_val3, self.dob_reduce_golden[2])


    def test_map_reduce_row_list_dob(self):

        rows = [self.rows[i] for i in [10,11]]
        reduce_val1 = self.dob_aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val1, self.dob_reduce_golden[0])
        
        rows = [self.rows[i] for i in [10,11,12]]
        reduce_val1 = self.dob_aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val1, self.dob_reduce_golden[1])

        rows = [self.rows[i] for i in [10,11,12,13]]
        reduce_val1 = self.dob_aggregator.map_reduce_row_list(rows)
        self.assertEqual(reduce_val1, self.dob_reduce_golden[2])




    def test_map_reduce_foo(self):
        ''' test map and reduce functions together for foo '''        

        map_val1 = self.foo_aggregator.map(self.rows[10])
        map_val2 = self.foo_aggregator.map(self.rows[11])
        map_val3 = self.foo_aggregator.map(self.rows[12])
        map_val4 = self.foo_aggregator.map(self.rows[13])
                   
        reduce_val1 = self.foo_aggregator.reduce(map_val1, map_val2)          
        self.assertEqual(reduce_val1, self.foo_reduce_golden[0])

        reduce_val2 = self.foo_aggregator.reduce(reduce_val1, map_val3)
        self.assertEqual(reduce_val2, self.foo_reduce_golden[1])

        reduce_val3 = self.foo_aggregator.reduce(reduce_val2, map_val4)
        self.assertEqual(reduce_val3, self.foo_reduce_golden[2])


    def test_map_reduce_row_list_foo(self):

        rows = [self.rows[i] for i in [10, 11]]
        reduce_val1 = self.foo_aggregator.map_reduce_row_list(rows)          
        self.assertEqual(reduce_val1, self.foo_reduce_golden[0])

        rows = [self.rows[i] for i in [10, 11, 12]]
        reduce_val1 = self.foo_aggregator.map_reduce_row_list(rows)          
        self.assertEqual(reduce_val1, self.foo_reduce_golden[1])

        rows = [self.rows[i] for i in [10, 11, 12, 13]]
        reduce_val1 = self.foo_aggregator.map_reduce_row_list(rows)          
        self.assertEqual(reduce_val1, self.foo_reduce_golden[2])



    def test_fields_needed_dob(self):
        ''' test fields_needed function for dob '''
        fn = self.dob_aggregator.fields_needed()
        self.assertSetEqual(set(fn), 
                            set([sv.VARS.DOB]))

    def test_fields_needed_foo(self):
        ''' test fields_needed function for foo '''
        fn = self.foo_aggregator.fields_needed()
        self.assertSetEqual(set(fn), 
                            set([sv.VARS.FOO]))
        
class XMLLeafQueryAggregatorTest(unittest.TestCase):
    """
    Test that the XMLLeadQueryAggregator class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''

        root = ElementTree.Element('a')
        root.text = "A"
        b = ElementTree.SubElement(root, 'b')
        b.text = "B"
        c = ElementTree.SubElement(root, 'c')
        c.text = "C"
        d = ElementTree.SubElement(b, 'd')
        d.text = "D"
        f = ElementTree.SubElement(b, 'f')
        f.text = "F"
        etree = ElementTree.ElementTree(root)
        self.generated_xml = GeneratedXml(etree)

        root2 = ElementTree.Element('x')
        root2.text = "X"
        c = ElementTree.SubElement(root2, 'y')
        c.text = "Y"
        etree2 = ElementTree.ElementTree(root2)
        self.generated_xml2 = GeneratedXml(etree2)

        self.matching_tuples = [('c', 'C'),
                                ('d', 'D'),
                                ('f', 'F')]
        
        self.invalid_tuples = [('c', 'A'),
                               ('b', 'B'),
                               ('f', 'D'),
                               ('z', 'Z')]
        


    def test_map(self):
        ''' test map function '''

        row = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }

        qid = 0
        for (path_list, leaf_value) in self.matching_tuples:
            qid = qid + 1
            query = { qs.QRY_QID : qid,
                      qs.QRY_FIELD : 'xml',
                      qs.QRY_XPATH : path_list,
                      qs.QRY_VALUE : leaf_value }
            aggregator = qa.XMLLeafQueryAggregator(query)

            goal =  { qs.QRY_QID : qid, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
            map_val = aggregator.map(row)
            self.assertEqual(map_val, goal, 
                             "path_list=%s leaf_value=%s map_val=%s" % 
                             (path_list, leaf_value, map_val))

        qid = 0
        for (leaf_tag, leaf_value) in self.invalid_tuples:
            qid = qid + 1
            query = { qs.QRY_QID : qid,
                      qs.QRY_FIELD : 'xml',
                      qs.QRY_XPATH : leaf_tag,
                      qs.QRY_VALUE : leaf_value }
            aggregator = qa.XMLLeafQueryAggregator(query)

            goal =  { qs.QRY_QID : qid, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
            map_val = aggregator.map(row)
            self.assertNotEqual(map_val, goal,
                             "path_list=%s leaf_value=%s map_val=%s" % 
                             (path_list, leaf_value, map_val))


    def test_reduce(self):
        ''' test reduce function '''
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1] }
        aggregator = qa.XMLLeafQueryAggregator(query)
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [2], qs.QRY_VALID: True }
        reduce_val = aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1,2], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))
        
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }
        row2 = { sv.VARS.ID : 2, sv.VARS.XML : self.generated_xml2 }
        row3 = { sv.VARS.ID : 3, sv.VARS.XML : self.generated_xml }
        row4 = { sv.VARS.ID : 4, sv.VARS.XML : self.generated_xml }

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1]}
        aggregator = qa.XMLLeafQueryAggregator(query)

        map_val1 = aggregator.map(row1)
        map_val2 = aggregator.map(row2)
        map_val3 = aggregator.map(row3)
        map_val4 = aggregator.map(row4)

        reduce_val1 = aggregator.reduce(map_val1, map_val2)          
        self.assertTrue(compare_results(reduce_val1, map_val1))

        reduce_val2 = aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val2, goal))

        reduce_val3 = aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val3, goal))

    def test_map_reduce_row_list(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }
        row2 = { sv.VARS.ID : 2, sv.VARS.XML : self.generated_xml2 }
        row3 = { sv.VARS.ID : 3, sv.VARS.XML : self.generated_xml }
        row4 = { sv.VARS.ID : 4, sv.VARS.XML : self.generated_xml }

        rows = [row1, row2, row3, row4]
        
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1]}
        aggregator = qa.XMLLeafQueryAggregator(query)

        reduce_val = aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))


    def test_fields_needed(self):
        ''' test fields_needed function '''
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1]}
        aggregator = qa.XMLLeafQueryAggregator(query)
        fn = aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.XML]))

    def test_match_row(self):
        ''' test match_row '''
        row1 = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }
        row2 = { sv.VARS.ID : 2, sv.VARS.XML : self.generated_xml2 }

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1]}
        aggregator = qa.XMLLeafQueryAggregator(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , False)

        # case sensitive
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0].upper(),
                  qs.QRY_VALUE : self.matching_tuples[0][1]}
        aggregator = qa.XMLLeafQueryAggregator(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , False)


class XMLPathQueryAggregatorTest(unittest.TestCase):
    """
    Test that the XMLPathQueryAggregator class acts as expected.
    """

    def setUp(self):
        ''' initialize test '''

        self.matching_tuples = [(['a', 'c'], 'C'),
                                (['a', 'b', 'd'], 'D'),
                                (['a', 'b', 'f'], 'F')]
        
        self.invalid_tuples = [(['c'], 'A'),
                               (['a', 'b'], 'D'),
                               (['a', 'b', 'f'], 'D'),
                               (['a', 'f'], 'F'),
                               (['z'], 'Z')]
        
        
        root = ElementTree.Element('a')
        root.text = "A"
        b = ElementTree.SubElement(root, 'b')
        b.text = "B"
        c = ElementTree.SubElement(root, 'c')
        c.text = "C"
        d = ElementTree.SubElement(b, 'd')
        d.text = "D"
        f = ElementTree.SubElement(b, 'f')
        f.text = "F"
        etree = ElementTree.ElementTree(root)
        self.generated_xml = GeneratedXml(etree)

        root2 = ElementTree.Element('x')
        root2.text = "X"
        c = ElementTree.SubElement(root2, 'y')
        c.text = "Y"
        etree2 = ElementTree.ElementTree(root2)
        self.generated_xml2 = GeneratedXml(etree2)


    def test_map(self):
        ''' test map function '''

        row = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }

        qid = 0
        for (path_list, leaf_value) in self.matching_tuples:
            qid = qid + 1
            query = { qs.QRY_QID : qid,
                      qs.QRY_FIELD : 'xml',
                      qs.QRY_XPATH : path_list,
                      qs.QRY_VALUE : leaf_value }
            aggregator = qa.XMLPathQueryAggregator(query)

            goal =  { qs.QRY_QID : qid, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
            map_val = aggregator.map(row)
            self.assertEqual(map_val, goal, 
                             "path_list=%s leaf_value=%s map_val=%s" % 
                             (path_list, leaf_value, map_val))

        qid = 0
        for (path_list, leaf_value) in self.invalid_tuples:
            qid = qid + 1
            query = { qs.QRY_QID : qid,
                      qs.QRY_FIELD : 'xml',
                      qs.QRY_XPATH : path_list,
                      qs.QRY_VALUE : leaf_value }
            aggregator = qa.XMLPathQueryAggregator(query)

            goal =  { qs.QRY_QID : qid, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
            map_val = aggregator.map(row)
            self.assertNotEqual(map_val, goal,
                             "path_list=%s leaf_value=%s map_val=%s" % 
                             (path_list, leaf_value, map_val))


    def test_reduce(self):
        ''' test reduce function '''
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1] }
        aggregator = qa.XMLPathQueryAggregator(query)
        map_result1 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1], qs.QRY_VALID: True }
        map_result2 = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [2], qs.QRY_VALID: True }
        reduce_val = aggregator.reduce(map_result1, map_result2)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1,2], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))
        
    def test_map_reduce(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }
        row2 = { sv.VARS.ID : 2, sv.VARS.XML : self.generated_xml2 }
        row3 = { sv.VARS.ID : 3, sv.VARS.XML : self.generated_xml }
        row4 = { sv.VARS.ID : 4, sv.VARS.XML : self.generated_xml }

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1] }
        aggregator = qa.XMLPathQueryAggregator(query)

        map_val1 = aggregator.map(row1)
        map_val2 = aggregator.map(row2)
        map_val3 = aggregator.map(row3)
        map_val4 = aggregator.map(row4)

        reduce_val1 = aggregator.reduce(map_val1, map_val2)          
        self.assertTrue(compare_results(reduce_val1, map_val1))

        reduce_val2 = aggregator.reduce(reduce_val1, map_val3)          
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val2, goal))

        reduce_val3 = aggregator.reduce(reduce_val2, map_val4)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val3, goal))

    def test_map_reduce2(self):
        ''' test map and reduce functions together '''
        row1 = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }
        row2 = { sv.VARS.ID : 2, sv.VARS.XML : self.generated_xml2 }
        row3 = { sv.VARS.ID : 3, sv.VARS.XML : self.generated_xml }
        row4 = { sv.VARS.ID : 4, sv.VARS.XML : self.generated_xml }

        rows = [row1, row2, row3, row4]
        
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1] }
        aggregator = qa.XMLPathQueryAggregator(query)

        reduce_val = aggregator.map_reduce_row_list(rows)
        goal = { qs.QRY_QID : 1, rdb.DBF_MATCHINGRECORDIDS : [1, 3, 4], qs.QRY_VALID: True }
        self.assertTrue(compare_results(reduce_val, goal))


    def test_fields_needed(self):
        ''' test fields_needed function '''
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1] }
        aggregator = qa.XMLPathQueryAggregator(query)
        fn = aggregator.fields_needed()
        fn_set = set(fn)
        self.assertSetEqual(fn_set, set([sv.VARS.XML]))

    def test_match_row(self):
        ''' test match_row '''
        row1 = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml }
        row2 = { sv.VARS.ID : 1, sv.VARS.XML : self.generated_xml2 }

        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : self.matching_tuples[0][0],
                  qs.QRY_VALUE : self.matching_tuples[0][1] }
        aggregator = qa.XMLPathQueryAggregator(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match , True)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , False)

        # case sensitive
        query = { qs.QRY_QID : 1,
                  qs.QRY_FIELD : 'xml',
                  qs.QRY_XPATH : ['a', 'C'],
                  qs.QRY_VALUE : self.matching_tuples[0][1] }
        aggregator = qa.XMLPathQueryAggregator(query)
        match = aggregator.match_row(row1)
        self.assertEqual(match , False)
        match  = aggregator.match_row(row2)
        self.assertEqual(match , False)




