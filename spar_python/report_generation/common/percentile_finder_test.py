# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JL
#  Description:        This is the test for the percentile finder code.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  26 July 2012  JL             Original Version
#  27 July 2012  JL             Added range boundary and sort test cases
#  30 July 2012  JL             Added test_midrange_odd
# *****************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.report_generation.common.percentile_finder as pf

class percentile_test(unittest.TestCase):

    def test_midrange_even(self): 
        """
        To see what the function does with a four-item list and a 50th percentile
        """
        x = pf.PercentileFinder([10, 20, 30, 40])
        t = x.getPercentile(50)
        self.assertEqual(t, 20)

    def test_midrange_odd(self): 
        """
        To see what the function does with a five-item list and a 50th percentile
        """
        x = pf.PercentileFinder([10, 20, 30, 40, 50])
        t = x.getPercentile(50)
        self.assertEqual(t, 30)
        
    def test_twonumberlow(self): 
        """
        To see what the function does with a two-item list and a low percentile
        """
        x = pf.PercentileFinder([5,6])
        t = x.getPercentile(1)
        self.assertEqual(t, 5)
        
    def test_nullset(self): 
        """
        To see what the function does with a null set
        """
        x = pf.PercentileFinder([])
        t = x.getPercentile(25)
        self.assertEqual(t, None)	

    def test_range1(self):
        """
        To see what happens when the percentile is at the top of the accepted range
        """
        x = pf.PercentileFinder([1,2,3,4,5,6])
        t = x.getPercentile(100)
        self.assertEqual(t, 6)
        
    def test_range2(self):
        """
        To see what happens when the percentile is below of the accepted range
        """
        x = pf.PercentileFinder([1,2,3,4,5,6])
        self.assertRaises(AssertionError, x.getPercentile, 0)
        
    def test_range3(self):
        """
        To see what happens when the percentile is towards the lower range boundary
        """
        x = pf.PercentileFinder([1,2,3,4,5,6,7,8])
        t = x.getPercentile(1)
        self.assertEqual(t, 1)

    def test_range4(self):
        """
        To see what happens when the percentile is towards the upper range boundary
        """
        x = pf.PercentileFinder([1,2,3,4,5,6,7,8])                 
        t = x.getPercentile(99)
        self.assertEqual(t, 8)

    def test_range5(self):
        """
        To see what happens when the percentile is above of the accepted range
        """
        x = pf.PercentileFinder([1,2,3,4,5,6])
        self.assertRaises(AssertionError, x.getPercentile, 101)
        
    def test_twonumber(self):
        """
        To see what happens when there is a two-number list
        """
        x = pf.PercentileFinder([0,5])
        t = x.getPercentile(50)
        self.assertEqual(t, 0)

    def test_stringpercentile(self):
        """
        To see what happens when there is a string for the percentile
        """
        x = pf.PercentileFinder([0,5])
        self.assertRaises(AssertionError, x.getPercentile, 'Hi!')

    def test_largelist (self):
        """
        To see what happens when the list given is enormous.
        """
        my_list = range(1, 10000)
        x = pf.PercentileFinder(my_list)
        t = x.getPercentile(75)
        self.assertEqual(t, 7500)

    def test_sort (self):
        """
        To see if the sorting truly works
        """
        x = pf.PercentileFinder([8,1,7,2,6,3,5,4])                 
        t = x.getPercentile(50)
        self.assertEqual(t, 4)
 
