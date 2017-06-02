# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 wire class test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_circuit as ic
import ibm_wire as iw
import unittest

class TestWire(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_depth(self):
        """
        Test that getting depth returns 0.0.
        """
        L = 15
        circuit = ic.IBMCircuit(L)
        w1_name = "w1"
        w1 = iw.IBMInputWire(w1_name, circuit)
        self.assertEquals(0, w1.get_depth())

    def test_get_level(self):
        """
        Test that getting level returns 0.
        """
        L = 15
        circuit = ic.IBMCircuit(L)
        w1_name = "w1"
        w1 = iw.IBMInputWire(w1_name, circuit)
        self.assertEquals(0, w1.get_level())

