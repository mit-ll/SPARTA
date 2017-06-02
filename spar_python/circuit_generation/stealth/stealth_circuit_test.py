# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 circuit class test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2012   SY             Original Version
# *****************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.circuit_generation.stealth.stealth_wire as sw
import spar_python.circuit_generation.stealth.stealth_gate_and as sga
import spar_python.circuit_generation.stealth.stealth_gate_or as sgo
import spar_python.circuit_generation.stealth.stealth_gate_xor as sgx
import spar_python.circuit_generation.stealth.stealth_circuit as sc
import spar_python.common.spar_random as sr

class TestAndGate(unittest.TestCase):

    def setUp(self):
        # create a simple sample circuit:
        w1 = sw.StealthInputWire("w1", True)
        w2 = sw.StealthInputWire("w2", True)
        w3 = sw.StealthInputWire("w3", False)
        g1 = sga.StealthAndGate("g1", [w1, w2], [True, False])
        g2 = sgo.StealthOrGate("g2", [g1, w3], [False, False])
        output_gate = sgx.StealthXorGate("og", [g1, g2],
                                         [False, False])
        self.circ = sc.StealthCircuit([w1, w2, w3], output_gate)


    def test_simple_circuit_example(self):
        """
        Tests that in the simple circuit example given above, the methods
        get_num_inputs, display, and evaluate work as intended.
        """
        self.assertEqual("\nL\ng1:AND(N(w1),w2)\nL\ng2:OR(g1,w3)\nL\nog:XOR(g1,g2)",
                         self.circ.display())
        self.assertEqual(3, self.circ.get_num_inputs())
        self.assertEqual(False, self.circ.evaluate([True, True, False]))
        self.assertEqual(True, self.circ.evaluate([True, True, True]))

    # TODO: need more tests here
 
