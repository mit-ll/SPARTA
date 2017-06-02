# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 multiplication gate calss test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_wire as iw
import ibm_gate_mul as igm
import ibm_circuit as ic
import unittest

class TestMulGate(unittest.TestCase):

    def test_get_full_display_string(self):
        """
        Tests that the method get_full_display_string returns the correct
        string.
        """
        #Initialize the circuit:
        circuit = ic.IBMCircuit(10)
        #Initialize the input wires:
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        #Initialize the gate:
        g = igm.IBMMulGate("g", w1, w2, circuit)
        self.assertEquals("g:LMUL(w1,w2)", g.get_full_display_string())
        
    def test_get_depth(self):
        """
        Tests that the get_depth method returns the correct depth, as defined
        by IBM.
        """
        circuit = ic.IBMCircuit(10)
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        w3 = iw.IBMInputWire("w3", circuit)
        w4 = iw.IBMInputWire("w4", circuit)
        g1 = igm.IBMMulGate("g1", w1, w2, circuit)
        g2 = igm.IBMMulGate("g2", g1, w3, circuit)
        g3 = igm.IBMMulGate("g3", g2, w4, circuit)
        self.assertEqual(1, g1.get_depth())
        self.assertEqual(2, g2.get_depth())
        self.assertEqual(3, g3.get_depth())
 
