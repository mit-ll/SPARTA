
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 wire class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_circuit_object as ico

class IBMInputWire(ico.IBMCircuitObject):
    """
    This class represents a single IBM input wire.
    """
    
    def __init__(self, displayname, circuit):
        """Initializes the wire with the display name and circuit specified."""
        ico.IBMCircuitObject.__init__(self, displayname, 0.0, 0, circuit)
