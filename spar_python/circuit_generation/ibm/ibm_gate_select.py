# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 select gate class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 Nov 2012    SY             Original Version
# *****************************************************************

import ibm_gate_two_inps_and_const as igtiac
import ibm_batch as ib

class IBMSelectGate(igtiac.IBMGateTwoInpsAndConst):
    """
    This class represents a select gate. 
    """
    def __init__(self, displayname, input1, input2, constant, circuit):
        """Initializes the gate."""
        D = max(input1.get_depth(), input2.get_depth()) + .6
        igtiac.IBMGateTwoInpsAndConst.__init__(self, displayname, D, input1,
                                               input2, constant, circuit)

    def get_func_name(self):
        """Returns the name of the function which this gate evaluates."""
        return "LSELECT"
