# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 batch class test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  14 Nov 2012   SY             Original Version
# *****************************************************************

import ibm_batch as ib
import unittest

class TestBatch(unittest.TestCase):

    def test_display(self):
        """
        Tests the display method in the IBMBatch class works as intended.
        """
        batch = ib.IBMBatch([1,2,3])
        self.assertEqual("123", str(batch))

    def test_get_num_values(self):
        batch = ib.IBMBatch([1, 0, 1, 0, 0])
        self.assertEqual(2, batch.get_num_values(1))
        self.assertEqual(3, batch.get_num_values(0))
 
