# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 gate superclass test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 Nov 2012    SY             Original Version
# *****************************************************************

import ibm_circuit as ic
import ibm_wire as iw
import ibm_gate as ig
import unittest

class TestGate(unittest.TestCase):

    def test_unimplemented_methods(self):
        """
        Tests that calling methods which are only implemented in subclasses
        causes errors.
        """
        L = 10
        circuit = ic.IBMCircuit(L)
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        D = 10
        level = 9
        g = ig.IBMGate("g", D, level, circuit)
        # AssertionError expected:
        self.assertRaises(AssertionError,
                          g.get_func_name)

