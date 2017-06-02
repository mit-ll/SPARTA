# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        The circuit generation functions for IBM TA2 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  12 Nov 2012   SY             Original Version
# *****************************************************************

# general imports:
import functools

# SPAR imports:
import spar_python.circuit_generation.ibm.ibm_batch as ib
import spar_python.circuit_generation.circuit_common.circuit_input as ci
import spar_python.circuit_generation.ibm.ibm_wire as iw
import spar_python.circuit_generation.ibm.ibm_gate as ig
import spar_python.circuit_generation.ibm.ibm_gate_mul as igm
import spar_python.circuit_generation.ibm.ibm_gate_mul_const as igmc
import spar_python.circuit_generation.ibm.ibm_gate_add as iga
import spar_python.circuit_generation.ibm.ibm_gate_add_const as igac
import spar_python.circuit_generation.ibm.ibm_gate_rotate as igr
import spar_python.circuit_generation.ibm.ibm_gate_select as igs
import spar_python.circuit_generation.ibm.ibm_circuit as ic
import spar_python.common.spar_random as sr
import spar_python.common.enum as enum

gate_types = ['LADD', 'LADDconst', 'LMUL', 'LMULconst', 'LSELECT', 'LROTATE']
# An Enum of gate types:
GATE_TYPES = enum.Enum(*gate_types)
# An Enum of possible gate type distributions used in the tests
# (identical to GATE_TYPES, but include RANDOM as well):
test_types = gate_types + ['RANDOM']
TEST_TYPES = enum.Enum(*test_types)
# Note that much of the following code relies on the fact that GATE_TYPES and
# TEST_TYPES coincide in the first 6 elements.

# This file contains methods for creating random gates and circuits.

# Below are methods for creating random gates of each type,
# wherein the method takes in the last level of gates (ultimate_level),
# the second-to-last level of gates (penultimate_level),
# a gate name, and a circuit for which the gate is intended.
# Inputs are chosen so that at least one of them comes from ultimate_level;
# any constants are chosen uniformly at random.
# The penultimate level is passed in even for gate types requiring only one
# input, since then the gate creation functions can be called interchangeably.
# There is also a method for creating a gate where the gate type is chosen
# uniformly at random.

def make_random_two_inp_gate(L, ultimate_level, penultimate_level, gate_name,
                             circuit, gate_factory):
    """creates a random gate with two inputs."""
    # This gate requires two inputs; at least two inputs should be available.
    assert(len(ultimate_level) + len(penultimate_level) > 1)
    input1_index = sr.randint(0, len(ultimate_level) - 1)
    input1 = ultimate_level[input1_index]
    input2_index = sr.randint(0, len(ultimate_level) +
                              len(penultimate_level) - 1)
    while input2_index == input1_index:
        input2_index = sr.randint(0, len(ultimate_level) +
                                  len(penultimate_level) - 1)
    if input2_index < len(ultimate_level):
        input2 = ultimate_level[input2_index]
    else:
        input2 = penultimate_level[input2_index - len(ultimate_level)]
    return gate_factory(gate_name, input1, input2, circuit)

def make_random_one_inp_and_const_inp_gate(L, ultimate_level, penultimate_level,
                                           gate_name, circuit, gate_factory):
    """creates a random gate with one input and a constant that is an input
    batch."""
    # This gate requires one input; at least one input should be available.
    assert(len(ultimate_level) + len(penultimate_level) > 0)
    input1_index = sr.randint(0, len(ultimate_level) - 1)
    input1 = ultimate_level[input1_index]
    const = ci.Input([ib.IBMBatch([sr.randbit() for inp_ind in xrange(L)])])
    return gate_factory(gate_name, input1, const, circuit)

def make_random_one_inp_and_const_int_gate(L, ultimate_level, penultimate_level,
                                           gate_name, circuit, gate_factory):
    """creates a random gate with one input and a constant that is an integer.
    """
    # This gate requires one input; at least one input should be available.
    assert(len(ultimate_level) + len(penultimate_level) > 0)
    input1_index = sr.randint(0, len(ultimate_level) - 1)
    input1 = ultimate_level[input1_index]
    const = sr.randint(0, L - 1)
    return gate_factory(gate_name, input1, const, circuit)

def make_random_two_inp_and_const_inp_gate(L, ultimate_level, penultimate_level,
                                           gate_name, circuit, gate_factory):
    """creats a random gate with two inputs and a constant that is an input
    batch."""
    # This gate requires two inputs; at least two inputs should be available.
    assert(len(ultimate_level) + len(penultimate_level) > 1)
    input1_index = sr.randint(0, len(ultimate_level) - 1)
    input1 = ultimate_level[input1_index]
    input2_index = sr.randint(0, len(ultimate_level) +
                              len(penultimate_level) - 1)
    while input2_index == input1_index:
        input2_index = sr.randint(0, len(ultimate_level) +
                                  len(penultimate_level) - 1)
    if input2_index < len(ultimate_level):
        input2 = ultimate_level[input2_index]
    else:
        input2 = penultimate_level[input2_index - len(ultimate_level)]
    const = ci.Input([ib.IBMBatch([sr.randbit() for inp_ind in xrange(L)])])
    return gate_factory(gate_name, input1, input2, const, circuit)


# A dictionary mapping distribution type to generator which creates a random
# gate of that type, given L, the ultimate_level, penultimate_level, and a
# gate_name:
TEST_TYPE_TO_GATE_MAKER ={
    TEST_TYPES.LADD: functools.partial(make_random_two_inp_gate,
                                            gate_factory = iga.IBMAddGate),
    TEST_TYPES.LADDconst:
    functools.partial(make_random_one_inp_and_const_inp_gate,
                      gate_factory = igac.IBMAddConstGate),
    TEST_TYPES.LMUL:
    functools.partial(make_random_two_inp_gate,
                      gate_factory = igm.IBMMulGate),
    TEST_TYPES.LMULconst:
    functools.partial(make_random_one_inp_and_const_inp_gate,
                      gate_factory = igmc.IBMMulConstGate),
    TEST_TYPES.LSELECT:
    functools.partial(make_random_two_inp_and_const_inp_gate,
                      gate_factory = igs.IBMSelectGate),
    TEST_TYPES.LROTATE:
    functools.partial(make_random_one_inp_and_const_int_gate,
                      gate_factory = igr.IBMRotateGate)}

def make_random_gate(L, ultimate_level, penultimate_level, gate_name, circuit):
    """Creates a random gate with uniformly distributed type."""
    gate_type = sr.choice([g_type for g_type in GATE_TYPES.numbers_generator()])
    generate = TEST_TYPE_TO_GATE_MAKER[gate_type]
    return generate(L, ultimate_level, penultimate_level, gate_name, circuit)

TEST_TYPE_TO_GATE_MAKER[TEST_TYPES.RANDOM] =  make_random_gate

def make_random_input(L, W):
    """Creates a random input with W batches, each with L bits."""
    return ci.Input([ib.IBMBatch([sr.randbit() for inp_num in xrange(L)])
                     for batch_num in xrange(W)])

def generate_circuit_by_level(L, num_levels, W, gate_maker):
    """
    This function this generates a random IBM circuit with num_levels instead
    of depth specified.
    It is called with the following inputs:
    L, the number of bits per batch,
    num_levels, the the number of levels in the circuit,
    W, the number of input 'wires' (batch inputs taken) in the circuit, and
    gate_maker, the function used to produce each gate.
    """
    # Create the circuit:
    circuit = ic.IBMCircuit(L)
    # Create W input wires:
    wires = [iw.IBMInputWire("".join(("W",str(wire_ind))), circuit)
             for wire_ind in xrange(W)]
    circuit.set_input_wires(wires)
    ultimate_level = wires # the last level created
    penultimate_level = [] # the second-to-last level created
    # Initialize the global gate counter, which acts as the unique numerical id
    # of each gate:
    unique_gate_num = W
    for level in xrange(num_levels):
        new_level = []
        for gate_index in xrange(W): # create W new gates
            new_gate = gate_maker(L,
                                  ultimate_level,
                                  penultimate_level,
                                  "".join(["G", str(unique_gate_num)]),
                                  circuit)
            # Add the new gate to the new level:
            new_level.append(new_gate)
            # Increment the unique gate number:
            unique_gate_num += 1
        # Update the ultimate_level and penultimate_level pointers:
        penultimate_level = ultimate_level
        ultimate_level = new_level
    # Select the output gate from the last level:
    output_gate = sr.choice(ultimate_level)
    circuit.set_output_gate(output_gate)
    return circuit

TEST_TYPE_TO_GENERATOR_BY_LEVEL = dict(
    (test_type, functools.partial(
        generate_circuit_by_level,
        gate_maker = TEST_TYPE_TO_GATE_MAKER[test_type]))
    for test_type in TEST_TYPES.numbers_generator())

def generate_circuit_by_depth(L, D, W, gate_maker):
    """
    This function this generates an IBM circuit.
    It is called with the following inputs:
    L, the number of bits per batch,
    D, the depth of the circuit as defined by IBM,
    W, the number of input 'wires' (batch inputs taken) in the circuit, and
    gate_maker, the function used to produce each gate.
    """
    # Create the circuit:
    circuit = ic.IBMCircuit(L)
    # Create W input wires:
    wires = [iw.IBMInputWire("".join(("W", str(wire_ind))), circuit)
             for wire_ind in xrange(W)]
    circuit.set_input_wires(wires)
    ultimate_level = wires # the last level created
    penultimate_level = [] # the second-to-last level created
    # Keep track of the smallest gate depth at the last level:
    min_depth = 0
    # Maintain a list of gates at depth D:
    depth_D_gates = []
    # Maintain a list of gates between depth D and D+1, not including D:
    depth_around_D_gates = []
    # Initialize the global gate counter, which acts as the unique numerical id
    # of each gate:
    unique_gate_num = W
    while (min_depth <= D):
        new_level = []
        for gate_index in range(W): # create W new gates
            new_gate = gate_maker(L,
                                  ultimate_level,
                                  penultimate_level,
                                  "".join(["G", str(unique_gate_num)]),
                                  circuit)
            # If the new gate has depth D, add it to depth_D_gates:
            if (new_gate.get_depth() == D): 
                depth_D_gates.append(new_gate)
            # If the new gate has D < depth <= D+1, add it to
            # depth_around_D_gates:
            if ((new_gate.get_depth() > D) and (new_gate.get_depth() < D+1)):
                depth_around_D_gates.append(new_gate)
            # Add the new gate to the new level:
            new_level.append(new_gate)
            # Increment the unique gate number:
            unique_gate_num += 1
        # Increment the smallest gate depth at the last level as needed:
        min_depth = min(gate.get_depth() for gate in new_level)
        # Update the ultimate_level and penultimate_level pointers:
        penultimate_level = ultimate_level
        ultimate_level = new_level
    # If there is at least one gate of depth exactly D, select the output
    # gate from among such gates at random. Otherwise, select the output
    # gate from among gates between depth D and D+1.
    if(len(depth_D_gates) > 0):
        output_gate = sr.choice(depth_D_gates)
    else:
        output_gate = sr.choice(depth_around_D_gates)
    circuit.set_output_gate(output_gate)
    return circuit

TEST_TYPE_TO_GENERATOR_BY_DEPTH = dict(
    (test_type,
     functools.partial(generate_circuit_by_depth,
                       gate_maker = TEST_TYPE_TO_GATE_MAKER[test_type]))
    for test_type in TEST_TYPES.numbers_generator())

TEST_TYPE_TO_GENERATOR = dict(
    (gate_type, TEST_TYPE_TO_GENERATOR_BY_LEVEL[gate_type])
    for gate_type in GATE_TYPES.numbers_generator())
