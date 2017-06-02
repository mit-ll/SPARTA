# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 two input gate superclass test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 Nov 2012    SY             Original Version
# *****************************************************************

import ibm_wire as iw
import ibm_gate_two_inps as igti
import ibm_circuit as ic
import unittest

class TestGateTwoInpAndConst(unittest.TestCase):

    def test_get_inputs(self):
        """
        Tests that the get_inputs method functions as expected.
        """
        L = 20
        circuit = ic.IBMCircuit(L)
        gate_name = "g"
        D = 10
        input1 = iw.IBMInputWire("w1", circuit)
        input2 = iw.IBMInputWire("w2", circuit)
        g = igti.IBMGateTwoInps(gate_name, D, input1, input2, circuit)
        self.assertEqual([input1, input2], g.get_inputs())


