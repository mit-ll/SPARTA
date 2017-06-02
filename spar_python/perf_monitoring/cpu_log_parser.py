#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module reads through the log files created
#                      by disk_monitor.sh and writes the entries to
#                      the performance monitoring database.
# *****************************************************************

'''A sample output is in the sample_files folder'''


import csv
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.perf_db import insert_cpu
from spar_python.perf_monitoring.time_utils import date_and_time_to_epoch
from spar_python.perf_monitoring.file_utils import CollectlFileIterator


class CpuLogEntry():
    '''Class representing an individual entry in the log'''
    def __init__(self, values):
        '''Initializes values from a dictionary'''
        self.host = values['host']
        self.time_epoch = float(values['time_epoch'])
        self.cpu_identifier = values['cpu_identifier']
        self.user_pct = float(values['user_pct'])
        self.sys_pct = float(values['sys_pct'])
        self.wait_pct = float(values['wait_pct'])
        self.irq_pct = float(values['irq_pct'])
        self.idle_pct = float(values['idle_pct'])
        self.total_pct = float(values['total_pct'])
        
    def __eq__(self, other):
        '''Make == compare values, not references'''
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        '''Make != compre values, not references'''
        return self.__dict__ != other.__dict__


    def __repr__(self):
        ''' Print nicely '''
        return "Host: %s Time: %0.6f CPU: %s User: %f Sys: %s Wait: %f irq: %f Idle: %f Total: %f" % \
            (self.host, self.time_epoch, self.cpu_identifier, self.user_pct, 
             self.sys_pct, self.wait_pct, self.irq_pct, self.idle_pct, 
             self.total_pct)
            
class CpuLogReader():
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
            # Each line contains a single Date, a single Time, 
            # and a set of entries per cpu
            thisdate = line["Date"]
            thistime = line["Time"]
            thisepoch = date_and_time_to_epoch(thisdate, thistime)
            
            # Everything else read per-cpu
            i = 0
            itemsread = 2
            while(itemsread < len(csvreader.fieldnames)):
                entry = { "host" : host,  
                         "time_epoch" : thisepoch, 
                         "cpu_identifier" : "cpu_" + str(i) }
                entry["user_pct"] = line["[CPU:" + str(i) + "]User%"]
                entry["nice"] = line["[CPU:" + str(i) + "]Nice%"]
                entry["sys_pct"] = line["[CPU:" + str(i) + "]Sys%"]
                entry["wait_pct"] = line["[CPU:" + str(i) + "]Wait%"]
                entry["irq_pct"] = line["[CPU:" + str(i) + "]Irq%"]
                entry["soft_pct"] = line["[CPU:" + str(i) + "]Soft%"]
                entry["steal_pct"] = line["[CPU:" + str(i) + "]Steal%"]
                entry["idle_pct"] = line["[CPU:" + str(i) + "]Idle%"]
                entry["total_pct"] = line["[CPU:" + str(i) + "]Totl%"]
                entry["interrupt"] = line["[CPU:" + str(i) + "]Intrpt"]
                
                self.entries.append(CpuLogEntry(entry))
                # host, time_epoch read once, not per-cpu
                itemsread += len(entry) - 3 
                i += 1
                

    def write_to_database(self, con):
        '''Write all entries to the database
        
        Inputs:
        connection: connection to a database
        
        Returns:
        nothing
        '''
        for entry in self.entries:
            insert_cpu(con, entry.host, entry.cpu_identifier, entry.time_epoch, 
                       entry.user_pct, entry.sys_pct, 
                       entry.wait_pct, entry.irq_pct, entry.idle_pct, 
                       entry.total_pct, commit=False)
        con.commit()