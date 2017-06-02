# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Parser class for TA2 results
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  19 Feb 2013   Yang           Original Version
# *****************************************************************

from parser_factory import get_parser

# This class simultaneously parses a script file and result log to obtain the
# data points and their associated parameters. The script file contains the
# parameters while the result log contains the data collected using those
# parameters.
#
# While parsing, it maintains a list of all data points that have been parsed so
# far. Data points are separated into key, circuit, and input data. Each have
# their own associated parameters. Since a data point is represented as a list
# itself, each type of data point will have its own length.
#
# DataAggregators are also specific to each performer since each uses its own
# set of parameters.
class DataAggregator:

    def __init__(self, key_state, circuit_state, key_schema, circuit_schema,
            input_schema):
        self.__key_state = key_state
        self.__circuit_state = circuit_state
        self.__key_schema = key_schema
        self.__circuit_schema = circuit_schema
        self.__input_schema = input_schema
        self.__key_id = 0
        self.__circuit_id = 0
        self.__input_id = 0
        self.__init_csv()
    
    def aggregate(self, tests):
        lines = tests.strip().split('\n')
        assert len(lines) >= 2
        circuit_dir = lines[0]
        result_dir = lines[1]
        for i in xrange(2, len(lines)):
            paths = lines[i].split()
            assert len(paths) == 1 or len(paths) == 2
            path_to_script = circuit_dir + '/' + paths[0]
            script_parser = get_parser("script", path_to_script)
            assert script_parser is not None
            path_to_log = None
            if len(paths) == 2:
                path_to_log = result_dir + '/' + paths[1]
                log_parser = get_parser("log", path_to_log)
            self.__parse(circuit_dir, script_parser, log_parser)
        return self.__data

    def __init_csv(self):
        self.__data = {}
        self.__data['KEY'] = [['key_id'] + self.__key_state.keys() + \
                self.__key_schema]
        self.__data['CIRCUIT'] = [['circuit_id'] \
                + self.__circuit_state.keys() + self.__circuit_schema]
        self.__data['INPUT'] = [['input_id', 'key_id', 'circuit_id'] + \
                self.__input_schema]
    
    def __update_state(self, action, params):
        if action == 'KEY':
            self.__key_id += 1
            for p in params:
                if p in self.__key_state.keys():
                    self.__key_state[p] = params[p]
        elif action == 'CIRCUIT':
            self.__circuit_id += 1
            for p in params:
                if p in self.__circuit_state.keys():
                    self.__circuit_state[p] = params[p]
        else:
            self.__input_id += 1

    def __insert_csv_row(self, action, data):
        row = []
        if data is None:
            row += [''] * len(self.__data[action][0])
        else:
            if action == 'KEY':
                row = [self.__key_id] + [self.__key_state[k] for k in \
                    self.__key_state.keys()] 
                row += [data[k] for k in self.__key_schema]
            elif action == 'CIRCUIT':
                row = [self.__circuit_id] + [self.__circuit_state[k] \
                        for k in self.__circuit_state.keys()]
                row += [data[k] for k in self.__circuit_schema]
            else:
                row = [self.__input_id, self.__key_id, self.__circuit_id]
                row += [data[k] for k in self.__input_schema]
        self.__data[action].append(row)

    def __parse(self, script_dir, script_parser, log_parser):
        tup = script_parser.next()
        while tup:
            self.__update_state(tup[0], tup[1])
            data = None
            if log_parser:
                data = log_parser.parse_data(tup[0])
            self.__insert_csv_row(tup[0], data)
            tup = script_parser.next()
