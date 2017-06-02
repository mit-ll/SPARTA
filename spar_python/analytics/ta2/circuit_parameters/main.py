# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Script to add additional parameters to Stealth
#                      circuit descriptions.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Mar 2013   Yang           Original Version
# *****************************************************************

import argparse
from itertools import *
from circuit_parameters import *

def main():
    parser = argparse.ArgumentParser(description = 'Appends additional '
            'parameters to the first line of each Stealth circuit description '
            'in the specified directory')
    parser.add_argument('-p, --path', dest = 'path', required = True,
            help = 'path to circuit')
    args = parser.parse_args();

    (num_xor, num_other, fn_xor, fn_other) = parse_circuit(args.path)
    print "Number of XOR: {}\nNumber of Other: {}\nXOR fan-in: {}\nOther " \
        "fan-in: {}".format(num_xor, num_other, fn_xor, fn_other)

    write_parameters(args.path, num_xor, num_other, fn_xor, fn_other)

if __name__ == '__main__':
    main()
