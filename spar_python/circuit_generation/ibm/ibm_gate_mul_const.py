# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 multiplication by constant gate class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 Nov 2012    SY             Original Version
# *****************************************************************

import ibm_gate_one_inp_and_const as igoiac
import ibm_batch as ib

class IBMMulConstGate(igoiac.IBMGateOneInpAndConst):
    """
    This class represents a mul by constant gate.
    """
    def __init__(self, displayname, input1, const, circuit):
        """Initializes the gate."""
        D = input1.get_depth() + .5
        igoiac.IBMGateOneInpAndConst.__init__(self, displayname, D,
                                              input1, const, circuit)

    def get_func_name(self):
        """Returns the name of the function which this gate evaluates."""
        return "LMULconst"
