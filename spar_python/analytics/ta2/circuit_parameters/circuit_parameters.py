# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Function to parse a circuit and calculate parameters
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Mar 2013   Yang           Original Version
# *****************************************************************

import itertools

def write_parameters(path_to_circuit, num_xor, num_other, fn_xor, fn_other):
    try:
        fd = open(path_to_circuit)
    except IOError:
        print "failed to open file %s", path_to_circuit

    lines = fd.readlines()
    lines[0] = lines[0].rstrip('\n') + ",nXor=" + str(num_xor) + ",nOther=" + \
            str(num_other) + ",fnXor=" + str(fn_xor) + ",fnOther=" + \
            str(fn_other) + "\n";
    
    try:
        fd = open(path_to_circuit, 'w')
    except IOError:
        print "failed to open file %s in write mode", path_to_circuit 
    for line in lines:
        fd.write(line)
    fd.close()

def parse_circuit(path_to_circuit):
    num_xor = 0
    num_other = 0
    fn_xor = 0
    fn_other = 0
    try:
        fd = open(path_to_circuit)
    except IOError:
        print 'failed to open %s', path_to_circuit
        return
    params = fd.readline()
    line = fd.readline()
    while line:
        if 'XOR' in line:
            num_xor += 1
            fn_xor += line.count(',') + 1
        elif 'L' not in line:
            num_other += 1
            fn_other += line.count(',') + 1
        line = fd.readline()
    return (num_xor, num_other, fn_xor, fn_other)


