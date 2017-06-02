#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      disk_log_parser.py 
# *****************************************************************


import unittest
import StringIO
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.perf_monitoring.disk_log_parser as dlp
import spar_python.perf_monitoring.perf_db as perfdb
from spar_python.perf_monitoring.time_utils import date_and_time_to_epoch, epoch_to_sql



TEST_DISK_LOG_FILE_1 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sD -i 1.283 -P -omz2 --sep , --filename /home/spar-dev/tests/disk.log 
# Host:       ubuntu  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130802-160749  Secs: 1375474069 TZ: -0400
# SubSys:     D Options: mz2 Interval: 1.283 NumCPUs: 1  NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 2494.409 Cores: 1  Siblings: 1
# Kernel:     3.5.0-23-generic  Memory: 1011932 kB  Swap: 1046524 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    2 NetNames: eth0: lo:
# SCSI:       CD:1:00:00:00 DA:2:00:00:00le "/home/spar-dev/Documents/spar-git/spar_python/perf_monitoring/disk_log_parser_test.py", line 124, in test_get_names
################################################################################
#Date,Time,[DSK:sda]Name,[DSK:sda]Reads,[DSK:sda]RMerge,[DSK:sda]RKBytes,[DSK:sda]Writes,[DSK:sda]WMerge,[DSK:sda]WKBytes,[DSK:sda]Request,[DSK:sda]QueLen,[DSK:sda]Wait,[DSK:sda]SvcTim,[DSK:sda]Util
20130802,16:07:51.285,sda,112.41,0.00,2076.50,44.50,696.33,2963.31,32.12,7.43,47.28,6.29,98.70
20130802,16:07:52.568,sda,240.84,0.00,3710.05,4.68,10.13,59.24,15.35,8.39,34.44,4.06,99.80,sdb,301.64,3.12,2815.28,3.90,9.35,53.00,9.39,14.78,48.12,3.21,98.23
20130802,16:07:55.134,sda,143.41,4.68,1549.49,64.69,219.02,1122.37,12.84,17.26,81.84,4.79,99.78'''

TEST_DISK_LOG_FILE_2 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sD -i 1.283 -P -omz2 --sep , --filename /home/spar-dev/tests/disk.log 
# Host:       ubuntu  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130802-160749  Secs: 1375474069 TZ: -0400
# SubSys:     D Options: mz2 Interval: 1.283 NumCPUs: 1  NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 2494.409 Cores: 1  Siblings: 1
# Kernel:     3.5.0-23-generic  Memory: 1011932 kB  Swap: 1046524 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    2 NetNames: eth0: lo:
# SCSI:       CD:1:00:00:00 DA:2:00:00:00
################################################################################
#Date,Time,[DSK:sda]Name,[DSK:sda]Reads,[DSK:sda]RMerge,[DSK:sda]RKBytes,[DSK:sda]Writes,[DSK:sda]WMerge,[DSK:sda]WKBytes,[DSK:sda]Request,[DSK:sda]QueLen,[DSK:sda]Wait,[DSK:sda]SvcTim,[DSK:sda]Util
20130802,16:07:56.436,sda,142.86,2.30,7674.35,53.00,771.89,3228.88,55.67,18.64,96.52,5.10,99.83
20130802,16:07:57.700,sda,47.47,8.70,11297.47,34.02,1685.92,5901.90,211.07,35.52,393.59,12.08,98.44
20130802,16:07:59.518,sda,91.31,2.20,12998.90,12.10,482.95,2770.08,152.49,40.21,406.68,9.68,100.11'''

TEST_DISK_LOG_FILE_3 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sD -i 1.283 -P -omz2 --sep , --filename /home/spar-dev/tests/disk.log 
# Host:       ubuntu  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130802-160749  Secs: 1375474069 TZ: -0400
# SubSys:     D Options: mz2 Interval: 1.283 NumCPUs: 1  NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 2494.409 Cores: 1  Siblings: 1
# Kernel:     3.5.0-23-generic  Memory: 1011932 kB  Swap: 1046524 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    2 NetNames: eth0: lo:
# SCSI:       CD:1:00:00:00 DA:2:00:00:00
################################################################################
#Date,Time,[DSK:sda]Name,[DSK:sda]Reads,[DSK:sda]RMerge,[DSK:sda]RKBytes,[DSK:sda]Writes,[DSK:sda]WMerge,[DSK:sda]WKBytes,[DSK:sda]Request,[DSK:sda]QueLen,[DSK:sda]Wait,[DSK:sda]SvcTim,[DSK:sda]Util,[DSK:sdb]Name,[DSK:sdb]Reads,[DSK:sdb]RMerge,[DSK:sdb]RKBytes,[DSK:sdb]Writes,[DSK:sdb]WMerge,[DSK:sdb]WKBytes,[DSK:sdb]Request,[DSK:sdb]QueLen,[DSK:sdb]Wait,[DSK:sdb]SvcTim,[DSK:sdb]Util
20130802,16:08:00.550,sda,368.22,9.69,4317.83,0.00,0.00,0.00,11.73,12.35,34.15,2.71,99.61,sdb,368.22,9.69,4317.83,0.00,0.00,0.00,11.73,12.35,34.15,2.71,99.61
20130802,16:08:01.889,sda,238.24,0.75,9956.68,2.24,174.76,53.77,41.63,9.53,37.64,4.16,100.07,sdb,238.24,0.75,9956.68,2.24,174.76,53.77,41.63,9.53,37.64,4.16,100.07
20130802,16:08:03.124,sda,98.79,0.00,3844.53,49.39,472.06,2672.06,43.98,6.67,52.17,6.75,100.08,sdb,98.79,0.00,3844.53,49.39,472.06,2672.06,43.98,6.67,52.17,6.75,100.08
20130802,16:08:04.399,sda,159.22,0.00,4508.24,43.14,222.75,1182.75,28.12,4.73,23.49,4.95,100.11,sdb,301.87,35.88,2985.96,1.56,6.24,31.20,9.94,17.94,53.80,3.29,99.82
'''


class DiskLogParserTest(unittest.TestCase):
    '''Unit tests for network_log_parser.py'''
    
    
    def test_disk_log_entry_init(self):
        '''Unit test for DiskLogEntry.__init__
        
        Create a few objects, verify the contents'''        
        hosts = ["client", "client", "server"]
        time_epochs = [1373902408.283685, 1373902408.284399, 1373902408.286417]
        disk_names = ["sda", "hda", "hdb"]
        reads_per_secs = [23.2, 15, 32.1]
        reads_kbps = [1024.8, 92.3, 10000]
        writes_per_secs = [49.2, 39.9, 23]
        writes_kbps = [488.4, 1500.1, 1277]
           
        for i in range(len(hosts)):
            row = { "host" : hosts[i], "time_epoch" : time_epochs[i],
                    "disk_name" : disk_names[i],
                    "reads_per_sec" : reads_per_secs[i], "reads_kbps" : reads_kbps[i],
                    "writes_per_sec" : writes_per_secs[i], "writes_kbps" : writes_kbps[i]
                    }
            entry = dlp.DiskLogEntry(row)
            self.assertEqual(entry.host, hosts[i])
            self.assertEqual(entry.time_epoch, time_epochs[i])
            self.assertEqual(entry.disk_name, disk_names[i])
            self.assertEqual(entry.reads_per_sec, reads_per_secs[i])
            self.assertEqual(entry.reads_kbps, reads_kbps[i])
            self.assertEqual(entry.writes_per_sec, writes_per_secs[i])
            self.assertEqual(entry.writes_kbps, writes_kbps[i])
            
    def test_get_names(self):
        '''Unit test for DiskLogReader._get_disk_names'''
        
        fieldnames = ["Date", "Time", "[DSK:sda]Name", "[DSK:sda]Reads", 
                      "[DSK:sdb]Name", "[DSK:sdb]Reads", "[DSK:abcdefghijklmnop]Name"]
        expected_disks = ["sda", "sdb", "abcdefghijklmnop"]

        actual_disks = dlp.DiskLogReader()._get_disk_names(fieldnames)
        self.assertEqual(expected_disks, actual_disks)

    def test_add_handle(self):
        '''Unit test for DiskLogreader.add_handle
        
        Add multiple files, ensure contents from each file
        are contained in the result'''
        reader = dlp.DiskLogReader()
        reader.add_handle(StringIO.StringIO(TEST_DISK_LOG_FILE_1), "client")
        reader.add_handle(StringIO.StringIO(TEST_DISK_LOG_FILE_2), "server")
        reader.add_handle(StringIO.StringIO(TEST_DISK_LOG_FILE_3), "thirdparty")
        
        expected_entries = [
            {
            "host" : "client",
            "time_epoch" :  date_and_time_to_epoch("20130802", "16:07:52.568"),
            "disk_name" : "sda",
            "reads_per_sec" : 240.84,
            "reads_kbps" : 3710.05,
            "writes_per_sec" : 4.68,
            "writes_kbps" : 59.24
            },
            {
            "host" : "server",
            "time_epoch" :  date_and_time_to_epoch("20130802", "16:07:57.700"),
            "disk_name" : "sda",
            "reads_per_sec" : 47.47,
            "reads_kbps" : 11297.47,
            "writes_per_sec" : 34.02,
            "writes_kbps" : 5901.90
            },                      
            {
            "host" : "thirdparty",
            "time_epoch" :  date_and_time_to_epoch("20130802", "16:08:04.399"),
            "disk_name" : "sdb",
            "reads_per_sec" : 301.87,
            "reads_kbps" : 2985.96,
            "writes_per_sec" : 1.56,
            "writes_kbps" : 31.20
            } 
            ]
        
        for entry in expected_entries:
            self.assertIn(dlp.DiskLogEntry(entry), reader.entries)
            
    

    def test_write_to_database(self):
        '''Unit test for write_to_database
        
        Generate some records, write them to database
        query database, ensure records in db'''
        
        reader = dlp.DiskLogReader(StringIO.StringIO(TEST_DISK_LOG_FILE_1), "client")
        reader.add_handle(StringIO.StringIO(TEST_DISK_LOG_FILE_2), "server")
        reader.add_handle(StringIO.StringIO(TEST_DISK_LOG_FILE_3), "thirdparty")
        
        con = perfdb.create_perf_db(":memory:")
        reader.write_to_database(con)
                
        expected_entries = [
            {
            "host" : "client",
            "time_epoch" :  date_and_time_to_epoch("20130802", "16:07:52.568"),
            "disk_name" : "sda",
            "reads_per_sec" : 240.84,
            "reads_kbps" : 3710.05,
            "writes_per_sec" : 4.68,
            "writes_kbps" : 59.24
            },
            {
            "host" : "server",
            "time_epoch" :  date_and_time_to_epoch("20130802", "16:07:57.700"),
            "disk_name" : "sda",
            "reads_per_sec" : 47.47,
            "reads_kbps" : 11297.47,
            "writes_per_sec" : 34.02,
            "writes_kbps" : 5901.90
            },                      
            {
            "host" : "thirdparty",
            "time_epoch" :  date_and_time_to_epoch("20130802", "16:08:04.399"),
            "disk_name" : "sdb",
            "reads_per_sec" : 301.87,
            "reads_kbps" : 2985.96,
            "writes_per_sec" : 1.56,
            "writes_kbps" : 31.20
            }
            ]

        expected_rows = []
        for entry in expected_entries:
            expected_rows.append((entry["host"], epoch_to_sql(entry["time_epoch"]), 
                                  entry["disk_name"], 
                                  entry["reads_per_sec"], entry["reads_kbps"],
                                  entry["writes_per_sec"], entry["writes_kbps"])) 
        
        query = "SELECT host, time, disk_name, reads_per_sec, reads_kbps, writes_per_sec, writes_kbps FROM Disk;"
        cursor = con.cursor()
        cursor.execute(query)
        actual_rows = cursor.fetchall()
        
        for entry in expected_rows:
            self.assertIn(entry, actual_rows)
            


