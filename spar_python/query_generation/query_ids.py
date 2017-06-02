# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Functions to guarentee unique query ids
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 August 2012  ATLH            Original version
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import itertools
import time


_automatic_counter_from_zero = itertools.count(0)
_query_counter_from_zero = itertools.count(0)
_seen_atomic_where_clauses = {}
_seen_full_where_clauses = {}
_seen_full_qids = []
_seen_atomic_qids = []
_seen_full_to_full_qids = []
_seen_full_to_atomic_qids = []

def total_num_queries():
    ''' only true at the end of query_generation'''
    return _automatic_counter_from_zero.next() + _query_counter_from_zero.next() 

def atomic_id():
    return  int(str(int(time.time())) + str(_automatic_counter_from_zero.next()))

def query_id():
    return int(str(int(time.time())) + str(_query_counter_from_zero.next()))

def atomic_where_has_been_seen(qid, where_clause):
    if where_clause in _seen_atomic_where_clauses.keys():
        return _seen_atomic_where_clauses[where_clause]
    else:
        _seen_atomic_where_clauses[where_clause]=qid
        return qid
    
def reset_atomic_where():
    _seen_atomic_where_clauses.clear()
    
def full_where_has_been_seen(qid, where_clause):
    if where_clause in _seen_full_where_clauses.keys():
        return _seen_full_where_clauses[where_clause]
    else:
        _seen_full_where_clauses[where_clause]=qid
        return qid

def reset_full_where():
    _seen_full_where_clauses.clear()
    
def atomic_qid_seen(qid):
    if qid in _seen_atomic_qids:
        return True
    else:
        _seen_atomic_qids.append(qid)
        return False

def reset_atomic_qid_seen():
    del _seen_atomic_qids[:] 
    
def full_qid_seen(qid):
    if qid in _seen_full_qids:
        return True
    else:
        _seen_full_qids.append(qid)
        return False

def reset_full_qid_seen():
    del _seen_full_qids[:]
    
    
def full_to_full_qids_seen(main_qid, child_qid):
    if (main_qid, child_qid) in _seen_full_to_full_qids:
        return True
    else:
        _seen_full_to_full_qids.append((main_qid, child_qid))
        return False
    

def reset_full_to_full_qid_seen():
    del _seen_full_to_full_qids[:]
    
def full_to_atomic_qids_seen(main_qid, child_qid):
    if (main_qid, child_qid) in _seen_full_to_atomic_qids:
        return True
    else:
        _seen_full_to_atomic_qids.append((main_qid, child_qid))
        return False
    
def reset_full_to_atomic_qid_seen():
    del _seen_full_to_atomic_qids[:]
    

