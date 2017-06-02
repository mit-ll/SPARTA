# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 circuit class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2012   SY             Original Version
# *****************************************************************
    
class IBMCircuit(object):
    """
    This class represents an IBM TA2 circuit.
    It stores all of the gates and wires of a circuit, organized by level.
    Speficially, it stores a list called 'levels';
    the first element of this list is a list of input wires,
    and all subsequent elements are lists of gates at various levels.
    The last element should have length one, and should be the output gate.
    """
    def __init__(self, L):
        """Initializes the circuit with a batch size L."""
        self.__L = int(L)
        # self.__levels is a list of the circuit's levels, and is set when
        # the levels first need to be accessed.
        self.__levels = None

    def set_input_wires(self, input_wires):
        """Sets the input wires"""
        self.__input_wires = input_wires

    def set_output_gate(self, output_gate):
        """Sets the output gate."""
        self.__output_gate = output_gate

    def get_depth(self):
        """Returns the depth (as measured by IBM) of the circuit"""
        return self.__output_gate.get_depth()

    def get_batch_size(self):
        """Returns the batch size used in the circuit"""
        return self.__L

    def get_num_levels(self):
        """Returns the number of levels in the circuit"""
        return self.__output_gate.get_level()

    def get_num_inputs(self):
        """Returns the number of input wires of the circuit"""
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

    def get_num_gates(self, gate_func_name=None):
        """Returns the number of gates (with the given function name if
        provided)"""
        num_gates = 0
        for level in self.get_levels()[1:] + [[self.__output_gate]]:
            for gate in level:
                if ((not gate_func_name) or
                    (gate.get_func_name() == gate_func_name)):
                    num_gates += 1
        return num_gates

    def get_output_gate_func(self):
        """Returns the name of the output gate function"""
        return self.__output_gate.get_func_name()

    def display(self):
        """Returns display string for the circuit. This is the string that
        is then given to the IBM server prototype as a representation of this
        circuit."""
        param_string = "".join(["W=",
                                str(self.get_num_inputs()),
                                ",D=",
                                str(self.get_depth()),
                                ",L=",
                                str(self.get_batch_size())])
        return "\n".join([param_string] +
                         ["\n".join((gate.get_full_display_string()
                                     for gate in level))
                          for level in self.get_levels()[1:]])  
