# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 rotation calss test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_wire as iw
import ibm_gate_rotate as igr
import ibm_circuit as ic
import unittest

class TestRotateGate(unittest.TestCase):

    def test_get_full_display_string(self):
        """
        Tests that the method get_full_display_string returns the correct
        string.
        """
        #Initialize the circuit:
        circuit = ic.IBMCircuit(10)
        #Initialize the input wires:
        w1 = iw.IBMInputWire("w1", circuit)
        #Initialize the gate:
        g = igr.IBMRotateGate("g", w1, 5, circuit)
        self.assertEquals("g:LROTATE(w1,5)", g.get_full_display_string())

    def test_get_depth(self):
        """
        Tests that the get_depth method returns the correct depth, as defined
        by IBM.
        """
        circuit1 = ic.IBMCircuit(600)
        w1 = iw.IBMInputWire("w1", circuit1)
        g1 = igr.IBMRotateGate("g1", w1, 3, circuit1)
        self.assertEqual(.75, g1.get_depth())
        circuit2 = ic.IBMCircuit(650)
        w2 = iw.IBMInputWire("w2", circuit2)
        g2 = igr.IBMRotateGate("g2", w2, 3, circuit2)
        self.assertEqual(.25, g2.get_depth())
        circuit3 = ic.IBMCircuit(570)
        w3 = iw.IBMInputWire("w3", circuit3)
        g3 = igr.IBMRotateGate("g3", w3, 3, circuit3)
        self.assertEqual(.5, g3.get_depth())

