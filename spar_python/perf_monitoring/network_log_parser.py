#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module reads through the csv file(s) created 
#                      by pcap_parser and writes the entries to
#                      the performance monitoring database.
# *****************************************************************

'''A sample output is in the sample_files folder'''


import csv
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.perf_db import insert_network

class NetworkLogEntry:
    '''Class representing an entry in the network log'''
    # Enums to represent direction
    def __init__(self, values):
        '''Initializer.  Converts a log line (dictionary) to a log entry'''
        self.time = float(values['time'])
        self.direction = values['direction']
        self.payloadlength = int(values['payloadlength'])
        self.protocol = values['protocol']
        
    def __eq__(self, other):
        '''Make == compare values, not references'''
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        '''Make != compre values, not references'''
        return self.__dict__ != other.__dict__
    
    def __repr__(self):
        ''' Print nicely '''
        return "Direction: %s Length: %s time: %0.6f proto: %s" % \
            (self.direction, self.payloadlength, self.time, self.protocol)
    
  

class NetworkLogReader:
    '''Class to read a pcap file'''
    def __init__(self, handle=None):
        '''Initializer.  Reads from the given file handle
        
        Inputs:
        Handle: handle to a file (open("foo.pcap")) 

        Returns:
        nothing
        '''
        self.fieldnames = []
        self.entries = []
        if (handle != None):
            self.add_handle(handle)
        
    def add_handle(self, handle):
        '''Reads in the specified file.  Combines contents
        of this file with contents of previously read file.
        
        Inputs:
        handle: handle to a file (open("foo.csv")) 

        Returns:
        nothing
        '''
        csvreader = csv.DictReader(handle)
        self.fieldnames = csvreader.fieldnames
        for line in csvreader:
            self.entries.append(NetworkLogEntry(line))

        
    def write_to_database(self, connection):
        '''Write all entries to the database
        
        Inputs:
        connection: connection to a database
        
        Returns:
        nothing
        '''
        for entry in self.entries:
            insert_network(connection, entry.time, entry.direction, 
                           entry.payloadlength, entry.protocol, commit=False)
        connection.commit()
