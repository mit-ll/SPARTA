# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 select calss test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_batch as ib
import ibm_wire as iw
import ibm_gate_select as igs
import ibm_circuit as ic
import unittest
import spar_python.circuit_generation.circuit_common.circuit_input as ci

class TestSelectGate(unittest.TestCase):

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
        #Initialize the constant:
        const = ci.Input([ib.IBMBatch([1, 0])])
        #Initialize the gate:
        g = igs.IBMSelectGate("g", w1, w2, const, circuit)
        self.assertEquals(g.get_full_display_string(), "g:LSELECT(w1,w2,[10])")

    def test_get_depth(self):
        """
        Tests that the get_depth method returns the correct depth, as defined
        by IBM.
        """
        circuit = ic.IBMCircuit(10)
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        const = ci.Input([ib.IBMBatch([1, 0, 1])])
        g1 = igs.IBMSelectGate("g1", w1, w2, const, circuit)
        self.assertEqual(.6, g1.get_depth())
 
