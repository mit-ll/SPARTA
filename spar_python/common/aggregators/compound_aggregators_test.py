# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for compound_aggregators.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  20 Aug 2013   jch            Original version
# *****************************************************************


import unittest

import spar_python.data_generation.spar_variables as sv
import spar_python.common.aggregators.compound_aggregators as ca
import spar_python.common.aggregators.atomic_query_aggregators as aqa


class ConjunctiveCollectorTest(unittest.TestCase):
    """
    Test that the ConjunctiveCollector class acts as expected.
    """


    def setUp(self):
        
        sub_agg1 = aqa.EqualityCollector('field1', 'a')
        sub_agg2 = aqa.EqualityCollector('field2', 'b')
        sub_aggs = [sub_agg1, sub_agg2]
        
        self.agg = ca.ConjunctiveCollector(sub_aggs)



    def test_fields_needed(self):
        fn = self.agg.fields_needed()
        goal = set(['field1', 'field2'])
        self.assertSetEqual(fn, goal)


    def test_map1(self):

        row = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 1}
        result = self.agg.map(row)
        
        goal_toplevel = set([1])
        goal_subs = [set([1]), set([1])]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)


    def test_map2(self):

        row = {'field1' : 'a', 
               'field2' : 'a',
               sv.VARS.ID : 1}
        result = self.agg.map(row)
        
        goal_toplevel = set()
        goal_subs = [set([1]), set()]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)


    def test_map3(self):

        row = {'field1' : 'c', 
               'field2' : 'c',
               sv.VARS.ID : 1}
        result = self.agg.map(row)
        
        goal_toplevel = set()
        goal_subs = [set(), set()]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)


    def test_reduce1(self):


        row1 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 1}
        result1 = self.agg.map(row1)

        
        row2 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 2}
        result2 = self.agg.map(row2)


        row3 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 3}
        result3 = self.agg.map(row3)

        result = self.agg.reduce(result1,
                                 self.agg.reduce(result2,
                                                 result3))

        goal_toplevel = set([1,2,3])
        goal_subs = [set([1,2,3]), set([1,2,3])]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)

    def test_reduce2(self):


        row1 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 1}
        result1 = self.agg.map(row1)

        
        row2 = {'field1' : 'a', 
               'field2' : None,
               sv.VARS.ID : 2}
        result2 = self.agg.map(row2)


        row3 = {'field1' : None, 
               'field2' : 'b',
               sv.VARS.ID : 3}
        result3 = self.agg.map(row3)

        result = self.agg.reduce(result1,
                                 self.agg.reduce(result2,
                                                 result3))

        goal_toplevel = set([1])
        goal_subs = [set([1,2]), set([1,3])]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)





class DisjunctiveCollectorTest(unittest.TestCase):
    """
    Test that the DisjunctiveCollector class acts as expected.
    """


    def setUp(self):
        
        sub_agg1 = aqa.EqualityCollector('field1', 'a')
        sub_agg2 = aqa.EqualityCollector('field2', 'b')
        sub_aggs = [sub_agg1, sub_agg2]
        
        self.agg = ca.DisjunctiveCollector(sub_aggs)



    def test_fields_needed(self):
        fn = self.agg.fields_needed()
        goal = set(['field1', 'field2'])
        self.assertSetEqual(fn, goal)


    def test_map1(self):

        row = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 1}
        result = self.agg.map(row)
        
        goal_toplevel = set([1])
        goal_subs = [set([1]), set([1])]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)


    def test_map2(self):

        row = {'field1' : 'a', 
               'field2' : 'a',
               sv.VARS.ID : 1}
        result = self.agg.map(row)
        
        goal_toplevel = set([1])
        goal_subs = [set([1]), set()]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)


    def test_map3(self):

        row = {'field1' : 'c', 
               'field2' : 'c',
               sv.VARS.ID : 1}
        result = self.agg.map(row)
        
        goal_toplevel = set()
        goal_subs = [set(), set()]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)


    def test_reduce1(self):


        row1 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 1}
        result1 = self.agg.map(row1)

        
        row2 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 2}
        result2 = self.agg.map(row2)


        row3 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 3}
        result3 = self.agg.map(row3)

        result = self.agg.reduce(result1,
                                 self.agg.reduce(result2,
                                                 result3))

        goal_toplevel = set([1,2,3])
        goal_subs = [set([1,2,3]), set([1,2,3])]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)

    def test_reduce2(self):


        row1 = {'field1' : 'a', 
               'field2' : 'b',
               sv.VARS.ID : 1}
        result1 = self.agg.map(row1)

        
        row2 = {'field1' : 'a', 
               'field2' : None,
               sv.VARS.ID : 2}
        result2 = self.agg.map(row2)


        row3 = {'field1' : None, 
               'field2' : 'b',
               sv.VARS.ID : 3}
        result3 = self.agg.map(row3)

        result = self.agg.reduce(result1,
                                 self.agg.reduce(result2,
                                                 result3))

        goal_toplevel = set([1,2,3])
        goal_subs = [set([1,2]), set([1,3])]
        goal = ca.CompoundResult(goal_toplevel, goal_subs)
        self.assertEqual(result, goal)




class CompoundCollectorTest(unittest.TestCase):
    """
    Test that the ConjunctiveCollector and DisjunctiveCollector 
    classes acts as expected when embedded in each other.
    """


    def setUp(self):
        
        sub_agg1 = aqa.EqualityCollector('field1', 'a')
        sub_agg2 = aqa.EqualityCollector('field2', 'b')
        sub_sub_aggs = [sub_agg1, sub_agg2]
        sub_agg = ca.DisjunctiveCollector(sub_sub_aggs)
        
        sub_agg3 = aqa.EqualityCollector('field3', 'c')
        sub_aggs = [sub_agg, sub_agg3]
        self.agg = ca.ConjunctiveCollector(sub_aggs)



    def test_fields_needed(self):
        fn = self.agg.fields_needed()
        goal = set(['field1', 'field2', 'field3'])
        self.assertSetEqual(fn, goal)


    def test_map1(self):

        row = {'field1' : 'a', 
               'field2' : 'b',
               'field3' : 'c',
               sv.VARS.ID : 1}
        result = self.agg.map(row)

        goal = ca.CompoundResult(set([1]), # top-level
                                 [ca.CompoundResult(set([1]),
                                                    [set([1]), set([1])]),
                                  # disjunctive result
                                  set([1])])  # agg3
        self.assertEqual(result, goal)




    def test_map2(self):

        row = {'field1' : 'a', 
               'field2' : None,
               'field3' : 'c',
               sv.VARS.ID : 1}
        result = self.agg.map(row)

        goal = ca.CompoundResult(set([1]), # top-level
                                 [ca.CompoundResult(set([1]),
                                                    [set([1]), set()]),
                                  # disjunctive result
                                  set([1])])  # agg3
        self.assertEqual(result, goal)


    def test_map3(self):

        row = {'field1' : None, 
               'field2' : None,
               'field3' : 'c',
               sv.VARS.ID : 1}
        result = self.agg.map(row)

        goal = ca.CompoundResult(set(), # top-level
                                 [ca.CompoundResult(set(),
                                                    [set(), set()]),
                                  # disjunctive result
                                  set([1])])  # agg3
        self.assertEqual(result, goal)


    def test_map4(self):

        row = {'field1' : 'a', 
               'field2' : 'b',
               'field3' : None,
               sv.VARS.ID : 1}
        result = self.agg.map(row)

        goal = ca.CompoundResult(set(), # top-level
                                 [ca.CompoundResult(set([1]),
                                                    [set([1]), set([1])]),
                                  # disjunctive result
                                  set()])  # agg3
        self.assertEqual(result, goal)




    def test_reduce1(self):


        row1 = {'field1' : 'a', 
               'field2' : 'b',
               'field3' : 'c',
               sv.VARS.ID : 1}
        result1 = self.agg.map(row1)

        
        row2 = {'field1' : 'a', 
               'field2' : 'b',
               'field3' : 'c',
               sv.VARS.ID : 2}
        result2 = self.agg.map(row2)


        row3 = {'field1' : 'a', 
               'field2' : 'b',
               'field3' : 'c',
               sv.VARS.ID : 3}
        result3 = self.agg.map(row3)

        result = self.agg.reduce(result1,
                                 self.agg.reduce(result2,
                                                 result3))

        goal = ca.CompoundResult(set([1,2,3]), # top-level
                                 [ca.CompoundResult(set([1,2,3]),
                                                    [set([1,2,3]), 
                                                     set([1,2,3])]),
                                  # disjunctive result
                                  set([1,2,3])])  # agg3
        self.assertEqual(result, goal)


    def test_reduce2(self):


        row1 = {'field1' : 'a', 
               'field2' : None,
               'field3' : 'c',
               sv.VARS.ID : 1}
        result1 = self.agg.map(row1)

        
        row2 = {'field1' : None, 
               'field2' : 'b',
               'field3' : 'c',
               sv.VARS.ID : 2}
        result2 = self.agg.map(row2)


        row3 = {'field1' : None, 
               'field2' : None,
               'field3' : None,
               sv.VARS.ID : 3}
        result3 = self.agg.map(row3)

        result = self.agg.reduce(result1,
                                 self.agg.reduce(result2,
                                                 result3))

        goal = ca.CompoundResult(set([1,2]), # top-level
                                 [ca.CompoundResult(set([1,2]),
                                                    [set([1]), 
                                                     set([2])]),
                                  # disjunctive result
                                  set([1,2])])  # agg3
        self.assertEqual(result, goal)

