# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for ContingencyTable 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  02 Feb 2012   omd            Original Version
# *****************************************************************

from contingency_table import ContingencyTable
import unittest

class ContingencyTableTest(unittest.TestCase):
    def test_correct(self):
        # The test data is weight, tuple pairs where the tuple is a record and
        # the weight is the number of times that record should be counted.
        test_data = (
                (10, (True, 'hello', 7)),
                (2,  (True, 'goodbye', 7)),
                (3,  (True, 'hello', 7)),
                (1,  (False, 'goodbye', 22)),
                (5,  (False, 'fred', 18)))


        baset = ContingencyTable(test_data)

        self.assertEqual(baset[(True, 'hello', 7)], 13)
        self.assertEqual(baset[(True, 'goodbye', 7)], 2)
        self.assertEqual(baset.total_count, 21)

        # Make sure that if we iterate only the expected keys and values are
        # present and that all the expected ones are present
        base_keys = set([x for _, x in test_data])
        num_keys = 0
        for k, v in baset.iteritems():
            self.assertTrue(k in base_keys)
            self.assertTrue(v in (13, 2, 1, 5))
            num_keys += 1
        self.assertEqual(num_keys, 4)

        # Create a subtable from the 1st and 3rd values in the initial data
        sub1 = baset.get_subtable(0, 2)
        self.assertEqual(sub1[(True, 7)], 15)
        self.assertEqual(sub1[(False, 22)], 1)
        self.assertEqual(sub1[(False, 18)], 5)
        self.assertEqual(sub1.total_count, 21)

        # There should be fewer keys in the subtable.
        sub1_keys = set([(x[0], x[2]) for x in base_keys])
        for k in sub1.iterkeys():
            self.assertTrue(k in sub1_keys)

        # Create a subtable for just index 1
        sub2 = baset.get_subtable(1)
        self.assertEqual(sub2[('hello',)], 13)
        self.assertEqual(sub2[('goodbye',)], 3)
        self.assertEqual(sub2[('fred',)], 5)
        self.assertEqual(sub2.total_count, 21)

        self.assertEqual(len(sub2), 3)

    def test_none_keys(self):
        """This should handle keys that are tuples containing the value None.
        Make sure that works correctly."""
        test_data = (
                (5, (None, 5, None)),
                (3, (None, None, None)),
                (2, (2, 5, 1)),
                (10, (None, None, None)),
                (8, (1, 5, None)))

        base_t = ContingencyTable(test_data)

        self.assertEqual(base_t[(None, 5, None)], 5)
        self.assertEqual(base_t[(None, None, None)], 13)
        self.assertEqual(base_t.total_not_all_none_count, 15)

        subtable_1_2 = base_t.get_subtable(1, 2)
        self.assertEqual(subtable_1_2[(5, None)], 13)
        self.assertEqual(subtable_1_2[(None, None)], 13)
        self.assertEqual(subtable_1_2.total_not_all_none_count, 15)

        subtable_0_2 = base_t.get_subtable(0, 2)
        self.assertEqual(subtable_0_2[(None, None)], 18)
        self.assertEqual(subtable_0_2[(1, None)], 8)
        self.assertEqual(subtable_0_2[(2, 1)], 2)
        self.assertEqual(subtable_0_2.total_not_all_none_count, 10)



