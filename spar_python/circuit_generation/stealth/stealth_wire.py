
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 wire class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
# *****************************************************************

import spar_python.circuit_generation.stealth.stealth_circuit_object as sco

class StealthInputWire(sco.StealthCircuitObject):
    """
    This class represents a single input wire.
    It extends the StealthCircuitObject class.

    Simple use:
    # An input wire can be instantiated as follows:
    wire = StealthInputWire("my_input_wire", True)
    # And it can be prompted to return its assigned input as follows:
    inp = wire.evaluate()
    # inp will be equal to True.

    """
    
    def __init__(self, displayname, value):
        """Initializes the wire with the display name and value specified."""
        sco.StealthCircuitObject.__init__(self, displayname)
        self.set_input(value)

    def set_input(self, value):
        """Sets the value of the input wire to value."""
        self.__value = value

    def wipe_input(self):
        """Sets the value of the input wire to None. This should cause an error
        to be thrown during evaluation."""
        self.__value = None
    
    def evaluate(self):
        """Returns the value of the input wire."""
        assert(self.__value == True or self.__value == False)
        return self.__value

    def get_level(self):
        """Returns the level of the wire, which is always 0."""
        return 0
