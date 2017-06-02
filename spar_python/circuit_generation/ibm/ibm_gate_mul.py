# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 multiplication gate class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 Nov 2012    SY             Original Version
# *****************************************************************

import ibm_gate_two_inps as igti
import ibm_batch as ib

class IBMMulGate(igti.IBMGateTwoInps):
    """
    This class represents a multiplication gate.
    """
    def __init__(self, displayname, input1, input2, circuit):
        """Initializes the gate."""
        D = max(input1.get_depth(), input2.get_depth()) + 1.0
        igti.IBMGateTwoInps.__init__(self, displayname, D, input1, input2,
                                     circuit)

    def get_func_name(self):
        """Returns the name of the function which this gate evaluates."""
        return "LMUL"
