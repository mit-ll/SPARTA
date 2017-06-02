# -*- coding: utf-8 -*-

# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 AND gate class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
#  08 Nov 2012   SY             Incorporated Oliver's feedback
# *****************************************************************

import spar_python.circuit_generation.stealth.stealth_gate as sg
import spar_python.common.spar_random as sr

class StealthAndGate(sg.StealthGate):
    """
    This class represents an AND gate. It is a subclass of StealthGate.

    Simple use:
    # Instantiate the inputs to our AND gate as follows:
    wire1 = StealthInputWire("wire1", True)
    wire2 = StealthInputWire("wire2", False)
    # Instantiate our AND gate as follows:
    this_gate = StealthAndGate("this_gate",[wire1,wire2],[False,False])
    # Our AND gate can be prompted to return its value as follows:
    val = this_gate.evaluate()
    # val will be equal to False.
    """
    def __init__(self, displayname, inputs, negations):
        sg.StealthGate.__init__(self, displayname, inputs, negations)

    def get_func_name(self):
        """Returns the name of the function which this gate evaluates ("AND").
        """
        return "AND"

    def _evaluate_based_on_inputs(self):
        """Uses the inputs to compute the output of the AND gate."""
        return all((self._get_value_with_negation(eval_ind)
                    for eval_ind in xrange(self.get_num_inputs())))
        
    def balance(self, desired_output):
        """Changes the negations on the inputs of this gate so that the gate
        yeilds the bit desired_output."""
        assert(desired_output == True or desired_output == False)
        current_eval = self.evaluate()
        # if the gate does not currently evaluate to the desired_output, tweak
        # the negations in such a way as to force it to evaluate to the
        # desired_output:
        if current_eval != desired_output:
            if (desired_output == False):
                # if the gate does not currently evaluate to False, we can get
                # it to do so by flipping a single negation:
                inp_ind = sr.randint(0, self.get_num_inputs() - 1)
                self._negate(inp_ind)
            else:
                # Getting an AND to evaluate to True is harder; we must make
                # sure that every input evaluates to True.
                for bal_ind2 in xrange(self.get_num_inputs()):
                    if self._get_value_with_negation(bal_ind2) == False:
                        self._negate(bal_ind2)
            self._set_value(desired_output)
