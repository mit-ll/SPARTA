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


import unittest
import spar_python.common.aggregators.atomic_query_aggregators \
    as atomic_query_aggregators
import spar_python.data_generation.spar_variables as spar_variables
from spar_python.common.distributions.generated_text import GeneratedText
import datetime



class LambdaCollectorTest(unittest.TestCase):
    """
    Test that the LambdaCollector class acts as expected.
    """

    def setUp(self):
        matching_f = lambda row : row['field1'] == 'a'
        self.fields_needed = ['field1']
        self.collector = \
            atomic_query_aggregators.LambdaCollector(matching_f,
                                                     self.fields_needed)

        self.row1 = {'field1' : 'a', spar_variables.VARS.ID : 'b'}
        self.row2 = {'field1' : 'a', spar_variables.VARS.ID : 'c'}
        self.row3 = {'field1' : 'a', spar_variables.VARS.ID : 'd'}

    def test_map1(self):
        result = self.collector.map(self.row1)
        self.assertSetEqual(result, set('b'))



    def test_map2(self):
        self.row1['field1'] = 'c'
        result = self.collector.map(self.row1)
        self.assertEqual(result, set())


    def test_map3(self):
        self.row1[spar_variables.VARS.ID] = None
        result = self.collector.map(self.row1)
        self.assertSetEqual(result, set([None]))

    def test_map4(self):
        self.row1['field2'] = 3
        result = self.collector.map(self.row1)
        self.assertSetEqual(result, set('b'))



    def test_reduce1(self):
        result1 = self.collector.map(self.row1)
        result2 = self.collector.map(self.row2)
        agg_result = self.collector.reduce(result1, result2)
        self.assertSetEqual(agg_result, set(['b','c']))
        
    def test_reduce2(self):
        base_count = 10
        agg_result1 = self.collector.map(self.row1)
        agg_result2 = self.collector.map(self.row2)
        agg_result3 = self.collector.map(self.row3)
        
        def add_row_to_result(row, result):
            new_result = self.collector.map(row)
            if new_result is None:
                return result
            else:
                return self.collector.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row1, agg_result2)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row3, agg_result3)
            
        
        final_agg_result = self.collector.reduce(agg_result1, agg_result2)
        final_agg_result = self.collector.reduce(final_agg_result, agg_result3)
        
        self.assertSetEqual(final_agg_result, set(['b', 'c', 'd']))
        
    def test_fields_needed(self):
        fn = self.collector.fields_needed()
        goal = set(self.fields_needed)
        self.assertSetEqual(set(fn), goal)




class EqualityCounterTest(unittest.TestCase):
    """
    Test that the equality-counter class acts as expected.
    """


    def setUp(self):
        pass

    def test_map(self):
        counter = atomic_query_aggregators.EqualityCounter('field1')
        row = {'field1' : 'a', 'field2' : 'b'}
        result = counter.map(row)
        self.assertDictEqual(result, {'a' : 1})


    def test_map2(self):
        counter = atomic_query_aggregators.EqualityCounter('field1')
        row = {'field1' : None, 'field2' : 'b'}
        result = counter.map(row)
        self.assertDictEqual(result, {None : 1})



    def test_reduce1(self):
        row1 = {'field1' : 'a'}

        ea1 = atomic_query_aggregators.EqualityCounter('field1')
        
        result1 = ea1.map(row1)
        result2 = ea1.map(row1)
        
        agg_result = ea1.reduce(result1, result2)
        
        self.assertEqual(agg_result, {'a': 2})
        


    def test_reduce2(self):
        row1 = {'field1' : 'a'}
        row2 = {'field1' : 'b'}
        row3 = {'field1' : 'c'}

        base_count = 10

        ea = atomic_query_aggregators.EqualityCounter('field1')

        agg_result1 = ea.map(row1)
        agg_result2 = ea.map(row2)
        agg_result3 = ea.map(row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(row1, agg_result1)
            add_row_to_result(row1, agg_result2)
            add_row_to_result(row2, agg_result2)
            add_row_to_result(row1, agg_result1)
            add_row_to_result(row2, agg_result2)
            add_row_to_result(row3, agg_result3)
            
            
        final_agg_result = ea.reduce(agg_result1, agg_result2)
        final_agg_result = ea.reduce(final_agg_result, agg_result3)
        
        self.assertDictEqual(final_agg_result,
                             {'a' : (3 * base_count) + 1,
                              'b' : (2 * base_count) + 1,
                              'c' : base_count + 1})
        
        
    def test_fields_needed(self):
        field_id = 'field1'
        ea = atomic_query_aggregators.EqualityCounter(field_id)
        fn = ea.fields_needed()
        self.assertSetEqual(set(fn), set([field_id]))

        
        
class EqualityCollectorTest(unittest.TestCase):
    """
    Test that the equality-counter class acts as expected.
    """

    def setUp(self):
        pass

    def test_map1(self):
        collector = atomic_query_aggregators.EqualityCollector('field1', 'a')
        row = {'field1' : 'a', spar_variables.VARS.ID : 'b'}
        result = collector.map(row)
        self.assertSetEqual(result, set('b'))



    def test_map2(self):
        collector = atomic_query_aggregators.EqualityCollector('field1', 'c')
        row = {'field1' : 'a',  spar_variables.VARS.ID : 'b'}
        result = collector.map(row)
        self.assertEqual(result, set())


    def test_map3(self):
        collector = atomic_query_aggregators.EqualityCollector('field1', 'a')
        row = {'field1' : 'a', spar_variables.VARS.ID : None}
        result = collector.map(row)
        self.assertSetEqual(result, set([None]))




    def test_reduce1(self):
        row1 = {'field1' : 'a', spar_variables.VARS.ID : 'b'}
        row2 = {'field1' : 'a', spar_variables.VARS.ID : 'c'}

        ea = atomic_query_aggregators.EqualityCollector('field1', 'a')
        
        result1 = ea.map(row1)
        result2 = ea.map(row2)
        
        agg_result = ea.reduce(result1, result2)
        
        self.assertSetEqual(agg_result, set(['b','c']))
        


    def test_reduce2(self):
        row1 = {'field1' : 'a', spar_variables.VARS.ID : 'b'}
        row2 = {'field1' : 'a', spar_variables.VARS.ID : 'c'}
        row3 = {'field1' : 'a', spar_variables.VARS.ID : 'd'}

        base_count = 10

        ea = atomic_query_aggregators.EqualityCollector('field1', 'a')

        agg_result1 = ea.map(row1)
        agg_result2 = ea.map(row2)
        agg_result3 = ea.map(row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            if new_result is None:
                return result
            else:
                return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(row1, agg_result1)
            add_row_to_result(row1, agg_result2)
            add_row_to_result(row2, agg_result2)
            add_row_to_result(row1, agg_result1)
            add_row_to_result(row2, agg_result2)
            add_row_to_result(row3, agg_result3)
            
        
        final_agg_result = ea.reduce(agg_result1, agg_result2)
        final_agg_result = ea.reduce(final_agg_result, agg_result3)
        
        self.assertSetEqual(final_agg_result, set(['b', 'c', 'd']))
        
    def test_fields_needed(self):
        field_id = 'field1'
        ea = atomic_query_aggregators.EqualityCollector(field_id, 'a')
        fn = ea.fields_needed()
        self.assertSetEqual(set(fn), set([field_id]))

        
        
class RangeCollectorTest(unittest.TestCase):
    """
    Test that the equality-counter class acts as expected.
    """

    def setUp(self):
        pass

    def test_map1(self):
        collector = atomic_query_aggregators.RangeCollector('field1', 3, 5)
        row = {'field1' : 4, spar_variables.VARS.ID : 'b'}
        result = collector.map(row)
        self.assertSetEqual(result, set('b'))

    def test_map2(self):
        collector = atomic_query_aggregators.RangeCollector('field1', 3, 5)
        row = {'field1' : 3, spar_variables.VARS.ID : 'b'}
        result = collector.map(row)
        self.assertSetEqual(result, set('b'))

    def test_map3(self):
        collector = atomic_query_aggregators.RangeCollector('field1', 3, 5)
        row = {'field1' : 5, spar_variables.VARS.ID : 'b'}
        result = collector.map(row)
        self.assertSetEqual(result, set('b'))

    def test_map4(self):
        collector = atomic_query_aggregators.RangeCollector('field1', 3, 5)
        row = {'field1' : 0,  spar_variables.VARS.ID : 'b'}
        result = collector.map(row)
        self.assertEqual(result, set())

    def test_map5(self):
        collector = atomic_query_aggregators.RangeCollector('field1', 3, 5)
        row = {'field1' : 6,  spar_variables.VARS.ID : 'b'}
        result = collector.map(row)
        self.assertEqual(result, set())


    def test_map6(self):
        collector = atomic_query_aggregators.RangeCollector('field1', 3, 5)
        row = {'field1' : 4, spar_variables.VARS.ID : None}
        result = collector.map(row)
        self.assertSetEqual(result, set([None]))


    def test_map_date1(self):
        lower_date = datetime.date(2012, 1, 1)
        upper_date = datetime.date(2012, 12, 31)
        
        collector = atomic_query_aggregators.RangeCollector('dob',
                                                            lower_date,
                                                            upper_date)
        
        row = {'dob' : datetime.date(2012, 6, 1), spar_variables.VARS.ID : 'a'} 
        
        result = collector.map(row)
        self.assertSetEqual(result, set('a'))



    def test_map_date2(self):
        lower_date = datetime.date(2012, 1, 1)
        upper_date = datetime.date(2012, 12, 31)
        
        collector = atomic_query_aggregators.RangeCollector('dob',
                                                            lower_date,
                                                            upper_date)
        
        row = {'dob' : datetime.date(2012, 1, 1), spar_variables.VARS.ID : 'a'} 
        
        result = collector.map(row)
        self.assertSetEqual(result, set('a'))



    def test_map_date3(self):
        lower_date = datetime.date(2012, 1, 1)
        upper_date = datetime.date(2012, 12, 31)
        
        collector = atomic_query_aggregators.RangeCollector('dob',
                                                            lower_date,
                                                            upper_date)
        
        row = {'dob' : datetime.date(2012, 12, 31), 
               spar_variables.VARS.ID : 'a'} 
        
        result = collector.map(row)
        self.assertSetEqual(result, set('a'))




    def test_map_date4(self):
        lower_date = datetime.date(2012, 1, 1)
        upper_date = datetime.date(2012, 12, 31)
        
        collector = atomic_query_aggregators.RangeCollector('dob',
                                                            lower_date,
                                                            upper_date)
        
        row = {'dob' : datetime.date(2011, 12, 31), 
               spar_variables.VARS.ID : 'a'} 
        
        result = collector.map(row)
        self.assertEqual(result, set())



    def test_map_date5(self):
        lower_date = datetime.date(2012, 1, 1)
        upper_date = datetime.date(2012, 12, 31)
        
        collector = atomic_query_aggregators.RangeCollector('dob',
                                                            lower_date,
                                                            upper_date)
        
        row = {'dob' : datetime.date(2013, 1, 1), 
               spar_variables.VARS.ID : 'a'} 
        
        result = collector.map(row)
        self.assertEqual(result, set())




    def test_reduce1(self):
        row1 = {'field1' : 3, spar_variables.VARS.ID : 'b'}
        row2 = {'field1' : 4, spar_variables.VARS.ID : 'c'}

        ea = atomic_query_aggregators.RangeCollector('field1', 3, 5)
        
        result1 = ea.map(row1)
        result2 = ea.map(row2)
        
        agg_result = ea.reduce(result1, result2)
        
        self.assertSetEqual(agg_result, set(['b','c']))
        


    def test_reduce2(self):
        row1 = {'field1' : 3, spar_variables.VARS.ID : 'b'}
        row2 = {'field1' : 4, spar_variables.VARS.ID : 'c'}
        row3 = {'field1' : 5, spar_variables.VARS.ID : 'd'}
        row4 = {'field1' : 6, spar_variables.VARS.ID : 'd'}

        base_count = 10

        ea = atomic_query_aggregators.RangeCollector('field1', 3, 5)

        agg_result1 = ea.map(row1)
        agg_result2 = ea.map(row2)
        agg_result3 = ea.map(row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            if new_result is None:
                return result
            else:
                return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(row1, agg_result1)
            add_row_to_result(row1, agg_result2)
            add_row_to_result(row2, agg_result2)
            add_row_to_result(row1, agg_result1)
            add_row_to_result(row2, agg_result2)
            add_row_to_result(row3, agg_result3)
            add_row_to_result(row4, agg_result1)
            add_row_to_result(row4, agg_result2)
            add_row_to_result(row4, agg_result3)
            
        
        final_agg_result = ea.reduce(agg_result1, agg_result2)
        final_agg_result = ea.reduce(final_agg_result, agg_result3)
        
        self.assertSetEqual(final_agg_result, set(['b', 'c', 'd']))

        
    def test_fields_needed(self):
        field_id = 'field1'
        ea = atomic_query_aggregators.RangeCollector(field_id, 3, 5)
        fn = ea.fields_needed()
        self.assertSetEqual(set(fn), set([field_id]))


class KeywordCounterTest(unittest.TestCase):
    """
    Test that the equality-counter class acts as expected.
    """


    def setUp(self):
        self.row1 = {spar_variables.VARS.ID : 1,
                     'text' : 
                     GeneratedText(['Running', ' ', 'is', ' ', 'discouraged', '.'],
                                   ['run', None, 'is', None, 'discourag', None],
                                   ['running', ' ', 'is', ' ', 'discouraged', '.'])}

        
        self.row2 = {spar_variables.VARS.ID : 2,
                     'text' : 
                    GeneratedText(['Walking', ' ', 'is', ' ', 'encouraged', '.'],
                                   ['walk', None, 'is', None, 'encourag', None],
                                   ['walking', ' ', 'is', ' ', 'encouraged', '.'])}

        self.row3 = {spar_variables.VARS.ID : 3,
                     'text' : 
                     GeneratedText(['Falling', ' ', 'is', ' ', 'forbidden', '.'],
                                   ['fall', None, 'is', None, 'forbid', None],
                                   ['falling', ' ', 'is', ' ', 'forbidden', '.'])}


    def test_map_ignore_case(self):
        counter = atomic_query_aggregators.KeywordCounter('text')
        result = counter.map(self.row1)
        goal_result = {"running" : 1,
                       "is": 1,
                       "discouraged" : 1}
        self.assertDictEqual(result, goal_result)


    def test_map_match_case(self):
        counter = atomic_query_aggregators.KeywordCounter('text',
                                                          match_case = True)
        result = counter.map(self.row1)
        goal_result = {"Running" : 1,
                       "is": 1,
                       "discouraged" : 1}
        self.assertDictEqual(result, goal_result)


    def test_reduce_ignore_case(self):

        ea1 = atomic_query_aggregators.KeywordCounter('text')
        
        result1 = ea1.map(self.row1)
        result2 = ea1.map(self.row2)
        
        agg_result = ea1.reduce(result1, result2)
        
        goal_result = {"running" : 1,
                       "is": 2,
                       "discouraged" : 1,
                       "walking" : 1,
                       "encouraged" : 1}
        
        self.assertDictEqual(agg_result, goal_result)



    def test_reduce_match_case(self):

        ea1 = atomic_query_aggregators.KeywordCounter('text',
                                                      match_case = True)
        
        result1 = ea1.map(self.row1)
        result2 = ea1.map(self.row2)
        
        agg_result = ea1.reduce(result1, result2)
        
        goal_result = {"Running" : 1,
                       "is": 2,
                       "discouraged" : 1,
                       "Walking" : 1,
                       "encouraged" : 1}
        
        self.assertDictEqual(agg_result, goal_result)



    def test_reduce_ignore_case2(self):

        base_count = 10

        ea = atomic_query_aggregators.KeywordCounter('text')

        agg_result1 = ea.map(self.row1)
        agg_result2 = ea.map(self.row2)
        agg_result3 = ea.map(self.row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row1, agg_result2)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row3, agg_result3)
            
            
        final_agg_result = ea.reduce(agg_result1, agg_result2)
        final_agg_result = ea.reduce(final_agg_result, agg_result3)


        goal_result = {"running" : (3 * base_count) + 1,
                       "walking" : (2 * base_count) + 1,
                       "falling" : base_count + 1,
                       "is" : (6 * base_count) + 3,
                       "discouraged" : (3 * base_count) + 1,
                       "encouraged" : (2 * base_count) + 1,
                       "forbidden" : base_count + 1}

        
        self.assertDictEqual(final_agg_result, goal_result)


    def test_reduce_match_case2(self):

        base_count = 10

        ea = atomic_query_aggregators.KeywordCounter('text',
                                                     match_case = True)

        agg_result1 = ea.map(self.row1)
        agg_result2 = ea.map(self.row2)
        agg_result3 = ea.map(self.row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row1, agg_result2)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row3, agg_result3)
            
            
        final_agg_result = ea.reduce(agg_result1, agg_result2)
        final_agg_result = ea.reduce(final_agg_result, agg_result3)


        goal_result = {"Running" : (3 * base_count) + 1,
                       "Walking" : (2 * base_count) + 1,
                       "Falling" : base_count + 1,
                       "is" : (6 * base_count) + 3,
                       "discouraged" : (3 * base_count) + 1,
                       "encouraged" : (2 * base_count) + 1,
                       "forbidden" : base_count + 1}

        
        self.assertDictEqual(final_agg_result, goal_result)

    def test_fields_needed(self):
        field_id = 'field1'
        ea = atomic_query_aggregators.KeywordCounter(field_id,
                                                     match_case = True)
        fn = ea.fields_needed()
        self.assertSetEqual(set(fn), set([field_id]))



class StemCounterTest(unittest.TestCase):
    """
    Test that the equality-counter class acts as expected.
    """


    def setUp(self):
        self.row1 = {spar_variables.VARS.ID : 1,
                     'text' : 
                     GeneratedText(['Running', ' ', 'is', ' ', 'discouraged', '.'],
                                   ['run', None, 'is', None, 'discourag', None],
                                   ['running', ' ', 'is', ' ', 'discouraged', '.'])}

        
        self.row2 = {spar_variables.VARS.ID : 2,
                     'text' : 
                    GeneratedText(['Walking', ' ', 'is', ' ', 'encouraged', '.'],
                                   ['walk', None, 'is', None, 'encourag', None],
                                   ['walking', ' ', 'is', ' ', 'encouraged', '.'])}

        self.row3 = {spar_variables.VARS.ID : 3,
                     'text' : 
                     GeneratedText(['Falling', ' ', 'is', ' ', 'forbidden', '.'],
                                   ['fall', None, 'is', None, 'forbid', None],
                                   ['falling', ' ', 'is', ' ', 'forbidden', '.'])}

 
    def test_map(self):
        counter = atomic_query_aggregators.StemCounter('text')
        result = counter.map(self.row1)
        goal_result = {"run" : 1,
                       "is": 1,
                       "discourag" : 1}
        self.assertDictEqual(result, goal_result)



    def test_reduce(self):

        ea1 = atomic_query_aggregators.StemCounter('text')
        
        result1 = ea1.map(self.row1)
        result2 = ea1.map(self.row2)
        
        agg_result = ea1.reduce(result1, result2)
        
        goal_result = {"run" : 1,
                       "is": 2,
                       "discourag" : 1,
                       "walk" : 1,
                       "encourag" : 1}
        
        self.assertEqual(agg_result, goal_result)


    def test_reduce2(self):

        base_count = 10

        ea = atomic_query_aggregators.StemCounter('text')

        agg_result1 = ea.map(self.row1)
        agg_result2 = ea.map(self.row2)
        agg_result3 = ea.map(self.row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row1, agg_result2)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row3, agg_result3)
            
            
        final_agg_result = ea.reduce(agg_result1, agg_result2)
        final_agg_result = ea.reduce(final_agg_result, agg_result3)


        goal_result = {"run" : (3 * base_count) + 1,
                       "walk" : (2 * base_count) + 1,
                       "fall" : base_count + 1,
                       "is" : (6 * base_count) + 3,
                       "discourag" : (3 * base_count) + 1,
                       "encourag" : (2 * base_count) + 1,
                       "forbid" : base_count + 1}

        
        self.assertDictEqual(final_agg_result, goal_result)


    def test_fields_needed(self):
        field_id = 'field1'
        ea = atomic_query_aggregators.StemCounter(field_id)
        fn = ea.fields_needed()
        self.assertSetEqual(set(fn), set([field_id]))
        
        
        
class KeywordCollectorTest(unittest.TestCase):
    """
    Test that the equality-counter class acts as expected.
    """

    def setUp(self):
        self.row1 = {spar_variables.VARS.ID : 1,
                     'text' : [("Running", "run"),
                               (" ", None),
                               ("is", "is"),
                               (" ", None),
                               ("discouraged", "discourag"),
                               (".", None)]}
        self.row2 = {spar_variables.VARS.ID : 2,
                     'text' : [("Walking", "walk"),
                               (" ", None),
                               ("is", "is"),
                               (" ", None),
                               ("encouraged", "encourag"),
                               (".", None)]}
        self.row3 = {spar_variables.VARS.ID : 3,
                     'text' : [("Falling", "fall"),
                               (" ", None),
                               ("is", "is"),
                               (" ", None),
                               ("forbidden", "forbid"),
                               (".", None)]}

    def test_map_ignore_case1(self):
        collector = atomic_query_aggregators.KeywordCollector('text', 'running')
        result = collector.map(self.row1)
        self.assertIsNotNone(result)
        self.assertSetEqual(result, set([1]))

    def test_map_match_case1_1(self):
        collector = atomic_query_aggregators.KeywordCollector('text', 'Running',
                                                              match_case = True)
        result = collector.map(self.row1)
        self.assertSetEqual(result, set([1]))

    def test_map_match_case1_2(self):
        collector = atomic_query_aggregators.KeywordCollector('text', 'running',
                                                              match_case = True)
        result = collector.map(self.row1)
        self.assertEqual(result, set())


    def test_map_ignore_case2(self):
        collector = atomic_query_aggregators.KeywordCollector('text', 'running')
        result = collector.map(self.row2)
        self.assertEqual(result, set())

    def test_map_match_case2(self):
        collector = atomic_query_aggregators.KeywordCollector('text', 'running',
                                                              match_case = True)
        result = collector.map(self.row2)
        self.assertEqual(result, set())


    def test_map_ignore_case3(self):
        broken_row1 = self.row1
        broken_row1[spar_variables.VARS.ID] = None
        collector = atomic_query_aggregators.KeywordCollector('text', 'Running')
        result = collector.map(broken_row1)
        self.assertSetEqual(result, set([None]))


    def test_map_match_case3(self):
        broken_row1 = self.row1
        broken_row1[spar_variables.VARS.ID] = None
        collector = atomic_query_aggregators.KeywordCollector('text', 'Running',
                                                              match_case = True)
        result = collector.map(broken_row1)
        self.assertSetEqual(result, set([None]))




    def test_reduce1(self):

        ea = atomic_query_aggregators.KeywordCollector('text', 'Running')
        
        result1 = ea.map(self.row1)
        result2 = ea.map(self.row1)
        
        agg_result = ea.reduce(result1, result2)
        
        self.assertSetEqual(agg_result, set([1]))



    def test_reduce2(self):

        base_count = 10

        ea = atomic_query_aggregators.KeywordCollector('text', 'is')

        agg_result1 = ea.map(self.row1)
        agg_result2 = ea.map(self.row2)
        agg_result3 = ea.map(self.row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row1, agg_result2)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row2, agg_result2)
            add_row_to_result(self.row3, agg_result3)
            
            
        final_agg_result = ea.reduce(agg_result1, agg_result2)
        final_agg_result = ea.reduce(final_agg_result, agg_result3)


        goal_result = set([1,2,3])
        
        self.assertSetEqual(final_agg_result, goal_result)


    def test_fields_needed(self):
        field_id = 'field1'
        ea = atomic_query_aggregators.KeywordCollector(field_id, 'Running',
                                                     match_case = True)
        fn = ea.fields_needed()
        self.assertSetEqual(set(fn), set([field_id]))
        
        
class StemCollectorTest(unittest.TestCase):
    """
    Test that the equality-counter class acts as expected.
    """

    def setUp(self):
        self.row1 = {spar_variables.VARS.ID : 1,
                     'text' : [("Running", "run"),
                               (" ", None),
                               ("is", "is"),
                               (" ", None),
                               ("discouraged", "discourag"),
                               (".", None)]}
        self.row2 = {spar_variables.VARS.ID : 2,
                     'text' : [("Walking", "walk"),
                               (" ", None),
                               ("is", "is"),
                               (" ", None),
                               ("encouraged", "encourag"),
                               (".", None)]}
        self.row3 = {spar_variables.VARS.ID : 3,
                     'text' : [("Do", "do"),
                               (" ", None),
                               ("not", "not"),
                               (" ", None),
                               ("run", "run"),
                               (".", None)]}

    def test_map1_1(self):
        collector = atomic_query_aggregators.StemCollector('text', 'run')
        result = collector.map(self.row1)
        self.assertIsNotNone(result)
        self.assertSetEqual(result, set([1]))

    def test_map1_2(self):
        collector = atomic_query_aggregators.StemCollector('text', 'running')
        result = collector.map(self.row1)
        self.assertIsNotNone(result)
        self.assertSetEqual(result, set([1]))

    def test_map1_3(self):
        collector = atomic_query_aggregators.StemCollector('text', 'Runs')
        result = collector.map(self.row1)
        self.assertIsNotNone(result)
        self.assertSetEqual(result, set([1]))



    def test_map2(self):
        collector = atomic_query_aggregators.StemCollector('text', 'Runs')
        result = collector.map(self.row2)
        self.assertEqual(result, set())

    def test_map3(self):
        broken_row1 = self.row1
        broken_row1[spar_variables.VARS.ID] = None
        collector = atomic_query_aggregators.StemCollector('text', 'Runs')
        result = collector.map(broken_row1)
        self.assertSetEqual(result, set([None]))



    def test_reduce1(self):

        ea = atomic_query_aggregators.StemCollector('text', 'Runs')
        
        result1 = ea.map(self.row1)
        result2 = ea.map(self.row1)
        
        agg_result = ea.reduce(result1, result2)
        
        self.assertSetEqual(agg_result, set([1]))




    def test_reduce2(self):

        base_count = 10

        ea = atomic_query_aggregators.StemCollector('text', 'Runs')

        agg_result1 = ea.map(self.row1)
        agg_result3 = ea.map(self.row3)
        
        def add_row_to_result(row, result):
            new_result = ea.map(row)
            return ea.reduce(result, new_result)
        
        for _ in xrange(base_count):
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row1, agg_result1)
            add_row_to_result(self.row3, agg_result3)
            
            
        final_agg_result = ea.reduce(agg_result1, agg_result3)


        goal_result = set([1,3])
        
        self.assertSetEqual(final_agg_result, goal_result)

    def test_fields_needed(self):
        field_id = 'field1'
        ea = atomic_query_aggregators.StemCollector(field_id, 'Running')
        fn = ea.fields_needed()
        self.assertSetEqual(set(fn), set([field_id]))

