# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 one input and constant gate superclass test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 Nov 2012    SY             Original Version
# *****************************************************************

import ibm_wire as iw
import ibm_gate_one_inp_and_const as igoiac
import ibm_circuit as ic
import unittest

class TestGateOneInpAndConst(unittest.TestCase):

    def test_get_inputs(self):
        """
        Tests that the get_inputs method functions as expected.
        """
        L = 20
        circuit = ic.IBMCircuit(L)
        gate_name = "g"
        D = 10
        input1 = iw.IBMInputWire("w1", circuit)
        const = "constant"
        g = igoiac.IBMGateOneInpAndConst(gate_name, D, input1, const, circuit)
        self.assertEqual([input1], g.get_inputs())

