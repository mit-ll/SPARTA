
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 gate superclass 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 Oct 2012   SY             Original Version
# *****************************************************************

import ibm_circuit_object as ico

class IBMGate(ico.IBMCircuitObject):
    """
    This class represents a boolean gate.
    It is an 'abstract' class extended by subclasses, one corresponding to
    each boolean gate type. The class IBMGate is never meant to be instantiated;
    only its subclasses are.
    """
    def __init__(self, displayname, D, level, circuit):
        """Initializes the gate with a display name, depth D, a level,
        and a circuit."""
        ico.IBMCircuitObject.__init__(self, displayname, D, level, circuit)
        
    def get_func_name(self):
        """Returns the name of the function which this gate evaluates.
        This should never be called from the abstract superclass IBMGate."""
        # This method should be overriden in the subclasses.
        assert(False)
