
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 gate superclass 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original Version
#  08 Nov 2012   SY             Incorporated Oliver's feedback
# *****************************************************************

import spar_python.circuit_generation.stealth.stealth_circuit_object as sco
import spar_python.common.spar_random as sr

class StealthGate(sco.StealthCircuitObject):
    """
    This class represents a boolean gate (such as an AND gate,
    an OR gate, or a XOR gate).
    It is an 'abstract' class extended by the classes StealthOrGate,
    StealthAndGate and StealthXorGate. The class StealthGate is never meant to
    be instantiated; only its subclasses are.
    """
    def __init__(self, displayname, inputs, negations):
        """Initializes the gate with a display name,
        a list of inputs, and a list of
        bits indicating which inputs are negated (N(input)).
        Inputs should be either input wires or other gates."""
        sco.StealthCircuitObject.__init__(self, displayname)
        assert(len(inputs) == len(negations))
        assert(len(inputs) > 1)
        self.__inputs = inputs
        self.__negations = negations
        self.__num_inputs = len(self.__inputs)
        self.__level = max([inp.get_level() for inp in self.get_inputs()])+1
        # the value is set to None, since upon initialization, no value
        # is assumed.
        self.__value = None

    def get_num_inputs(self):
        """Returns the number of inputs."""
        return self.__num_inputs

    def get_inputs(self):
        """Returns the inputs to this gate."""
        return self.__inputs

    def get_level(self):
        """Returns the level this gate is at."""
        return self.__level

    def get_full_display_string(self):
        """Returns the string representing the wire. For instance, for gate G3,
        this might look something like "G3 = AND(G0,G1,N(G2))" (if G3 is the
        'and' of gates G0, G1, and the negation of G2), or it might be
        something like "G3 = OR(N(W2),W4)" (if G3 is the 'or' of the negation
        of wire W2 and wire W4.
        """
        inp_strs = (self.get_inputs()[i].get_short_display_string(self.__negations[i])
                  for i in xrange(self.get_num_inputs()))
        return "".join([self.get_name(),
                       ":",
                       self.get_func_name(),
                       "(",
                       ",".join(inp_strs),
                       ")"])
        
    def get_func_name(self):
        """Returns the name of the function which this gate evaluates
        ("AND", "OR" or "XOR"). This should never be called from the abstract
        superclass StealthGate."""
        # This method should be overriden in the subclasses.
        assert(False)

    def _evaluate_based_on_inputs(self):
        """Returns the output of the gate. Uses the inputs to compute the
        output of the gate, and assignes that value to self._value.
        This should never be called from the abstract superclass StealthGate."""
        # This method should be overriden in the subclasses.
        assert(False)

    def evaluate(self):
        """Returns the output of the gate. If the stored value is None,
        it is computed based on the gate's inputs, and only then returned."""
        if self.__value == None:
            self.__value = self._evaluate_based_on_inputs()
        return self.__value

    def _set_value(self, new_value):
        """Sets the value to new_value. Should only be called from the balance
        method, in order to avoid unnecessary reevaluation."""
        self.__value = new_value

    def wipe_input(self):
        """Wipes the stored value, and recursively does the same to this gate's
        inputs if needed."""
        if self.__value != None:
            self.__value = None
            for inp in self.get_inputs():
                inp.wipe_input()

    def balance(self, desired_output):
        """Changes the negations on the inputs of this gate so that the gate
        yeilds the bit desired_output. This should never be called from the
        abstract superclass StealthGate."""
        # This method should be overriden in the subclasses.
        assert(False)

    def _get_value_with_negation(self, inp_index):
        """Returns the value of the inp_index'th input, taking negations into
        account. In other words, returns not self.__inputs[inp_index] if
        self.__negations[inp_index] == True, and returns
        self.__inputs[inp_index] otherwise. """
        return self.__negations[inp_index]^self.__inputs[inp_index].evaluate()

    def _negate(self, inp_index):
        """Reverses the negation for the inp_index'th input. Recomputes the
        stored value, since the negations were changed."""
        self.__negations[inp_index] = not self.__negations[inp_index]
        self.__value = None

    def _randomize_negations(self):
        """Replaces the existing negations with new randomly chosen ones.
        Recomputes the stored value, since the negations were changed."""
        self.__negations = [bool(sr.randbit())
                            for bal_ind in xrange(len(self.get_inputs()))]
        self.__value = None
