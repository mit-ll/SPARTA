# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA2 input class test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  14 Nov 2012   SY             Original Version
# *****************************************************************

import circuit_input as ci
import unittest

class TestInput(unittest.TestCase):

    def test_display(self):
        """
        Tests the display method in the Input class works as intended.
        """
        elt1 = "element1"
        elt2 = "element2"
        inp = ci.Input([elt1, elt2])
        self.assertEqual("[element1,element2]", str(inp))
        
    def test_get_num_values(self):
        inp = ci.Input([0, 1, 1, 0, 1])
        self.assertEqual(3, inp.get_num_values(1))
        self.assertEqual(2, inp.get_num_values(0))
        inp = ci.Input([ci.Input([1, 1, 0]), ci.Input([1, 1, 1])])
        self.assertEqual(5, inp.get_num_values(1))
        self.assertEqual(1, inp.get_num_values(0))
        
