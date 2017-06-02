#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      ram_log_parser.py 
# *****************************************************************


import unittest
import StringIO
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.perf_monitoring.ram_log_parser as rlp
import spar_python.perf_monitoring.perf_db as perfdb
from spar_python.perf_monitoring.time_utils import date_and_time_to_epoch, epoch_to_sql


TEST_RAM_LOG_FILE_1 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sm -i 3 --filename ram_sample -P -omz --sep , 
# Host:       ubuntu  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130731-113329  Secs: 1375284809 TZ: -0400
# SubSys:     m Options: mz Interval: 3 NumCPUs: 1  NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 2494.409 Cores: 1  Siblings: 1
# Kernel:     3.5.0-23-generic  Memory: 1011932 kB  Swap: 1046524 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    2 NetNames: eth0: lo:
# SCSI:       CD:1:00:00:00 DA:2:00:00:00
################################################################################
#Date,Time,[MEM]Tot,[MEM]Used,[MEM]Free,[MEM]Shared,[MEM]Buf,[MEM]Cached,[MEM]Slab,[MEM]Map,[MEM]Commit,[MEM]SwapTot,[MEM]SwapUsed,[MEM]SwapFree,[MEM]SwapIn,[MEM]SwapOut,[MEM]Dirty,[MEM]Clean,[MEM]Laundry,[MEM]Inactive,[MEM]PageIn,[MEM]PageOut,[MEM]PageFaults,[MEM]PageMajFaults,[MEM]HugeTotal,[MEM]HugeFree,[MEM]HugeRsvd,[MEM]SUnreclaim
20130731,11:33:33.003,1011932,940564,71368,0,16460,114736,65824,693116,3268208,1046524,304800,741724,0,178,108,0,0,51936,0,762,9,0,0,0,0,26180
20130731,11:33:36.002,1011932,940564,71368,0,16464,114736,65824,693132,3268208,1046524,304800,741724,0,0,112,0,0,51924,1,0,18,0,0,0,0,26180'''

TEST_RAM_LOG_FILE_2 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sm -i 3 --filename ram_sample -P -omz --sep , 
# Host:       ubuntu  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130731-113329  Secs: 1375284809 TZ: -0400
# SubSys:     m Options: mz Interval: 3 NumCPUs: 1  NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 2494.409 Cores: 1  Siblings: 1
# Kernel:     3.5.0-23-generic  Memory: 1011932 kB  Swap: 1046524 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    2 NetNames: eth0: lo:
# SCSI:       CD:1:00:00:00 DA:2:00:00:00
################################################################################
#Date,Time,[MEM]Tot,[MEM]Used,[MEM]Free,[MEM]Shared,[MEM]Buf,[MEM]Cached,[MEM]Slab,[MEM]Map,[MEM]Commit,[MEM]SwapTot,[MEM]SwapUsed,[MEM]SwapFree,[MEM]SwapIn,[MEM]SwapOut,[MEM]Dirty,[MEM]Clean,[MEM]Laundry,[MEM]Inactive,[MEM]PageIn,[MEM]PageOut,[MEM]PageFaults,[MEM]PageMajFaults,[MEM]HugeTotal,[MEM]HugeFree,[MEM]HugeRsvd,[MEM]SUnreclaim
20130731,11:33:39.003,1011932,940564,71368,0,16472,114736,65824,693144,3268208,1046524,304800,741724,0,0,116,0,0,51932,0,15,2,0,0,0,0,26180
20130731,11:33:42.003,1011932,940688,71244,0,16472,114736,65824,693200,3268208,1046524,304800,741724,0,0,112,0,0,51932,0,1,87,0,0,0,0,26180
20130731,11:33:45.002,1011932,940440,71492,0,16472,114736,65824,692952,3268208,1046524,304800,741724,0,0,120,0,0,51932,0,0,94,0,0,0,0,26180
20130731,11:33:48.003,1011932,940316,71616,0,16480,114736,65824,692952,3268208,1046524,304800,741724,0,0,64,0,0,51936,0,36,189,0,0,0,0,26180'''

TEST_RAM_LOG_FILE_3 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sm -i 3 --filename ram_sample -P -omz --sep , 
# Host:       ubuntu  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130731-113329  Secs: 1375284809 TZ: -0400
# SubSys:     m Options: mz Interval: 3 NumCPUs: 1  NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 2494.409 Cores: 1  Siblings: 1
# Kernel:     3.5.0-23-generic  Memory: 1011932 kB  Swap: 1046524 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    2 NetNames: eth0: lo:
# SCSI:       CD:1:00:00:00 DA:2:00:00:00
################################################################################
#Date,Time,[MEM]Tot,[MEM]Used,[MEM]Free,[MEM]Shared,[MEM]Buf,[MEM]Cached,[MEM]Slab,[MEM]Map,[MEM]Commit,[MEM]SwapTot,[MEM]SwapUsed,[MEM]SwapFree,[MEM]SwapIn,[MEM]SwapOut,[MEM]Dirty,[MEM]Clean,[MEM]Laundry,[MEM]Inactive,[MEM]PageIn,[MEM]PageOut,[MEM]PageFaults,[MEM]PageMajFaults,[MEM]HugeTotal,[MEM]HugeFree,[MEM]HugeRsvd,[MEM]SUnreclaim
20130731,11:33:51.003,1011932,939572,72360,0,16480,114736,65824,692124,3267184,1046524,304800,741724,0,0,64,0,0,51940,0,0,0,0,0,0,0,26180
20130731,11:33:54.002,1011932,939572,72360,0,16480,114736,65824,692124,3267184,1046524,304800,741724,0,0,64,0,0,51940,0,0,0,0,0,0,0,26180
20130731,11:33:57.003,1011932,938580,73352,0,16488,114728,65824,691120,3267184,1046524,304800,741724,0,0,112,0,0,51940,0,31,88,0,0,0,0,26180'''


class RamLogParserTest(unittest.TestCase):
    '''Unit tests for network_log_parser.py'''
        
    def test_ram_log_entry_init(self):
        '''Unit test for RamLogEntry.__init__
        
        Create a few objects, verify the contents'''
        
        hosts = ["client", "client", "server"]
        time_epochs = [1373902408.283685, 1373902408.284399, 1373902408.286417]
        used_kbs = [1123, 6453943, 23435]
        free_kbs = [984651, 153, 55152]
        swap_totals = [1000, 5000, 10000]
        swap_useds = [512, 3499.9, 8723]
        swap_frees = [488, 1500.1, 1277]
           
        for i in range(len(hosts)):
            row = { "host" : hosts[i], "time_epoch" : time_epochs[i],
                    "used_kb" : used_kbs[i],
                    "free_kb" : free_kbs[i], "swap_total" : swap_totals[i],
                    "swap_used" : swap_useds[i], "swap_free" : swap_frees[i]                    }
            entry = rlp.RamLogEntry(row)
            self.assertEqual(entry.host, hosts[i])
            self.assertEqual(entry.time_epoch, time_epochs[i])
            self.assertEqual(entry.used_kb, used_kbs[i])
            self.assertEqual(entry.free_kb, free_kbs[i])
            self.assertEqual(entry.swap_total, swap_totals[i])
            self.assertEqual(entry.swap_used, swap_useds[i])
            self.assertEqual(entry.swap_free, swap_frees[i])
            
            
    def test_add_handle(self):
        '''Unit test for RamLogreader.add_handle
        
        Add multiple files, ensure contents from each file
        are contained in the result'''
        reader = rlp.RamLogReader()
        reader.add_handle(StringIO.StringIO(TEST_RAM_LOG_FILE_1), "client")
        reader.add_handle(StringIO.StringIO(TEST_RAM_LOG_FILE_2), "thirdparty")
        reader.add_handle(StringIO.StringIO(TEST_RAM_LOG_FILE_3), "thirdparty")
        
        expected_entries = [
            {
            "host" : "client",
            "time_epoch" :  date_and_time_to_epoch("20130731", "11:33:33.003"),
            "free_kb" : 71368,
            "used_kb" : 940564,
            "swap_total" : 1046524,
            "swap_used" : 304800,
            "swap_free" : 741724
            },
            {
            "host" : "thirdparty",
            "time_epoch" :  date_and_time_to_epoch("20130731", "11:33:42.003"),
            "free_kb" : 71244,
            "used_kb" : 940688,
            "swap_total" : 1046524,
            "swap_used" : 304800,
            "swap_free" : 741724
            },                      
            {
            "host" : "thirdparty",
            "time_epoch" :  date_and_time_to_epoch("20130731", "11:33:57.003"),
            "free_kb" : 73352,
            "used_kb" : 938580,
            "swap_total" : 1046524,
            "swap_used" : 304800,
            "swap_free" : 741724
            }
            ]
        
        for entry in expected_entries:
            self.assertIn(rlp.RamLogEntry(entry), reader.entries)


    def test_write_to_database(self):
        '''Unit test for write_to_database
        
        Generate some records, write them to database
        query database, ensure records in db'''
        
        reader = rlp.RamLogReader(StringIO.StringIO(TEST_RAM_LOG_FILE_1), "client")
        reader.add_handle(StringIO.StringIO(TEST_RAM_LOG_FILE_2), "thirdparty")
        reader.add_handle(StringIO.StringIO(TEST_RAM_LOG_FILE_3), "thirdparty")
        
        con = perfdb.create_perf_db(":memory:")
        reader.write_to_database(con)
                
        expected_entries = [
            {
            "host" : "client",
            "time_epoch" :  date_and_time_to_epoch("20130731", "11:33:33.003"),
            "free_kb" : 71368,
            "used_kb" : 940564,
            "swap_total" : 1046524,
            "swap_used" : 304800,
            "swap_free" : 741724
            },
            {
            "host" : "thirdparty",
            "time_epoch" :  date_and_time_to_epoch("20130731", "11:33:42.003"),
            "free_kb" : 71244,
            "used_kb" : 940688,
            "swap_total" : 1046524,
            "swap_used" : 304800,
            "swap_free" : 741724
            },                      
            {
            "host" : "thirdparty",
            "time_epoch" :  date_and_time_to_epoch("20130731", "11:33:57.003"),
            "free_kb" : 73352,
            "used_kb" : 938580,
            "swap_total" : 1046524,
            "swap_used" : 304800,
            "swap_free" : 741724
            }
            ]

        expected_rows = []
        for entry in expected_entries:
            expected_rows.append((entry["host"], epoch_to_sql(entry["time_epoch"]), 
                                  entry["free_kb"], 
                                  entry["used_kb"], entry["swap_total"],
                                  entry["swap_used"], entry["swap_free"])) 
        
        query = "SELECT host, time, free_kb, used_kb, swap_total, swap_used, swap_free FROM Ram;"
        cursor = con.cursor()
        cursor.execute(query)
        actual_rows = cursor.fetchall()
        
        for entry in expected_rows:
            self.assertIn(entry, actual_rows)
            
            