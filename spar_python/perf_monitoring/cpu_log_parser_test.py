#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      cpu_log_parser.py 
# *****************************************************************


import unittest
import StringIO
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.perf_monitoring.cpu_log_parser as clp
import spar_python.perf_monitoring.perf_db as perfdb
from spar_python.perf_monitoring.time_utils import date_and_time_to_epoch, epoch_to_sql

TEST_CPU_LOG_FILE_1 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sC -i 1.376 --filename cpu.log -P -om2z --sep , 
# Host:       sparllan05  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130805-113854  Secs: 1375727934 TZ: -0700
# SubSys:     C Options: m2z Interval: 1.376 NumCPUs: 8 [HYPER] NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 1600.000 Cores: 4  Siblings: 8
# Kernel:     3.2.0-29-generic  Memory: 16404896 kB  Swap: 7999484 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    3 NetNames: lo: eth1: eth0:
# SCSI:       DA:0:00:00:00
###############################################################################
#Date,Time,[CPU:0]User%,[CPU:0]Nice%,[CPU:0]Sys%,[CPU:0]Wait%,[CPU:0]Irq%,[CPU:0]Soft%,[CPU:0]Steal%,[CPU:0]Idle%,[CPU:0]Totl%,[CPU:0]Intrpt,[CPU:1]User%,[CPU:1]Nice%,[CPU:1]Sys%,[CPU:1]Wait%,[CPU:1]Irq%,[CPU:1]Soft%,[CPU:1]Steal%,[CPU:1]Idle%,[CPU:1]Totl%,[CPU:1]Intrpt,[CPU:2]User%,[CPU:2]Nice%,[CPU:2]Sys%,[CPU:2]Wait%,[CPU:2]Irq%,[CPU:2]Soft%,[CPU:2]Steal%,[CPU:2]Idle%,[CPU:2]Totl%,[CPU:2]Intrpt,[CPU:3]User%,[CPU:3]Nice%,[CPU:3]Sys%,[CPU:3]Wait%,[CPU:3]Irq%,[CPU:3]Soft%,[CPU:3]Steal%,[CPU:3]Idle%,[CPU:3]Totl%,[CPU:3]Intrpt,[CPU:4]User%,[CPU:4]Nice%,[CPU:4]Sys%,[CPU:4]Wait%,[CPU:4]Irq%,[CPU:4]Soft%,[CPU:4]Steal%,[CPU:4]Idle%,[CPU:4]Totl%,[CPU:4]Intrpt,[CPU:5]User%,[CPU:5]Nice%,[CPU:5]Sys%,[CPU:5]Wait%,[CPU:5]Irq%,[CPU:5]Soft%,[CPU:5]Steal%,[CPU:5]Idle%,[CPU:5]Totl%,[CPU:5]Intrpt,[CPU:6]User%,[CPU:6]Nice%,[CPU:6]Sys%,[CPU:6]Wait%,[CPU:6]Irq%,[CPU:6]Soft%,[CPU:6]Steal%,[CPU:6]Idle%,[CPU:6]Totl%,[CPU:6]Intrpt,[CPU:7]User%,[CPU:7]Nice%,[CPU:7]Sys%,[CPU:7]Wait%,[CPU:7]Irq%,[CPU:7]Soft%,[CPU:7]Steal%,[CPU:7]Idle%,[CPU:7]Totl%,[CPU:7]Intrpt
20130805,11:38:56.377,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.72,0.00,0.00,0.00,0.00,0.00,0.00,99.28,0.72,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00
20130805,11:38:57.753,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00'''

TEST_CPU_LOG_FILE_2 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sC -i 1.376 --filename cpu.log -P -om2z --sep , 
# Host:       sparllan05  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130805-113854  Secs: 1375727934 TZ: -0700
# SubSys:     C Options: m2z Interval: 1.376 NumCPUs: 8 [HYPER] NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 1600.000 Cores: 4  Siblings: 8
# Kernel:     3.2.0-29-generic  Memory: 16404896 kB  Swap: 7999484 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    3 NetNames: lo: eth1: eth0:
# SCSI:       DA:0:00:00:00
###############################################################################
#Date,Time,[CPU:0]User%,[CPU:0]Nice%,[CPU:0]Sys%,[CPU:0]Wait%,[CPU:0]Irq%,[CPU:0]Soft%,[CPU:0]Steal%,[CPU:0]Idle%,[CPU:0]Totl%,[CPU:0]Intrpt,[CPU:1]User%,[CPU:1]Nice%,[CPU:1]Sys%,[CPU:1]Wait%,[CPU:1]Irq%,[CPU:1]Soft%,[CPU:1]Steal%,[CPU:1]Idle%,[CPU:1]Totl%,[CPU:1]Intrpt,[CPU:2]User%,[CPU:2]Nice%,[CPU:2]Sys%,[CPU:2]Wait%,[CPU:2]Irq%,[CPU:2]Soft%,[CPU:2]Steal%,[CPU:2]Idle%,[CPU:2]Totl%,[CPU:2]Intrpt,[CPU:3]User%,[CPU:3]Nice%,[CPU:3]Sys%,[CPU:3]Wait%,[CPU:3]Irq%,[CPU:3]Soft%,[CPU:3]Steal%,[CPU:3]Idle%,[CPU:3]Totl%,[CPU:3]Intrpt,[CPU:4]User%,[CPU:4]Nice%,[CPU:4]Sys%,[CPU:4]Wait%,[CPU:4]Irq%,[CPU:4]Soft%,[CPU:4]Steal%,[CPU:4]Idle%,[CPU:4]Totl%,[CPU:4]Intrpt,[CPU:5]User%,[CPU:5]Nice%,[CPU:5]Sys%,[CPU:5]Wait%,[CPU:5]Irq%,[CPU:5]Soft%,[CPU:5]Steal%,[CPU:5]Idle%,[CPU:5]Totl%,[CPU:5]Intrpt,[CPU:6]User%,[CPU:6]Nice%,[CPU:6]Sys%,[CPU:6]Wait%,[CPU:6]Irq%,[CPU:6]Soft%,[CPU:6]Steal%,[CPU:6]Idle%,[CPU:6]Totl%,[CPU:6]Intrpt,[CPU:7]User%,[CPU:7]Nice%,[CPU:7]Sys%,[CPU:7]Wait%,[CPU:7]Irq%,[CPU:7]Soft%,[CPU:7]Steal%,[CPU:7]Idle%,[CPU:7]Totl%,[CPU:7]Intrpt
20130805,11:38:59.129,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.72,0.00,0.00,0.00,0.00,0.00,0.00,99.28,0.72,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00
20130805,11:39:00.505,0.00,0.00,0.00,2.16,0.00,0.00,0.00,97.84,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,2.94,0.00,0.74,0.00,0.00,0.00,0.00,96.32,3.68,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.72,0.00,0.00,0.00,0.00,0.00,0.00,99.28,0.72,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00
20130805,11:39:01.881,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.72,0.00,0.00,0.00,0.00,0.00,0.00,99.28,0.72,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00'''

TEST_CPU_LOG_FILE_3 = '''################################################################################
# Collectl:   V3.6.0-1  HiRes: 1  Options: -sC -i 1.376 --filename cpu.log -P -om2z --sep , 
# Host:       sparllan05  DaemonOpts: 
# Distro:       Platform: 
# Date:       20130805-113854  Secs: 1375727934 TZ: -0700
# SubSys:     C Options: m2z Interval: 1.376 NumCPUs: 8 [HYPER] NumBud: 0 Flags: i
# Filters:    NfsFilt:  EnvFilt: 
# HZ:         100  Arch: x86_64-linux-gnu-thread-multi PageSize: 4096
# Cpu:        GenuineIntel Speed(MHz): 1600.000 Cores: 4  Siblings: 8
# Kernel:     3.2.0-29-generic  Memory: 16404896 kB  Swap: 7999484 kB
# NumDisks:   1 DiskNames: sda
# NumNets:    3 NetNames: lo: eth1: eth0:
# SCSI:       DA:0:00:00:00
###############################################################################
#Date,Time,[CPU:0]User%,[CPU:0]Nice%,[CPU:0]Sys%,[CPU:0]Wait%,[CPU:0]Irq%,[CPU:0]Soft%,[CPU:0]Steal%,[CPU:0]Idle%,[CPU:0]Totl%,[CPU:0]Intrpt,[CPU:1]User%,[CPU:1]Nice%,[CPU:1]Sys%,[CPU:1]Wait%,[CPU:1]Irq%,[CPU:1]Soft%,[CPU:1]Steal%,[CPU:1]Idle%,[CPU:1]Totl%,[CPU:1]Intrpt,[CPU:2]User%,[CPU:2]Nice%,[CPU:2]Sys%,[CPU:2]Wait%,[CPU:2]Irq%,[CPU:2]Soft%,[CPU:2]Steal%,[CPU:2]Idle%,[CPU:2]Totl%,[CPU:2]Intrpt,[CPU:3]User%,[CPU:3]Nice%,[CPU:3]Sys%,[CPU:3]Wait%,[CPU:3]Irq%,[CPU:3]Soft%,[CPU:3]Steal%,[CPU:3]Idle%,[CPU:3]Totl%,[CPU:3]Intrpt,[CPU:4]User%,[CPU:4]Nice%,[CPU:4]Sys%,[CPU:4]Wait%,[CPU:4]Irq%,[CPU:4]Soft%,[CPU:4]Steal%,[CPU:4]Idle%,[CPU:4]Totl%,[CPU:4]Intrpt,[CPU:5]User%,[CPU:5]Nice%,[CPU:5]Sys%,[CPU:5]Wait%,[CPU:5]Irq%,[CPU:5]Soft%,[CPU:5]Steal%,[CPU:5]Idle%,[CPU:5]Totl%,[CPU:5]Intrpt,[CPU:6]User%,[CPU:6]Nice%,[CPU:6]Sys%,[CPU:6]Wait%,[CPU:6]Irq%,[CPU:6]Soft%,[CPU:6]Steal%,[CPU:6]Idle%,[CPU:6]Totl%,[CPU:6]Intrpt,[CPU:7]User%,[CPU:7]Nice%,[CPU:7]Sys%,[CPU:7]Wait%,[CPU:7]Irq%,[CPU:7]Soft%,[CPU:7]Steal%,[CPU:7]Idle%,[CPU:7]Totl%,[CPU:7]Intrpt
20130805,11:39:03.257,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.72,0.00,0.00,0.00,0.00,0.00,0.00,99.28,0.72,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00
20130805,11:39:04.633,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00
20130805,11:39:06.009,0.00,0.00,0.00,2.17,0.00,0.00,0.00,97.83,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.72,0.00,0.00,0.00,0.00,0.00,0.00,99.28,0.72,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,100.00,0.00,0.00'''


class CpuLogParserTest(unittest.TestCase):
    '''Unit tests for network_log_parser.py'''
    
    
    def test_cpu_log_entry_init(self):
        '''Unit test for CpuLogEntry.__init__
        
        Create a few objects, verify the contents'''        
        hosts = ["client", "client", "server"]
        time_epochs = [1373902408.283685, 1373902408.284399, 1373902408.286417]
        cpu_identifiers = ["cpu_0", "cpu_5", "cpu_7"]
        user_pcts = [23.2, 15, 32.1]
        sys_pcts = [10, 4.3, 0]
        wait_pcts = [0, 2.7, 9]
        irq_pcts = [13.4, 2.9, 0.01]
        idle_pcts = [3.71, 9.21, 2.12]
        total_pcts = [33.2, 19.3, 32.1]
           
        for i in range(len(hosts)):
            row = { "host" : hosts[i], "time_epoch" : time_epochs[i],
                    "cpu_identifier" : cpu_identifiers[i],
                    "user_pct" : user_pcts[i], "sys_pct" : sys_pcts[i],
                    "wait_pct" : wait_pcts[i], "irq_pct" : irq_pcts[i],
                    "idle_pct" : idle_pcts[i], "total_pct" : total_pcts[i] }
            entry = clp.CpuLogEntry(row)
            self.assertEqual(entry.host, hosts[i])
            self.assertEqual(entry.time_epoch, time_epochs[i])
            self.assertEqual(entry.cpu_identifier, cpu_identifiers[i])
            self.assertEqual(entry.user_pct, user_pcts[i])
            self.assertEqual(entry.sys_pct, sys_pcts[i])
            self.assertEqual(entry.wait_pct, wait_pcts[i])
            self.assertEqual(entry.irq_pct, irq_pcts[i])
            self.assertEqual(entry.idle_pct, idle_pcts[i])
            self.assertEqual(entry.total_pct, total_pcts[i])
            
    def test_add_handle(self):
        '''Unit test for CpuLogReader.add_handle
        
        Add multiple files, ensure contents from each file
        are contained in the result'''
        reader = clp.CpuLogReader()
        reader.add_handle(StringIO.StringIO(TEST_CPU_LOG_FILE_1), "client")
        reader.add_handle(StringIO.StringIO(TEST_CPU_LOG_FILE_2), "server")
        reader.add_handle(StringIO.StringIO(TEST_CPU_LOG_FILE_3), "thirdparty")
        
        expected_entries = [
            {
             "host" : "client", 
             "time_epoch" : date_and_time_to_epoch("20130805", "11:38:56.377"),
             "cpu_identifier" : "cpu_6",   
             "user_pct" : .72, 
             "sys_pct" : 0.0,
             "wait_pct" : 0.0, 
             "irq_pct" : 0.0,
             "idle_pct" : 99.28, 
             "total_pct" : .72 
            },
            {
             "host" : "server", 
             "time_epoch" : date_and_time_to_epoch("20130805", "11:39:00.505"),
             "cpu_identifier" : "cpu_4",   
             "user_pct" : 2.94, 
             "sys_pct" : 0.74,
             "wait_pct" : 0.0, 
             "irq_pct" : 0.0,
             "idle_pct" : 96.32, 
             "total_pct" : 3.68 
            },                      
            {
             "host" : "thirdparty", 
             "time_epoch" : date_and_time_to_epoch("20130805", "11:39:06.009"),
             "cpu_identifier" : "cpu_0",   
             "user_pct" : 0.0, 
             "sys_pct" : 0.0,
             "wait_pct" : 2.17, 
             "irq_pct" : 0.0,
             "idle_pct" : 97.83, 
             "total_pct" : 0.0 
            } 
            ]
        
        for entry in expected_entries:
            self.assertIn(clp.CpuLogEntry(entry), reader.entries)

            
    def test_write_to_database(self):
        '''Unit test for write_to_database
        
        Generate some records, write them to database
        query database, ensure records in db'''
        
        reader = clp.CpuLogReader(StringIO.StringIO(TEST_CPU_LOG_FILE_1), "client")
        reader.add_handle(StringIO.StringIO(TEST_CPU_LOG_FILE_2), "server")
        reader.add_handle(StringIO.StringIO(TEST_CPU_LOG_FILE_3), "thirdparty")
        
        con = perfdb.create_perf_db(":memory:")
        reader.write_to_database(con)
                
        expected_entries = [
            {
             "host" : "client", 
             "time_epoch" : date_and_time_to_epoch("20130805", "11:38:56.377"),
             "cpu_identifier" : "cpu_6",   
             "user_pct" : .72, 
             "sys_pct" : 0.0,
             "wait_pct" : 0.0, 
             "irq_pct" : 0.0,
             "idle_pct" : 99.28, 
             "total_pct" : .72 
            },
            {
             "host" : "server", 
             "time_epoch" : date_and_time_to_epoch("20130805", "11:39:00.505"),
             "cpu_identifier" : "cpu_4",   
             "user_pct" : 2.94, 
             "sys_pct" : 0.74,
             "wait_pct" : 0.0, 
             "irq_pct" : 0.0,
             "idle_pct" : 96.32, 
             "total_pct" : 3.68 
            },                      
            {
             "host" : "thirdparty", 
             "time_epoch" : date_and_time_to_epoch("20130805", "11:39:06.009"),
             "cpu_identifier" : "cpu_0",   
             "user_pct" : 0.0, 
             "sys_pct" : 0.0,
             "wait_pct" : 2.17, 
             "irq_pct" : 0.0,
             "idle_pct" : 97.83, 
             "total_pct" : 0.0 
            } 
            ]

        expected_rows = []
        for entry in expected_entries:
            expected_rows.append((entry["host"], epoch_to_sql(entry["time_epoch"]), 
                                  entry["cpu_identifier"], 
                                  entry["user_pct"], entry["sys_pct"],
                                  entry["wait_pct"], entry["irq_pct"],
                                  entry["idle_pct"], entry["total_pct"])) 
        
        query = "SELECT host, time, cpu_identifier, user_pct, sys_pct, wait_pct, irq_pct, idle_pct, total_pct from Cpu;"
        cursor = con.cursor()
        cursor.execute(query)
        actual_rows = cursor.fetchall()
        
        for entry in expected_rows:
            self.assertIn(entry, actual_rows)
            