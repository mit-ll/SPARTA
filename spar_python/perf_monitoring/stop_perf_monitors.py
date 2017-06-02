#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        Stops performance monitors.  Pairs with 
#                      start_perf_monitors
# *****************************************************************


'''Stops the performance monitoring tools.  Must be run as root
(because the monitors are run as root).  Reads pids as a 
comma-separated string from stdin'''

import os
import signal
import sys


def is_root_user():
    '''Returns True if user is root'''
    return (os.geteuid() == 0)

def terminate_pids(pids):
    '''Terminates the input pids
    
    Input: pids: an integer array of process ids
    '''
    for pid in pids:
        os.kill(pid, signal.SIGTERM)
        
def read_pids(handle):
    '''Reads a comma-separated list of pids from a file handle'''
    pids = [int(x) for x in handle.readline().split(',')]
    return pids

def main():
    '''Main'''
    if (not is_root_user()):
        sys.stderr.write("ERROR: %s must be run as root\n" % sys.argv[0])
        sys.exit(-1)
    pids = read_pids(sys.stdin)
    terminate_pids(pids) 
    
    
if __name__ == "__main__":
    main()