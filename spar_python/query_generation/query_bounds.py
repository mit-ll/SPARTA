# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Functions to delinate the bounds for different
#                     query types 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 May 2014  ATLH            Original version
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

'''
Represents the maximal and minimum lower bounds seen
in the csv input file for each sub_query type, also
the specific bounds for the compound queries
'''
_result_set_size_range_lower = {}
_result_set_size_range_upper = {}
_tm_result_set_size_range_lower = {}
_tm_result_set_size_range_upper = {}
    
def set_result_set_size_range_lower(query_type, lower):
    try:
        if lower < _result_set_size_range_lower[query_type]:
            _result_set_size_range_lower[query_type] = lower
    except KeyError:
        _result_set_size_range_lower[query_type] = lower

def get_rss_lower(query_type):
    return _result_set_size_range_lower[query_type]
        
def set_result_set_size_range_upper(query_type, upper):
    try:
        if upper > _result_set_size_range_upper[query_type]:
            _result_set_size_range_upper[query_type] = upper
    except KeyError:
        _result_set_size_range_upper[query_type] = upper
        
def get_rss_upper(query_type):
    return _result_set_size_range_upper[query_type]
        
def set_tm_result_set_size_range_lower(query_type, lower):
    try:
        if lower < _tm_result_set_size_range_lower[query_type]:
            _tm_result_set_size_range_lower[query_type] = lower
    except KeyError:
        _tm_result_set_size_range_lower[query_type] = lower
        
def get_tm_rss_lower(query_type):
    return _tm_result_set_size_range_lower[query_type]
    
def set_tm_result_set_size_range_upper(query_type, upper):
    try:
        if upper > _tm_result_set_size_range_upper[query_type]:
            _tm_result_set_size_range_upper[query_type] = upper
    except KeyError:
        _tm_result_set_size_range_upper[query_type] = upper    
    
def get_tm_rss_upper(query_type):
    return _tm_result_set_size_range_upper[query_type]

