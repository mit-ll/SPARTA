# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 circuit class test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2012   SY             Original Version
# *****************************************************************

import ibm_wire as iw
import ibm_gate_mul as igm
import ibm_gate_add as iga
import ibm_circuit as ic
import unittest
import spar_python.common.spar_random as sr

class TestAndGate(unittest.TestCase):

    def test_display(self):
        """
        Tests that the display method works as intended in a simple circuit.
        """
        # set the desired batch size:
        L = 10
        # create a simple sample circuit:
        circuit = ic.IBMCircuit(L)
        # create input wires:
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        w3 = iw.IBMInputWire("w3", circuit)
        # create gates:
        g1 = iga.IBMAddGate("g1", w1, w2, circuit)
        g2 = igm.IBMMulGate("g2", g1, w3, circuit)
        output_gate = iga.IBMAddGate("og", g1, g2, circuit)
        # set the circuit with the input wires and output gate:
        circuit.set_input_wires([w1, w2, w3])
        circuit.set_output_gate(output_gate)
        self.assertEqual(("W=3,D=1.2,L=10\ng1:LADD(w1,w2)\ng2:LMUL(g1,w3)"
                          "\nog:LADD(g1,g2)"),
                         circuit.display())

    def test_trim(self):
        """
        Tests that gates that do not lead to the output gate are not displayed.
        """
        # set the desired batch size:
        L = 10
        # create a simple sample circuit:
        circuit = ic.IBMCircuit(L)
        # create input wires:
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        w3 = iw.IBMInputWire("w3", circuit)
        # create gates that do lead to the output gate:
        g1 = iga.IBMAddGate("g1", w1, w2, circuit)
        g2 = igm.IBMMulGate("g2", g1, w3, circuit)
        # create a gate that does not lead to the output gate:
        g3 = iga.IBMAddGate("g3", w2, g2, circuit)
        # create the output gate:
        output_gate = iga.IBMAddGate("og", g1, g2, circuit)
        # set the circuit with the input wires and output gate:
        circuit.set_input_wires([w1, w2, w3])
        circuit.set_output_gate(output_gate)
        self.assertEqual(("W=3,D=1.2,L=10\ng1:LADD(w1,w2)\ng2:LMUL(g1,w3)"
                          "\nog:LADD(g1,g2)"),
                         circuit.display())

    def test_get_num_gates(self):
        # set the desired batch size:
        L = 10
        # create a simple sample circuit:
        circuit = ic.IBMCircuit(L)
        # create input wires:
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        w3 = iw.IBMInputWire("w3", circuit)
        # create gates that do lead to the output gate:
        g1 = iga.IBMAddGate("g1", w1, w2, circuit)
        g2 = igm.IBMMulGate("g2", g1, w3, circuit)
        # create a gate that does not lead to the output gate:
        g3 = iga.IBMAddGate("g3", w2, g2, circuit)
        # create the output gate:
        output_gate = iga.IBMAddGate("og", g1, g2, circuit)
        # set the circuit with the input wires and output gate:
        circuit.set_input_wires([w1, w2, w3])
        circuit.set_output_gate(output_gate)
        self.assertEqual(3, circuit.get_num_gates(gate_func_name="LADD"))
        self.assertEqual(1, circuit.get_num_gates(gate_func_name="LMUL"))

    def test_get_num_inputs(self):
        """
        Tests that the get_num_inputs method functions as expected.
        """
        # set the desired batch size:
        L = 10
        # create a simple sample circuit:
        circuit = ic.IBMCircuit(L)
        # create input wires:
        w1 = iw.IBMInputWire("w1", circuit)
        w2 = iw.IBMInputWire("w2", circuit)
        w3 = iw.IBMInputWire("w3", circuit)
        # create gates:
        g1 = iga.IBMAddGate("g1", w1, w2, circuit)
        g2 = igm.IBMMulGate("g2", g1, w3, circuit)
        output_gate = iga.IBMAddGate("og", g1, g2, circuit)
        # set the circuit with the input wires and output gate:
        circuit.set_input_wires([w1, w2, w3])
        circuit.set_output_gate(output_gate)
        self.assertEqual(3, circuit.get_num_inputs())

