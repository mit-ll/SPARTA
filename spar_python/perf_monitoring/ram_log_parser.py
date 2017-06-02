#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module reads through the log files created
#                      by ram_monitor.sh and writes the entries to
#                      the performance monitoring database.
# *****************************************************************

''' A sample output file is in the sample_files directory'''

import csv
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.file_utils import CollectlFileIterator
from spar_python.perf_monitoring.perf_db import insert_ram
from spar_python.perf_monitoring.time_utils import date_and_time_to_epoch

class RamLogEntry():
    '''Class representing an individual entry in the log'''
    def __init__(self, values):
        '''Initializes values from a dictionary'''
        self.host = values['host']
        self.time_epoch = float(values['time_epoch'])
        self.used_kb = float(values['used_kb'])
        self.free_kb = float(values['free_kb'])
        self.swap_total = float(values['swap_total'])
        self.swap_used = float(values['swap_used'])
        self.swap_free = float(values['swap_free'])

    def __eq__(self, other):
        '''Make == compare values, not references'''
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        '''Make != compre values, not references'''
        return self.__dict__ != other.__dict__

    def __repr__(self):
        ''' Print nicely '''
        return "Host: %s Time: %0.6f Used_KB: %f Free_KB: %f Swap_total: %f Swap_used: %f Swap_free: %f" % \
            (self.host, self.time_epoch, self.used_kb, self.free_kb,
             self.swap_total, self.swap_used, self.swap_free)
            
class RamLogReader():
    '''class to read log files produced by ram_monitor.sh'''
    def __init__(self, handle=None, host=None):
        '''Initializer.  Reads from the given file handle
        
        Inputs:
        handle (optional): handle to a file (open("foo.csv")) 
        host( required if handle given): the host on which the data was collected ("client")

        Returns:
        nothing
        '''
        self.entries = []
        if (handle != None):
            self.add_handle(handle, host)
            
    def add_handle(self, handle, host):
        '''Reads in the specified file.  Combines contents
        of this file with contents of previously read file.
        
        Inputs:
        handle: handle to a file (open("foo.csv")) 
        host: the host on which the data was collected ("client")

        Returns:
        nothing
        '''
        csvreader = csv.DictReader(CollectlFileIterator(handle))
        for line in csvreader:
            thisdate = line["Date"]
            thistime = line["Time"]
            thisepoch = date_and_time_to_epoch(thisdate, thistime)
            
            entry = { "host" : host, 
                     "time_epoch" : thisepoch}
            entry["used_kb"] = line["[MEM]Used"]
            entry["free_kb"] = line["[MEM]Free"]
            entry["swap_total"] = line["[MEM]SwapTot"]
            entry["swap_used"] = line["[MEM]SwapUsed"]
            entry["swap_free"] = line["[MEM]SwapFree"]
            self.entries.append(RamLogEntry(entry))


    
    
    def write_to_database(self, con):
        '''Write all entries to the database
        
        Inputs:
        connection: connection to a database
        
        Returns:
        nothing
        '''
        for entry in self.entries:
            insert_ram(con, entry.host, entry.time_epoch,  
                       entry.used_kb, entry.free_kb, entry.swap_total, 
                       entry.swap_used, entry.swap_free, commit=False)
        con.commit()
        

