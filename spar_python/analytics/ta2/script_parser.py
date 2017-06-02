# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Parser class for TA2 script files
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 Feb 2013   Yang           Original Version
# *****************************************************************

class ScriptParser:
    
    def __init__(self, script):
        self.__lines = script.strip().split('\n')
        self.__index = 0
    
    def next(self):
        if self.__index >= len(self.__lines):
            return None
        
        action = self.__lines[self.__index]
        assert action in ['KEY', 'CIRCUIT', 'INPUT']
        self.__index += 1
        path = self.__lines[self.__index]
        params = None
        if action != 'INPUT':
            params = self.__parse_params(path)
        self.__index += 1
        return (action, params)
    
    def __parse_params(self, path):
        try:
            fd = open(path, 'r')
        except IOError:
            print 'failed to open ' + path
            sys.exit(1)
        # the first line contains a comma-separated list of key parameters
        line = fd.readline().strip()
        params = line.split(',')
        param_dict = {}
        for p in params:
            i = p.find('=')
            if i >= 0:
                param_dict[p[:i]] = p[i+1:]
            else:
                param_dict['K'] = 'default'
        return param_dict
