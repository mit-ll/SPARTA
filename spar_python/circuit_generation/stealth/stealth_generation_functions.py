
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 random circuit generation 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  18 Oct 2012   SY             Original Version
# *****************************************************************

import spar_python.circuit_generation.stealth.stealth_wire as sw
import spar_python.circuit_generation.stealth.stealth_gate_and as sga
import spar_python.circuit_generation.stealth.stealth_gate_or as sgo
import spar_python.circuit_generation.stealth.stealth_gate_xor as sgx
import spar_python.circuit_generation.stealth.stealth_circuit as sc
import spar_python.circuit_generation.circuit_common.circuit_input as si
import spar_python.common.spar_random as sr
import spar_python.common.enum as enum

import itertools
import functools

gate_types = ['AND', 'OR', 'XOR']
# An Enum of gate types:
GATE_TYPES = enum.Enum(*gate_types)
# An Enum of possible gate type distributions used in the tests
# (identical to GATE_TYPES, but include RANDOM as well):
test_types = gate_types + ['RANDOM']
TEST_TYPES = enum.Enum(*test_types)
# Note that much of the following code relies on the fact that GATE_TYPES and
# TEST_TYPES coincide in the first 6 elements.

LEVEL_TYPES = enum.Enum("RANDOM", "XOR")

# This file contains methods for creating random gates and circuits.

# Below are methods for creating random and, or, and xor gates, wherein the
# inputs are chosen from the last level of gates available.
# There is also a method for creating a gate where the gate type is chosen
# uniformly at random.

def make_random_gate(ultimate_level, fanin_frac, gate_name, gate_factory):
    """Creates a random family 1 or 2 gate using gate_factory.

    Args:
        ultimate_level: a list of gates or wires at the level directly above
            the one to which the new gate will belong.
        fanin_frac: the fraction of the gates at the ultimate_level which will
            serve as input to the new gate.
        gate_name: the name which the new gate will have.
        gate_factory: the method used to generate the new gate.
    """
    if fanin_frac == 1:
        fanin = len(ultimate_level)
        inputs = ultimate_level
    else:
        max_fanin = len(ultimate_level)
        # compute the standard deviation sigma as per the test plan appendix:
        sigma = min(max_fanin * (1 - fanin_frac), max_fanin * fanin_frac) / 3
        # compute the fanin as a normal distribution with mean max_fanin times
        # fanin frac, and standard deviation above:
        fanin = max(2, min(int(round(sr.gauss(max_fanin * fanin_frac, sigma))),
                       max_fanin))
        # choose random inputs:
        inputs = sr.sample(ultimate_level, fanin)
    # choose the negations:
    negations = [sr.randbit() for neg_ind in xrange(fanin)]
    return gate_factory(gate_name, inputs, negations)

def make_random_fam_3_gate(levels, gate_name, gate_factory):
    """Creates a random family 3 gate using gate_factory.
    A family 3 gate takes in two inputs, at least one of which is from the level
    directly above it.

    Args:
        levels: a list of lists of gates, one corresponding to each level
            already created in the circuit.
        gate_name: the name which the new gate will have.
        gate_factory: the method used to generate the new gate.
    """
    W = len(levels[0])
    assert(all(len(level) == W for level in levels))
    # make sure that we have at least two possible inputs:
    assert(W * len(levels) > 1)
    # find the first input among the circuit objects in the ultimate level:
    input1_index = sr.randint(0, W - 1)
    input1 = levels[-1][input1_index]
    # find the second input among all available circuit objects:
    input2_index = sr.randint(0, (len(levels) * W) - 1)
    while input2_index == input1_index:
        input2_index = sr.randint(0, (len(levels) * W) - 1)
    input2_inp_index = input2_index % W
    input2_level_index = len(levels) - ((input2_index -
                                        input2_inp_index) / W) - 1
    input2_inp_index = input2_index % W
    input2 = levels[input2_level_index][input2_inp_index]
    # create the gate:
    inputs = [input1, input2]
    negations = [sr.randbit() for neg_ind in xrange(2)]
    return gate_factory(gate_name, inputs, negations)

# A dictionary mapping gate type to generator which creates a random gate of
# that type, given ultimate_leve, fanin_frac and gate_name:
TYPE_TO_GATE_GEN = {TEST_TYPES.AND:
               functools.partial(make_random_gate,
                                 gate_factory = sga.StealthAndGate),
               TEST_TYPES.OR:
               functools.partial(make_random_gate,
                                 gate_factory = sgo.StealthOrGate),
               TEST_TYPES.XOR:
               functools.partial(make_random_gate,
                                 gate_factory = sgx.StealthXorGate)}

TYPE_TO_FAM3_GATE_GEN = {TEST_TYPES.AND:
                    functools.partial(make_random_fam_3_gate,
                                      gate_factory = sga.StealthAndGate),
                    TEST_TYPES.OR:
                    functools.partial(make_random_fam_3_gate,
                                      gate_factory = sgo.StealthOrGate),
                    TEST_TYPES.XOR:
                    functools.partial(make_random_fam_3_gate,
                                      gate_factory = sgx.StealthXorGate)}

def make_uniform_random_gate(ultimate_level, fanin_frac, gate_name):
    """Makes a random family 1 or 2 gate with type determined at random.
    """
    gate_type = sr.randint(0, GATE_TYPES.size() - 1)
    gate_factory = TYPE_TO_GATE_GEN[gate_type]
    return gate_factory(ultimate_level, fanin_frac, gate_name)

TYPE_TO_GATE_GEN[TEST_TYPES.RANDOM] = make_uniform_random_gate

def make_uniform_random_fam3_gate(levels, gate_name):
    """Makes a random family 3 gate with type determined at random.
    """
    gate_type = sr.randint(0, GATE_TYPES.size() - 1)
    gate_factory = TYPE_TO_FAM3_GATE_GEN[gate_type]
    return gate_factory(levels, gate_name)

TYPE_TO_FAM3_GATE_GEN[TEST_TYPES.RANDOM] = make_uniform_random_fam3_gate

def make_random_input_wire(displayname):
    """Makes a random input wire with the displayname. Its value is set to True
    with probability .5, and to False with probability .5."""
    val = sr.randbit()
    return sw.StealthInputWire(displayname, val)

def make_random_input(W):
    """Returns an array of W random bits."""
    # TODO: this can probably be made to run faster by generating all W random
    # bits at once.
    return si.Input([sr.randbit() for inp_num in xrange(W)])

class circuit_maker(object):
    """This is the circuit maker superclass. f1f2 and f3 makers extend it."""

    def __init__(self, circuit_file, input_file, output_file, W, gate_maker,
                 family):
        """Initializes the class with:
        circuit_file: the file to which the circuit is written.
        input_file: the file to which the input is written.
        output_file: the file to which the output is written.
        W: the number of input wires.
        gate_maker: the function used to generate random gates for the
            intermediate layers (can be a random gate generator, or can generate
            only gates of one type.)
        family: the number of the stealth circuit family to which this circuit
            belongs
        """
        self._circuit_file = circuit_file
        self._input_file = input_file
        self._output_file = output_file
        self._W = W
        self._gate_maker = gate_maker
        self._family = family

    def _create_circuit_header(self):
        """returns the circuit header, and writes it to the circuit file"""
        if self._family == 1:
            header_string = ",".join(["W=" + str(self._W),
                                      "G=" + str(self._G),
                                      "F=1"])
        elif self._family == 2:
            header_string = ",".join(["W=" + str(self._W),
                                      "G=" + str(self._G),
                                      "X=" + str(self._X),
                                      "F=2"])
        elif self._family == 3:
            header_string = ",".join(["W=" + str(self._W),
                                      "D=" + str(self._D),
                                      "F=3"])
        self._circuit_file.write(header_string)
        return header_string

    def _create_input_wires(self):
        """returns input wires, and write the inputs to the input file"""
        input_wires = [make_random_input_wire(
            'W%s' % wire_ind) for wire_ind in xrange(self._W)]
        # write the inputs to the input file:
        input_string = "".join([str(int(wire.evaluate()))
                                for wire in input_wires])
        input_string = "".join(["[", input_string, "]"])
        self._input_file.write(input_string)
        return input_wires

    def _create_output(self):
        """returns the output, and writes the output to the output file"""
        # choose a random output, and write it to the output file:
        output = sr.randbit()
        self._output_file.write(str(output))
        return output

class f1f2_circuit_maker_with_trimming_switch(circuit_maker):
    """This class generates a random circuit-input pair with the circuit
    belonging to the superclass of Stealth's first and second circuit families.
    """
    def __init__(self, W, G, fg, circuit_file, input_file, output_file, X, fx,
                 gate_maker, level_type_array, trimming):
        """Initializes the circuit maker with the following additional
        parameters:
        G: the number of intermediate gates in each intermediate layer.
        fg: the fan-in fraction to intermediate gates.
        X: the number of XOR gates in each XOR layer.
        fx: the fan-in fraction to XOR gates.
        level_type_array: an array containing elements of the LEVEL_TYPES enum,
            indicating the types of levels and their order.
        trimming: a boolean indicating whether or not this circuit maker
            should take care to exclude gates not contributing to the output
            gate or not. We choose 'trimming' depending on how likely such a
            gate is to occur.
        """
        if level_type_array == [LEVEL_TYPES.RANDOM]:
            family = 1
        elif level_type_array == [LEVEL_TYPES.XOR, LEVEL_TYPES.RANDOM,
                                  LEVEL_TYPES.XOR]:
            family = 2
        circuit_maker.__init__(self, circuit_file, input_file, output_file, W,
                               gate_maker, family)
        self._G = G
        self._fg = fg
        self._X = X
        self._fx = fx
        self._level_type_array = level_type_array
        self._trimming = trimming

    def generate(self):
        """Populates the circuit, input and output files with a circuit, an
        input, and the corresponding output with the appropriate parameters."""
        # create the header and write it to the circuit file:
        header_string = self._create_circuit_header()
        # create the input wires and write the inputs to the input file:
        input_wires = self._create_input_wires()
        # create the output and write it to the output file:
        output = self._create_output()
        # initialize the global gate counter, which acts as the unique numerical
        # id of each gate:
        unique_gate_num_gen = itertools.count(self._W, 1)
        # set the 'ultimate level' for the first level of gates:
        ultimate_level = input_wires
        # for each level:
        for level_ind in xrange(len(self._level_type_array)):
            if not self._trimming:
                # if this circuit is not being trimmed, then we have to write
                # 'L' to the circuit file, because we will not be creating a
                # circuit object to take care of our printing for us:
                self._circuit_file.write("\nL")
            # if this is an intermediate level:
            if self._level_type_array[level_ind] == LEVEL_TYPES.RANDOM:
                num_gates = self._G
                fanin_frac = self._fg
                make_gate = self._gate_maker
            # if this is an XOR level:
            elif self._level_type_array[level_ind] == LEVEL_TYPES.XOR:
                num_gates = self._X
                fanin_frac = self._fx
                make_gate = TYPE_TO_GATE_GEN[GATE_TYPES.XOR]
            # Create the list of gates at this level:
            this_level = [None] * num_gates
            for gate_ind in xrange(num_gates):
                displayname = "".join(["G", str(unique_gate_num_gen.next())])
                # make the random gate:
                new_gate = make_gate(ultimate_level, fanin_frac, displayname)
                # choose a random output, and balance the new gate with respect
                # to that output:
                new_gate_output = sr.randbit()
                new_gate.balance(new_gate_output)
                if not self._trimming:
                    # if this circuit is not being trimmed, then we can just
                    # write the gate to the circuit file right away:
                    self._circuit_file.write(
                        "".join(["\n", new_gate.get_full_display_string()]))
                    # since this gate is already written to the circuit file,
                    # we can save on memory space by re-representing it as an
                    # input wire with the correct value:
                    new_gate = sw.StealthInputWire(displayname, new_gate_output)
                # add this gate to our list of gates at this level:
                this_level[gate_ind] = new_gate
                # increment the global gate counter:
            # set things up for the next level:
            ultimate_level = this_level
        # create the output gate:
        negations = [sr.randbit() for neg_ind in xrange(len(ultimate_level))]
        output_gate = self._gate_maker(ultimate_level, 1, "output_gate")
        # balance the output gate with respect to the chosen output:
        output_gate.balance(output)
        if self._trimming:
            # if this circuit is being trimmed, then we create a circuit and
            # write it to the circuit_file:
            circ = sc.StealthCircuit(input_wires, output_gate)
            self._circuit_file.write(circ.display())
        else:
            # otherwise, we will have already written all the gates as we went
            # along, so we only need to record the output gate:
            self._circuit_file.write("".join(["\nL\n",
                                        output_gate.get_full_display_string()]))

def get_prob_needs_trimming(W, G, fg, X, fx, level_type_array):
    """Calculates the probability that a circuit with the parameters specified
    will contain a gate or wire which does not contribute to the output gate,
    and thus needs trimming. Note that this function makes the simplifying
    assumption that input choice events are independant; this is, in fact, not
    so.

    Args:
        W: the number of input wires.
        G: the number of intermediate gates in each intermediate layer.
        fg: the fan-in fraction to intermediate gates.
        X: the number of XOR gates in each XOR layer.
        fx: the fan-in fraction to XOR gates.
        level_type_array: an array containing elements of the LEVEL_TYPES enum,
            indicating the types of levels and their order.
    """
    num_levels = len(level_type_array)
    pr = 0.0
    for level_type_index in xrange(num_levels):
        if level_type_index == 0: prev_level_size = W
        elif level_type_array[level_type_index-1] == LEVEL_TYPES.RANDOM:
            prev_level_size = G
        elif level_type_array[level_type_index-1] == LEVEL_TYPES.XOR:
            prev_level_size = X
        if level_type_array[level_type_index] == LEVEL_TYPES.RANDOM:
            level_size = G
            fanin_frac = fg
        elif level_type_array[level_type_index] == LEVEL_TYPES.XOR:
            level_size = X
            fanin_frac = fx
        # for each gate at the previous level, the probability that it doesn't
        # lead to any gate at this level is as follows:
        pr_abandoned_prev_level_gate = (1.0 - fanin_frac) ** (level_size)
        # the probability that at least one gate at the previous level doesn't
        # lead to any gate at this level is as follows:
        pr_exists_abandoned_prev_level_gate = 1.0 - (
            (1.0 - pr_abandoned_prev_level_gate) ** prev_level_size)
        # the probability that there exists at least one gate that doesn't lead
        # to anything on at least one of the levels is modified as follows:
        pr = 1.0 - ((1.0 - pr) * (1.0 - pr_exists_abandoned_prev_level_gate))
    return pr


class f1f2_circuit_maker(f1f2_circuit_maker_with_trimming_switch):
    """This class generates a random circuit-input pair with the circuit
    belonging to the superclass of Stealth's first and second circuit families.
    It determines whether to use trimming or not based on the probability that
    trimming will be becessary.
    """
    def __init__(self, W, G, fg, circuit_file, input_file, output_file, X, fx,
                 gate_maker, level_type_array):
        # if the probability of a gate not contributing to the output gate is
        # less than a certain threshold, use trimming.
        # otherwise, do not.
        threshold = .00001
        pr = get_prob_needs_trimming(W, G, fg, X, fx, level_type_array)
        if (pr > threshold):
            f1f2_circuit_maker_with_trimming_switch.__init__(self, W, G, fg,
                                                    circuit_file, input_file,
                                                    output_file, X, fx,
                                                    gate_maker,
                                                    level_type_array, True)
        else:
            f1f2_circuit_maker_with_trimming_switch.__init__(self, W, G, fg,
                                                    circuit_file, input_file,
                                                    output_file, X, fx,
                                                    gate_maker,
                                                    level_type_array, False)
            
class f3_circuit_maker(circuit_maker):
    """This class generates a random circuit-input pair with the circuit
    belonging to Stealth's third circuit family.
    """
    def __init__(self, W, D, circuit_file, input_file, output_file, gate_maker):
        """Initializes the circuit maker with:
        W: the number of input wires.
        D: the depth of the circuit.
        circuit_file: the file to which the circuit is written.
        input_file: the file to which the input is written.
        output_file: the file to which the output is written.
        gate_maker: the function used to generate random gates for the
            intermediate layers (can be a random gate generator, or can generate
            only gates of one type.)
        """
        circuit_maker.__init__(self, circuit_file, input_file, output_file, W,
                               gate_maker, 3)
        self._D = D

    def generate(self):
        """Populates the circuit, input and output files with a circuit, an
        input, and the corresponding output with the appropriate parameters."""
        # create the header and write it to the circuit file:
        header_string = self._create_circuit_header()
        # create the input wires and write the inputs to the input file:
        input_wires = self._create_input_wires()
        # set set of all circuit objects already created:
        levels = [input_wires]
        # initialize the global gate counter, which acts as the unique numerical
        # id of each gate:
        unique_gate_num_gen = itertools.count()
        # for each level:
        for level_index in xrange(self._D):
            # Create the list of gates at this level:
            this_level = [None] * self._W
            for gate_ind in xrange(self._W):
                displayname = "".join(["G",str(unique_gate_num_gen.next())])
                # make the new gate:
                new_gate = self._gate_maker(levels, displayname)
                new_gate_output = sr.randbit()
                new_gate.balance(new_gate_output)
                # add this gate to our list of gates at this level:
                this_level[gate_ind] = new_gate
            # set things up for the next level:
            ultimate_level = this_level
            levels.append(this_level)
        output_gate = sr.choice(levels[-1])
        output_gate.set_name("output_gate")
        # choose a random output, and write it to the output file:
        output = sr.randbit()
        self._output_file.write(str(output))
        # balance the output gate with respect to the chosen output:
        output_gate.balance(output)
        circ = sc.StealthCircuit(input_wires, output_gate)
        # write the circuit to the circuit file:
        self._circuit_file.write(circ.display())

TYPE_TO_FAM1_GEN = {TEST_TYPES.RANDOM:
                    functools.partial(
                        f1f2_circuit_maker,
                        X = None,
                        fx = None,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.RANDOM],
                        level_type_array = [LEVEL_TYPES.RANDOM]),
                    TEST_TYPES.AND:
                    functools.partial(
                        f1f2_circuit_maker,
                        X = None,
                        fx = None,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.AND],
                        level_type_array = [LEVEL_TYPES.RANDOM]),
                    TEST_TYPES.OR:
                    functools.partial(
                        f1f2_circuit_maker,
                        X = None,
                        fx = None,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.OR],
                        level_type_array = [LEVEL_TYPES.RANDOM]),
                    TEST_TYPES.XOR:
                    functools.partial(
                        f1f2_circuit_maker,
                        X = None,
                        fx = None,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.XOR],
                        level_type_array = [LEVEL_TYPES.RANDOM])}

TYPE_TO_FAM2_GEN = {TEST_TYPES.RANDOM:
                    functools.partial(
                        f1f2_circuit_maker,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.RANDOM],
                        level_type_array = [LEVEL_TYPES.XOR,
                                            LEVEL_TYPES.RANDOM,
                                            LEVEL_TYPES.XOR]),
                    TEST_TYPES.AND:
                    functools.partial(
                        f1f2_circuit_maker,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.AND],
                        level_type_array = [LEVEL_TYPES.XOR,
                                            LEVEL_TYPES.RANDOM,
                                            LEVEL_TYPES.XOR]),
                    TEST_TYPES.OR:
                    functools.partial(
                        f1f2_circuit_maker,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.OR],
                        level_type_array = [LEVEL_TYPES.XOR,
                                            LEVEL_TYPES.RANDOM,
                                            LEVEL_TYPES.XOR]),
                    TEST_TYPES.XOR:
                    functools.partial(
                        f1f2_circuit_maker,
                        gate_maker = TYPE_TO_GATE_GEN[TEST_TYPES.XOR],
                        level_type_array = [LEVEL_TYPES.XOR,
                                            LEVEL_TYPES.RANDOM,
                                            LEVEL_TYPES.XOR])}

TYPE_TO_FAM3_GEN = {TEST_TYPES.RANDOM:
                    functools.partial(
                        f3_circuit_maker,
                        gate_maker = TYPE_TO_FAM3_GATE_GEN[TEST_TYPES.RANDOM]),
                    TEST_TYPES.AND:
                    functools.partial(
                        f3_circuit_maker,
                        gate_maker = TYPE_TO_FAM3_GATE_GEN[TEST_TYPES.AND]),
                    TEST_TYPES.OR:
                    functools.partial(
                        f3_circuit_maker,
                        gate_maker = TYPE_TO_FAM3_GATE_GEN[TEST_TYPES.OR]),
                    TEST_TYPES.XOR:
                    functools.partial(
                        f3_circuit_maker,
                        gate_maker = TYPE_TO_FAM3_GATE_GEN[TEST_TYPES.XOR])}

FAM_TO_TYPE_TO_GENERATOR = {1: TYPE_TO_FAM1_GEN,
                            2: TYPE_TO_FAM2_GEN,
                            3: TYPE_TO_FAM3_GEN}
