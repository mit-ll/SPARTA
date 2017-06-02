# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 rotate gate class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 Nov 2012    SY             Original Version
# *****************************************************************

import ibm_gate_one_inp_and_const as igoiac
import ibm_batch as ib

class IBMRotateGate(igoiac.IBMGateOneInpAndConst):
    """
    This class represents a rotate gate.
    """
    def __init__(self, displayname, input1, const, circuit):
        """Initializes the gate."""
        if input1.get_batch_size() == 600:
            additional_depth = .75
        elif input1.get_batch_size() > 600:
            # possible batch sizes greater than 600 are 682 and 630.
            additional_depth = .25
        elif input1.get_batch_size() < 600:
            # possible batch sizes smaller than 600 are 256 and 378.
            additional_depth = .5
        D = input1.get_depth() + additional_depth
        igoiac.IBMGateOneInpAndConst.__init__(self, displayname, D, input1,
                                              int(const), circuit)

    def get_func_name(self):
        """Returns the name of the function which this gate evaluates."""
        return "LROTATE"
