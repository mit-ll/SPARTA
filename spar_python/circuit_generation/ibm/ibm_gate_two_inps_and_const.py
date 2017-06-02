
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 two input and constant gate superclass 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_gate as ig

class IBMGateTwoInpsAndConst(ig.IBMGate):
    """
    This class represents a boolean gate which takes in two inputs and a
    constant.
    """
    def __init__(self, displayname, D, input1, input2, const, circuit):
        """Initializes the gate with a display name, depth D, two inputs, and
        a circuit.
        Inputs should be either input wires or other gates."""
        level = max(input1.get_level(), input2.get_level()) + 1
        ig.IBMGate.__init__(self, displayname, D, level, circuit)
        self.__input1 = input1
        self.__input2 = input2
        self.__const = const

    def _get_input_1(self):
        """Returs the first input."""
        return self.__input1

    def _get_input_2(self):
        """Returns the second input."""
        return self.__input2

    def _get_const(self):
        """Returns the constant."""
        return self.__const

    def get_full_display_string(self):
        """Returns the string representing the gate, as it appears in the
        circuit that is given to the IBM server prototype."""
        inp_list = [self._get_input_1().get_name(),
                    self._get_input_2().get_name(),
                    str(self._get_const())]
        return "".join([self.get_name(),
                       ":",
                       self.get_func_name(),
                       "(",
                       ",".join(inp_list),
                       ")"])

    def get_inputs(self):
        """Returns the inputs to this gate."""
        return [self._get_input_1(), self._get_input_2()]
