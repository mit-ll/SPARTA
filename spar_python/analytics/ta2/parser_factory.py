# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Factory class for parser
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Mar 2013   Yang           Original Version
# *****************************************************************

from script_parser import ScriptParser
from log_parser import LogParser

def get_parser(parser_type, path_to_file):
    parser = None
    if parser_type == "script":
        try:
            fd = open(path_to_file)
            parser = ScriptParser(fd.read())
        except IOError as e:
            print 'failed to open script file ' + path_to_file
    elif parser_type == "log":
        try:
            fd = open(path_to_file)
            parser = LogParser(fd.read())
        except IOError as e:
            print 'failed to open log file ' + path_to_file
    return parser
