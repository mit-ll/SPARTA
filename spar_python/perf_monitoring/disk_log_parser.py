#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module reads through the log files created
#                      by disk_monitor.sh and writes the entries to
#                      the performance monitoring database.
# *****************************************************************

'''A sample output is in the sample_files folder

Note that, if there are multiple disks, there will be more columns per row
'''

import csv
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.file_utils import CollectlFileIterator
from spar_python.perf_monitoring.perf_db import insert_disk
from spar_python.perf_monitoring.time_utils import date_and_time_to_epoch


class DiskLogEntry():
    '''Class representing an individual entry in the log'''
    def __init__(self, values):
        '''Initializes values from a dictionary'''
        self.host = values['host']
        self.time_epoch = float(values['time_epoch'])
        self.disk_name = values['disk_name']
        self.reads_per_sec = float(values['reads_per_sec'])
        self.reads_kbps = float(values['reads_kbps'])
        self.writes_per_sec = float(values['writes_per_sec'])
        self.writes_kbps = float(values['writes_kbps'])

    def __eq__(self, other):
        '''Make == compare values, not references'''
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        '''Make != compre values, not references'''
        return self.__dict__ != other.__dict__

    def __repr__(self):
        ''' Print nicely '''
        return "Host: %s Time: %0.6f Name: %s Reads_per_sec: %f Reads_kbps: %f Writes_per_sec: %f Writes_kbps: %f" % \
            (self.host, self.time_epoch, self.disk_name, self.reads_per_sec,
             self.reads_kbps, self.writes_per_sec, self.writes_kbps)
            
class DiskLogReader():
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
    
    def _get_disk_names(self, fieldnames):
        '''Returns a list of the disks covered by this collectl log file
        by parsing the header'''
        names = []
        for field in fieldnames:
            # look for the "[DSK:<name>]Name field
            if field.endswith("]Name"):
                #strip off the leading "[DSK:" and trailing "]Name"
                names.append(field[5:-5])
        return names
                
        
            
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
        # Learn what disks are located in this file 
        disknames = self._get_disk_names(csvreader.fieldnames)
        for line in csvreader:
            # Each line contains a single Date, a single Time, 
            # and a set of entries per Disk
            thisdate = line["Date"]
            thistime = line["Time"]
            thisepoch = date_and_time_to_epoch(thisdate, thistime)
            
            # Everything else read per-disk
            for disk in disknames:
                entry = { "host" : host,  
                         "time_epoch" : thisepoch }
                entry["disk_name"] = disk
                entry["reads_per_sec"] = line["[DSK:" + disk + "]Reads"]
                entry["reads_kbps"] = line["[DSK:" + disk + "]RKBytes"]
                entry["writes_per_sec"] = line["[DSK:" + disk + "]Writes"]
                entry["writes_kbps"] = line["[DSK:" + disk + "]WKBytes"]
                
                self.entries.append(DiskLogEntry(entry))
                
    def write_to_database(self, con):
        '''Write all entries to the database
        
        Inputs:
        connection: connection to a database
        
        Returns:
        nothing
        '''
        for entry in self.entries:
            insert_disk(con, entry.host, entry.time_epoch,  
                        entry.disk_name, entry.reads_per_sec, 
                        entry.reads_kbps, entry.writes_per_sec, 
                        entry.writes_kbps, commit=False)
        con.commit()
        
    
            
            