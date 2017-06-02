# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 circuit object superclass 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 Oct 2012   SY             Original version
# *****************************************************************

class IBMCircuitObject(object):
    """
    This superclass represents any object (a wire or gate) found in an
    IBM circuit. This class is never meant to be instantiated; only
    its subclasses are. It holds some fields and methods common to all
    circuit objects.
    """
        
    def __init__(self, displayname, D, level, circuit):
        """Initializes the object with the displayname, depth, level,
        and circuit."""
        self.__name = str(displayname)
        assert(len(self.__name) > 0)
        # currently depth is only measured in increments of .1. if this changes,
        # the following line will also have to change:
        self.__D = round(float(D), 2)
        self.__level = int(level)
        self.__circuit = circuit

    def get_name(self):
        """Returns the displayname of the object."""
        return self.__name

    def get_depth(self):
        """Returns the depth of the circuit object, as defined by IBM."""
        return self.__D

    def get_level(self):
        """Returns the level of the circuit object."""
        return self.__level

    def get_batch_size(self):
        """Returns the batch size used in the circuit object."""
        return self.__circuit.get_batch_size()

    def __str__(self):
        """Returns the string representation of this object, unnegated."""
        return self.get_name()
