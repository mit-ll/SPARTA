# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 circuit class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2012   SY             Original Version
# *****************************************************************
    
class StealthCircuit(object):
    """
    This class represents a Stealth TA2 circuit.
    It stores all of the gates and wires of a circuit, organized by level.
    Speficially, it stores a list called 'levels';
    the first element of this list is a list of input wires,
    and all subsequent elements are lists of gates at various levels.
    The last element should have length one, and should be the output gate.

    Simple use:
    # Let output_gate be a gate, and wire0 and wire1 be wires which serve as
    # inputs to output_gate.
    # a circuit can be instantiated as follows:
    circuit = Circuit([wire0, wire1],output_gate)
    # It can be evaluated on input [True, False] as follows:
    circuit.evaluate([True, False])
    # The circuit can be prompted to print itself out as follows:
    circuit.display()
    """
    def __init__(self, input_wires, output_gate):
        """initializes the circuit with a list of input wires,
        and an output gate."""
        self.__output_gate = output_gate
        self.__input_wires = input_wires
        # self.__levels is a list of the circuit's levels. It is set the first
        # time the get_levels() method is called.
        self.__levels = None

    def get_num_inputs(self):
        """returns the number of input wires of the circuit"""
        return len(self.__input_wires)

    def __init_levels(self):
        """Initializes the levels."""
        # Populate self.__levels by doing a breadth-first crawl of the circuit.
        self.__levels = [[] for level_index
                         in xrange(self.__output_gate.get_level() + 1)]
        # Object_stack is a stack of circuit objects; circuit objects are
        # popped one by one. When a circuit object is popped, it is inserted
        # into the appropriate level in self.__levels, and its inputs are
        # pushed onto the stack to eventually be processed as well (unless
        # they have already been processed).
        object_stack = [self.__output_gate]
        while len(object_stack) > 0:
            this_object = object_stack.pop()
            this_level = this_object.get_level()
            if (this_object not in self.__levels[this_level]):
                self.__levels[this_level].append(this_object)
                if this_level > 1:
                    for other_object in this_object.get_inputs():
                        object_stack.append(other_object)

    def get_levels(self):
        """Returns the circuit's levels"""
        if self.__levels == None:
            self.__init_levels()
        return self.__levels

    def display(self):
        """returns display string for the circuit"""
        return "\nL\n".join([""]+["\n".join([gate.get_full_display_string()
                                              for gate in level])
                           for level in self.get_levels()[1:]])        

    def __set_input(self, input_val_list):
        """Takes in an input_val_list, which should contain
        W lists of L bits each.
        It sets each of the W lists as the value of the appropriate input wire.
        """
        for wire_index in range(len(self.__input_wires)):
            self.__input_wires[wire_index].set_input(input_val_list[wire_index])

    def __wipe_input(self):
        """Wipes the input from all of the input wires."""
        self.__output_gate.wipe_input()

    def evaluate(self, input_val_list):
        """evaluates this circuit on the given input"""
        self.__wipe_input()
        self.__set_input(input_val_list)
        output = self.__output_gate.evaluate()
        return output
