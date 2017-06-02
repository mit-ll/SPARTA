#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module contains the unit tests for
#                      perf_db.py                     
# *****************************************************************

import unittest
import time
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.perf_db import create_perf_db, \
    insert_network, insert_cpu, insert_ram, insert_disk
from spar_python.perf_monitoring.time_utils import epoch_to_sql

class PerfDBTest(unittest.TestCase):
    '''Class to hold unit tests for perf_db.py'''
    
    def test_create_perf_db(self):
        '''unit test for create_perf_db
        
        Ensure that tables are created'''
        con = create_perf_db(":memory:")
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        self.assertIn(("Network",), tables)
        self.assertIn(("Cpu",), tables)
        self.assertIn(("Ram",), tables)
        self.assertIn(("Disk",), tables)
        
        
    def test_insert_network(self):
        '''unit test for insert_network
        
        Insert a few values and make sure they can be retrieved'''
        times = [
                 time.time(),
                 time.time() + 15.347,
                 time.time() + 53.421
                 ] 
        directions = ["client_to_server", 
                      "server_to_client", "server_to_client"]
        payload_sizes = [500, 1024, 1460]
        protocols = ["IP/TCP", "IP/TCP", "IP/TCP"]
        
        con = create_perf_db(":memory:")
        expected_rows = []
        for i in range(len(times)):
            insert_network(con, times[i], directions[i], payload_sizes[i],
                            protocols[i], commit=False)
            expected_rows.append((epoch_to_sql(times[i]), directions[i], 
                                  payload_sizes[i], protocols[i]))       
        con.commit()
        cur = con.cursor()
        query = "SELECT time, direction, payloadlength, protocol FROM Network;"
        cur.execute(query)
        results = cur.fetchall()
        self.assertEqual(len(expected_rows), len(results))
        for row in expected_rows:
            self.assertIn(row, results)
            
    def test_insert_cpu(self):
        '''unit test for insert_network
        
        Insert a few values and make sure they can be retrieved'''
        hosts = ["client", "client", "server"]
        identifiers = ["cpu1", "cpu2", "cpu1"]
        times = [
                 time.time(),
                 time.time() + 15.347,
                 time.time() + 53.421
                 ] 
        user_pcts = [23.7, 32.4, 77.8]
        sys_pcts = [10.2, 23.2, 8.3]
        wait_pcts = [1.1, 0.0, 2.1]
        irq_pcts = [2.3, 4.3, 0.1]
        idle_pcts = [0.0, 0.5, 0.0]
        total_pcts = [33.9, 55.6, 86.1]
        
        expected_rows = []
        con = create_perf_db(":memory:")
        for i in range(len(hosts)):
            insert_cpu(con, hosts[i], identifiers[i], times[i],  
                       user_pcts[i], sys_pcts[i], wait_pcts[i], irq_pcts[i],
                       idle_pcts[i], total_pcts[i], commit=False)
            expected_rows.append((hosts[i], identifiers[i], 
                       epoch_to_sql(times[i]), user_pcts[i], sys_pcts[i], 
                       wait_pcts[i], irq_pcts[i], idle_pcts[i], total_pcts[i]))
        con.commit()
        cur = con.cursor()
        query = "SELECT host, cpu_identifier, time, user_pct, sys_pct, wait_pct, irq_pct, idle_pct, total_pct from Cpu;"
        cur.execute(query)
        results = cur.fetchall()
        self.assertEqual(len(expected_rows), len(results))
        for row in expected_rows:
            self.assertIn(row, results)
            
    def test_insert_ram(self):
        '''unit test for insert_ram
        
        Insert a few values and make sure they can be retrieved'''
        
        hosts = ["client", "thirdparty", "thirdparty"]
        times = [
                 time.time(),
                 time.time() + 15.347,
                 time.time() + 53.421
                 ]
        used_kbs = [1024, 2047.0, 2046.3]
        free_kbs = [0.0, 1.0, 0.7]
        swap_totals = [4096.0, 8192.0, 8192.0]
        swap_useds = [1234.5, 2102.7, 4212.0]
        swap_frees = [2861.5, 6089.3, 3980.0]
        
        expected_rows = []
        con = create_perf_db(":memory:")
        for i in range(len(hosts)):
            insert_ram(con, hosts[i], times[i], used_kbs[i], 
                       free_kbs[i], swap_totals[i], swap_useds[i], 
                       swap_frees[i], commit=False)
            expected_rows.append((hosts[i], epoch_to_sql(times[i]), 
                       used_kbs[i], free_kbs[i], swap_totals[i], swap_useds[i],
                       swap_frees[i]))
        con.commit()
        cur = con.cursor()
        query = "SELECT host, time, used_kb, free_kb, swap_total, swap_used, swap_free from Ram;"
        cur.execute(query)
        results = cur.fetchall()
        self.assertEqual(len(expected_rows), len(results))
        for row in expected_rows:
            self.assertIn(row, results)
            
    def test_insert_disk(self):
        '''unit test for insert_disk
        
        Insert a few vlues and make sure they can be retrieved'''
        hosts = ["thirdparty", "thirdparty", "server"]
        times = [
                 time.time(),
                 time.time() + 15.347,
                 time.time() + 53.421
                 ]        
        disk_names = ["/dev/sda", "/dev/sdb", "/dev/hda"]
        reads_per_secs = [5.3, 4.7, 6.8]
        reads_kbps = [48.6, 983.2, 43.7]
        writes_per_secs = [76.2, 53.4, 98.2]
        writes_kbps = [123.4, 321.5, 1023.7]
        
        expected_rows = []
        con = create_perf_db(":memory:")
        for i in range(len(hosts)):
            insert_disk(con, hosts[i], times[i], disk_names[i], 
                       reads_per_secs[i], reads_kbps[i], writes_per_secs[i], 
                       writes_kbps[i], commit=False)
            expected_rows.append((hosts[i], epoch_to_sql(times[i]), 
                       disk_names[i], reads_per_secs[i], reads_kbps[i], 
                       writes_per_secs[i], writes_kbps[i]))
        con.commit()
        cur = con.cursor()
        query = "SELECT host, time, disk_name, reads_per_sec, reads_kbps, writes_per_sec, writes_kbps from Disk;"
        cur.execute(query)
        results = cur.fetchall()
        self.assertEqual(len(expected_rows), len(results))
        for row in expected_rows:
            self.assertIn(row, results)

        
        