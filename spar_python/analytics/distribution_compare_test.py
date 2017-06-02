# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JL
#  Description:        This is the test for the distribution comparison code.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  31 July 2012  JL             Original Version
# *****************************************************************
import random

import distribution_compare as dc

import single_percentile_comparator as sp

import unittest

class percentile_test(unittest.TestCase):

    def test_samelist(self): 
        """
        Two lists of identical times should trivially satisfy the criteria in
        the BAA. This checks that our distribution_compare method correctly
        returns True in this case.
        """
        list_a = [1,2,3,4,5,6,7,8]
        random.shuffle(list_a)
        list_b = [1,2,3,4,5,6,7,8]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, True)

    def test_smalllarge(self): 
        """
        When the first list is several orders of magnitude larger than the
        second list, it is expected that the distribution_compare method will
        return False.
        """
        list_a = [1000,2000,3000,4000,5000,6000,7000,8000]
        random.shuffle(list_a)
        list_b = [1,2,3,4,5,6,7,8]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, False)

    def test_largesmall(self):
        """
        When the lists from the previous test case are swapped, it is expected
        that the distribution_compare function will return True.
        """
        list_a = [1,2,3,4,5,6,7,8]
        random.shuffle(list_a)
        list_b = [1000,2000,3000,4000,5000,6000,7000,8000]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, True)

    def test_onefalse(self): 
        """
        When the comparisons should all be True except for one, then the
        distribution_compare returns False.
        """
        list_a = [1,2,3,4,5000,6,7,8]
        random.shuffle(list_a)
        list_b = [1,2,3,4,5,6,7,8]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, False)
        
    def test_allequal(self): 
        """
        When the values are made equal through the BAA criteria, it is
        expected that the method will return True.
        """
        list_a = [25,35,45,55,65,75,85,95]
        random.shuffle(list_a)
        list_b = [1,2,3,4,5,6,7,8]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, True)	

    def test_justwithin(self):
        """
        When the values for the first list are just within the accepted range
        of the BAA criteria, it is expected that the method will return True.
        """
        list_a = [24,34,44,54,64,74,84,94]
        random.shuffle(list_a)
        list_b = [1,2,3,4,5,6,7,8]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, True)

    def test_justoutside(self):
        """
        When the values for the first list are just outside the accepted range
        of the BAA criteria, it is expected that the method will return False.
        """
        list_a = [26,36,46,56,66,76,86,96]
        random.shuffle(list_a)
        list_b = [1,2,3,4,5,6,7,8]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, False)


    def test_emptysets(self):
        """
        When there are two empty sets, it is expected that the method would
        raise an Assertion Error.
        """
        self.assertRaises(AssertionError, dc.distribution_compare,
                          sp.baa_criteria, [], [])	

    def test_emptyset1(self):
        """
        When the first list is empty, it is expected that the method would
        raise an Assertion Error.
        """
        list_b = [1,2,3,4,5,6,7,8]
        random.shuffle(list_b)
        self.assertRaises(AssertionError, dc.distribution_compare,
                          sp.baa_criteria, [], list_b)

    def test_emptyset2(self):
        """
        When the second list is empty, it is expected that the method would
        raise an Assertion Error.
        """
        list_a = [1,2,3,4,5,6,7,8]
        random.shuffle(list_a)
        self.assertRaises(AssertionError, dc.distribution_compare,
                          sp.baa_criteria, list_a, [])

    def test_unevennumbers (self):
        """
        Even when the lists are of different sizes, if the matching values are
        all the same, then the method will return True.
        """
        list_a = [1,2,3,4,5,6,7,8,9]
        random.shuffle(list_a)
        list_b = [1000,2000,3000,4000,5000,6000,7000,8000]
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, True)

    def test_largelists (self):
        """
        When the lists are extremely large, the method will return True if all
        the values pass the criteria.
        """
        list_a = range(10, 10001)
        random.shuffle(list_a)
        list_b = range(10, 10001)
        random.shuffle(list_b)
        t = dc.distribution_compare(sp.baa_criteria,list_a,list_b)
        self.assertEqual(t, True)

    def test_onenumberlist (self):
        """
        Even when the lists contain only one object, the method should still
        return True.
        """
        t = dc.distribution_compare(sp.baa_criteria, [64], [5])
        self.assertEqual(t, True)
 
