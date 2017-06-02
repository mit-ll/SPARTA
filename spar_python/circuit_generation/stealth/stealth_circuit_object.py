# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 circuit object superclass 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original version
# *****************************************************************

class StealthCircuitObject(object):
    """
    This superclass represents any object (a wire or gate) found in a
    Stealth circuit. This class is never meant to be instantiated; only
    its subclasses are. It holds some fields and methods common to all
    circuit objects, such as:
    1. The field self.__displayname, containing the name of the wire or gate.
    2. The method get_name, which returns the name of the wire or gate.
    3. The method get_short_display_string, which returns the string
        representing the wire or gate when it serves as input to another gate.
    4. The method __str__, which returns a string representation of the wire
        or gate. __str__ currently simply returns the wire or gate name.
    """
    def __init__(self, displayname):
        """Initializes the object with the displayname."""
        assert(len(displayname) > 0)
        self.__name = displayname

    def get_name(self):
        """Returns the displayname of the object."""
        return self.__name

    def set_name(self, name):
        """Sets the displayname of the object."""
        self.__name = name

    def get_short_display_string(self, negation):
        """Returns the string representing the circuit object when it serves as
        an input to a gate. For an unnegated gate G3 or wire W24, this would
        simply be "G3" or "W24". For a negated gate G3 or wire W24, this would
        be "N(G3)" or "N(W4)"."""
        assert(negation == True or negation == False)
        if negation:
            return "".join(["N(",self.get_name(),")"])
        else:
            return self.get_name()

    def __str__(self):
        """Returns the string representation of this object, unnegated."""
        return self.get_name()

    def evaluate(self):
        """This returns the output of the circuit object. This should never be
        called from the abstract superclass CircuitObject."""
        # This method should be overriden in the subclasses.
        assert False
