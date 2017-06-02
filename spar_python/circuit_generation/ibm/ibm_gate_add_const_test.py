# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 add constant gate class test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_batch as ib
import ibm_wire as iw
import ibm_gate_add_const as igac
import ibm_gate_mul as igm
import ibm_circuit as ic
import unittest
import spar_python.circuit_generation.circuit_common.circuit_input as ci

class TestAddConstGate(unittest.TestCase):

    def test_get_full_display_string(self):
        """
        Tests that the method get_full_display_string returns the correct
        string.
        """
        #Initialize the circuit:
        circuit = ic.IBMCircuit(10)
        #Initialize the input wires:
        w1 = iw.IBMInputWire("w1", circuit)
        #Initialize the constant:
        const = ci.Input([ib.IBMBatch([True, False])])
        #Initialize the gate:
        g = igac.IBMAddConstGate("g", w1, const, circuit)
        self.assertEquals("g:LADDconst(w1,[10])", g.get_full_display_string())
        
    def test_get_depth(self):
        """
        Tests that the get_depth method returns the correct depth, as defined
        by IBM.
        """
        circuit = ic.IBMCircuit(10)
        w1 = iw.IBMInputWire("w1", circuit)
        g1 = igac.IBMAddConstGate("g1", w1, ib.IBMBatch([True, True]), circuit)
        g2 = igm.IBMMulGate("g2", g1, w1, circuit)
        g3 = igac.IBMAddConstGate("g3", g2, ib.IBMBatch([True, True]), circuit)
        self.assertEqual(0, g1.get_depth())
        self.assertEqual(1, g2.get_depth())
        self.assertEqual(1, g3.get_depth())

