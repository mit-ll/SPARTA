# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Script to parse TA2 results and save them to
#                      csv format.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  19 Feb 2013   Yang           Original Version
# *****************************************************************

# Two files are needed for the parser to extract the data points from the raw
# result logs: 1) the test script used to run the test and 2) the result log.
# Rather than doing them one pair at a time, this script takes in a single text
# file containing the file path of all script/result pairs that are to be
# parsed.

import argparse
import csv
from aggregator import DataAggregator

def main():
    parser = argparse.ArgumentParser(description = 'Generates a '
            'comma separated values file of all data points')
    parser.add_argument('-c, --config', dest = 'config', required = True,
            help = 'path to configuration file')
    parser.add_argument('-o, --output', dest = 'output', help = 'name of output'
            ' csv file without the file extension')
    parser.add_argument('-p, --performer', dest = 'performer',
            choices = ['stealth', 'ibm'], required = True,
            help = 'name of performer')
    args = parser.parse_args();

    key_schema = ['KEYGEN', 'KEYSIZE', 'KEYTRANSMIT']
    circuit_schema = ['INGESTION', 'CIRCUITTRANSMIT']
    input_schema = ['ENCRYPT', 'INPUTSIZE', 'INPUTTRANSMIT', 'EVAL', 'DECRYPT']
    
    key_state = {}
    circuit_state = {}
    if args.performer == 'ibm':
        key_state = {'K': ''}
        circuit_state = {'L': '', 'D': '', 'W': ''}
    else:
        key_state = {'K': 'default'}
        circuit_state = {'F': '', 'G': '', 'W': '', 'X': '', 'D': '', 'fx': ''}
    
    d = DataAggregator(key_state, circuit_state, key_schema, circuit_schema,
            input_schema)

    try:
        fd = open(args.config)
    except IOError:
        print 'failed to open configuration file'
        sys.exit(1)

    data = d.aggregate(fd.read())
    
    if args.output:
        with open(args.output + '-key.csv', 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(data['KEY'])
        with open(args.output + '-circuit.csv', 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(data['CIRCUIT'])
        with open(args.output + '-input.csv', 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(data['INPUT'])

if __name__ == "__main__":
    main()
