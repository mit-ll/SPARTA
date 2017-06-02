# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Function to parse TA2 keys and circuits
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  04 Mar 2013   Yang           Original Version
# *****************************************************************

def read_from_file(script_dir, path_from_file):
    a = path_from_file.split('/')
    assert len(a) == 4
    fd = open(script_dir + '/' + a[2] + '/' + a[3])
    return fd.readline()

def parse_parameters(line):
    params = line.split(',')
    param_dict = {}
    for p in params:
        index = p.find('=')
        assert index >= 0, "did not find '='"
        param_dict[p[:index]] = p[index + 1:]
    return param_dict
