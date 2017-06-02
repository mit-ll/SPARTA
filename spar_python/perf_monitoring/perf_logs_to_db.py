#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This reads through performance monitoring 
#                      log files and puts the results into an
#                      sqlite database
# *****************************************************************

import os
import sys
import argparse
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.cpu_log_parser import CpuLogReader
from spar_python.perf_monitoring.disk_log_parser import DiskLogReader
from spar_python.perf_monitoring.ram_log_parser import RamLogReader
from spar_python.perf_monitoring.perf_db import create_perf_db
from spar_python.perf_monitoring.pcap_parser import pcap_to_log
from spar_python.perf_monitoring.pcap_parser import get_mappings_from_handle



def main():
    '''Reads in raw log files/pcap and writes entries to an sqlite database'''
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--endpoint', dest = 'host',
          type = str, required = False, 
          help = 'endpoint, aka host ("client", "server", etc.)')
    parser.add_argument('-c', '--cpu-file', dest = 'cpu_file',
          type = str, required = False, default=None,
          help = '(uncompressed) cpu log file')
    parser.add_argument('-d', '--disk-file', dest = 'disk_file',
          type = str, required = False, default=None,
          help = '(uncompressed) disk log file')
    parser.add_argument('-r', '--ram-file', dest = 'ram_file',
          type = str, required = False, default=None,
          help = '(uncompressed) ram log file')
    parser.add_argument('-n', '--network-file', dest = 'network_file',
          type = str, required = False, default=None,
          help = 'pcap file')
    parser.add_argument("-m", "--network-map", dest = 'network_map',
          type = str, required = False, default=None,
          help = 'file containing map from IP address to host ("client")')
    parser.add_argument('-o', '--output-file', dest = 'sqlite_file',
          type = str, required = True,
          help = 'sqlite3 file to write to')
    
    options = parser.parse_args()    
    
    con = create_perf_db(options.sqlite_file)
   
    if (options.cpu_file != None):
        reader = CpuLogReader(handle=open(options.cpu_file), host=options.host)
        reader.write_to_database(con)
    if (options.disk_file != None):
        reader = DiskLogReader(handle=open(options.disk_file), 
                    host=options.host)
        reader.write_to_database(con)
    if (options.ram_file != None):
        reader = RamLogReader(handle=open(options.ram_file), host=options.host)
        reader.write_to_database(con)
    if (options.network_file != None):
        if (options.network_map == None):
            sys.stderr.write("Must include network map if parsing pcap files")
        else:
            mappings = get_mappings_from_handle(open(options.network_map))
            reader = pcap_to_log(options.network_file, mappings)
            reader.write_to_database(con)
                              
if __name__ == '__main__':
    main()


