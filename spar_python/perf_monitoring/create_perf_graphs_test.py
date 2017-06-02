#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      create_perf_graphs.py 
# *****************************************************************


import sqlite3
import unittest
import StringIO
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.perf_monitoring.create_perf_graphs as cpg
import spar_python.perf_monitoring.perf_db as perf_db

# pillow is useful for looking at graphs during development,
# but needed for unittests or product, and thus not in requirements.txt
try:
    from PIL import Image
except ImportError:
    Image = None


class PerfGraphGeneratorTest(unittest.TestCase):
    '''Unit tests for PerfGraphGenerator.py'''
    
    def _create_database(self):
        con = perf_db.create_perf_db(":memory:")
        # 1377616554 = 2013-08-27 15:15:54 (GMT)
        perf_db.insert_ram(con, "client", 1377616554.1, 10000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.2, 12000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.3, 18000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.4, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.5, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.6, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.7, 35000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.8, 33000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "client", 1377616554.9, 30000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.1, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.2, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.3, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.4, 10000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.5, 5000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.6, 5000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.7, 25000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.8, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "server", 1377616554.9, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.1, 1000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.2, 35000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.3, 25000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.4, 1000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.5, 10000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.6, 25000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.7, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.8, 40000, 0, 0, 0, 0) 
        perf_db.insert_ram(con, "thirdparty", 1377616554.9, 15000, 0, 0, 0, 0) 
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.1, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.1, 0,0,0,0,0,15.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.1, 0,0,0,0,0,20.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.1, 0,0,0,0,0,25.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.2, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.2, 0,0,0,0,0,12.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.2, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.2, 0,0,0,0,0,43.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.3, 0,0,0,0,0,23.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.3, 0,0,0,0,0,15.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.3, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.3, 0,0,0,0,0,34.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.4, 0,0,0,0,0,34.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.4, 0,0,0,0,0,33.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.4, 0,0,0,0,0,0.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.4, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.5, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.5, 0,0,0,0,0,13.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.5, 0,0,0,0,0,100.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.5, 0,0,0,0,0,88.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.6, 0,0,0,0,0,43.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.6, 0,0,0,0,0,17.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.6, 0,0,0,0,0,74.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.6, 0,0,0,0,0,56.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.7, 0,0,0,0,0,76.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.7, 0,0,0,0,0,45.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.7, 0,0,0,0,0,17.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.7, 0,0,0,0,0,77.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.8, 0,0,0,0,0,14.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.8, 0,0,0,0,0,54.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.8, 0,0,0,0,0,11.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.8, 0,0,0,0,0,96.0)
        perf_db.insert_cpu(con, "client", "cpu_0", 1377616554.9, 0,0,0,0,0,41.0)
        perf_db.insert_cpu(con, "client", "cpu_1", 1377616554.9, 0,0,0,0,0,47.0)
        perf_db.insert_cpu(con, "client", "cpu_2", 1377616554.9, 0,0,0,0,0,9.0)
        perf_db.insert_cpu(con, "client", "cpu_3", 1377616554.9, 0,0,0,0,0,0.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.1, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.1, 0,0,0,0,0,15.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.1, 0,0,0,0,0,20.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.1, 0,0,0,0,0,25.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.2, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.2, 0,0,0,0,0,12.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.2, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.2, 0,0,0,0,0,43.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.3, 0,0,0,0,0,23.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.3, 0,0,0,0,0,15.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.3, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.3, 0,0,0,0,0,34.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.4, 0,0,0,0,0,34.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.4, 0,0,0,0,0,33.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.4, 0,0,0,0,0,55.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.4, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.5, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.5, 0,0,0,0,0,13.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.5, 0,0,0,0,0,100.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.5, 0,0,0,0,0,88.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.6, 0,0,0,0,0,43.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.6, 0,0,0,0,0,17.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.6, 0,0,0,0,0,74.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.6, 0,0,0,0,0,56.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.7, 0,0,0,0,0,76.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.7, 0,0,0,0,0,45.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.7, 0,0,0,0,0,17.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.7, 0,0,0,0,0,77.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.8, 0,0,0,0,0,14.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.8, 0,0,0,0,0,54.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.8, 0,0,0,0,0,11.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.8, 0,0,0,0,0,96.0)
        perf_db.insert_cpu(con, "server", "cpu_0", 1377616554.9, 0,0,0,0,0,41.0)
        perf_db.insert_cpu(con, "server", "cpu_1", 1377616554.9, 0,0,0,0,0,47.0)
        perf_db.insert_cpu(con, "server", "cpu_2", 1377616554.9, 0,0,0,0,0,9.0)
        perf_db.insert_cpu(con, "server", "cpu_3", 1377616554.9, 0,0,0,0,0,0.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.1, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.1, 0,0,0,0,0,15.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.1, 0,0,0,0,0,20.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.1, 0,0,0,0,0,25.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.2, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.2, 0,0,0,0,0,12.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.2, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.2, 0,0,0,0,0,43.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.3, 0,0,0,0,0,23.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.3, 0,0,0,0,0,15.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.3, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.3, 0,0,0,0,0,34.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.4, 0,0,0,0,0,34.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.4, 0,0,0,0,0,33.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.4, 0,0,0,0,0,55.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.4, 0,0,0,0,0,32.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.5, 0,0,0,0,0,10.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.5, 0,0,0,0,0,13.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.5, 0,0,0,0,0,100.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.5, 0,0,0,0,0,88.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.6, 0,0,0,0,0,43.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.6, 0,0,0,0,0,17.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.6, 0,0,0,0,0,74.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.6, 0,0,0,0,0,56.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.7, 0,0,0,0,0,76.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.7, 0,0,0,0,0,45.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.7, 0,0,0,0,0,17.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.7, 0,0,0,0,0,77.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.8, 0,0,0,0,0,14.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.8, 0,0,0,0,0,54.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.8, 0,0,0,0,0,11.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.8, 0,0,0,0,0,96.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_0", 1377616554.9, 0,0,0,0,0,41.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_1", 1377616554.9, 0,0,0,0,0,47.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_2", 1377616554.9, 0,0,0,0,0,9.0)
        perf_db.insert_cpu(con, "thirdparty", "cpu_3", 1377616554.9, 0,0,0,0,0,0.0)        
        perf_db.insert_disk(con, "client", 1377616554.1, "sda", 0, 32.2, 0, 23.2, 0)
        perf_db.insert_disk(con, "client", 1377616554.1, "sdb", 0, 52.2, 0, 63.5, 0)
        perf_db.insert_disk(con, "client", 1377616554.1, "sdc", 0, 123.4, 0, 12.5, 0)
        perf_db.insert_disk(con, "client", 1377616554.2, "sda", 0, 63, 0, 21.9, 0)
        perf_db.insert_disk(con, "client", 1377616554.2, "sdb", 0, 214, 0, 52, 0)
        perf_db.insert_disk(con, "client", 1377616554.2, "sdc", 0, 63, 0, 98.2, 0)        
        perf_db.insert_disk(con, "client", 1377616554.3, "sda", 0, 47, 0, 36.2, 0)
        perf_db.insert_disk(con, "client", 1377616554.3, "sdb", 0, 84.4, 0, 41.4, 0)
        perf_db.insert_disk(con, "client", 1377616554.3, "sdc", 0, 63.9, 0, 96.3, 0)
        perf_db.insert_disk(con, "client", 1377616554.4, "sda", 0, 85.2, 0, 10.0, 0)
        perf_db.insert_disk(con, "client", 1377616554.4, "sdb", 0, 71.4, 0, 18.0, 0)
        perf_db.insert_disk(con, "client", 1377616554.4, "sdc", 0, 5.2, 0, 36.5, 0)
        perf_db.insert_disk(con, "client", 1377616554.5, "sda", 0, 104.1, 0, 47.8, 0)
        perf_db.insert_disk(con, "client", 1377616554.5, "sdb", 0, 3, 0, 0.0, 0)
        perf_db.insert_disk(con, "client", 1377616554.5, "sdc", 0, 150.7, 0, 0.0, 0)
        perf_db.insert_disk(con, "client", 1377616554.6, "sda", 0, 63.7, 0, 01.5, 0)
        perf_db.insert_disk(con, "client", 1377616554.6, "sdb", 0, 57.4, 0, 84.6, 0)
        perf_db.insert_disk(con, "client", 1377616554.6, "sdc", 0, 14.8, 0, 98.4, 0)
        perf_db.insert_disk(con, "client", 1377616554.7, "sda", 0, 98.6, 0, 56.3, 0)
        perf_db.insert_disk(con, "client", 1377616554.7, "sdb", 0, 74.5, 0, 47.1, 0)
        perf_db.insert_disk(con, "client", 1377616554.7, "sdc", 0, 48.5, 0, 96.1, 0)
        perf_db.insert_disk(con, "client", 1377616554.8, "sda", 0, 25.6, 0, 87.4, 0)
        perf_db.insert_disk(con, "client", 1377616554.8, "sdb", 0, 49.8, 0, 24.8, 0)
        perf_db.insert_disk(con, "client", 1377616554.8, "sdc", 0, 57.9, 0, 63.6, 0)
        perf_db.insert_disk(con, "client", 1377616554.9, "sda", 0, 32.6, 0, 14.5, 0)
        perf_db.insert_disk(con, "client", 1377616554.9, "sdb", 0, 19.4, 0, 74.2, 0)
        perf_db.insert_disk(con, "client", 1377616554.9, "sdc", 0, 1.3, 0, 85, 0)
        perf_db.insert_disk(con, "server", 1377616554.1, "sda", 0, 32.2, 0, 23.2, 0)
        perf_db.insert_disk(con, "server", 1377616554.1, "sdb", 0, 52.2, 0, 63.5, 0)
        perf_db.insert_disk(con, "server", 1377616554.1, "sdc", 0, 123.4, 0, 12.5, 0)
        perf_db.insert_disk(con, "server", 1377616554.2, "sda", 0, 63, 0, 21.9, 0)
        perf_db.insert_disk(con, "server", 1377616554.2, "sdb", 0, 214, 0, 52, 0)
        perf_db.insert_disk(con, "server", 1377616554.2, "sdc", 0, 63, 0, 98.2, 0)        
        perf_db.insert_disk(con, "server", 1377616554.3, "sda", 0, 47, 0, 36.2, 0)
        perf_db.insert_disk(con, "server", 1377616554.3, "sdb", 0, 84.4, 0, 41.4, 0)
        perf_db.insert_disk(con, "server", 1377616554.3, "sdc", 0, 63.9, 0, 96.3, 0)
        perf_db.insert_disk(con, "server", 1377616554.4, "sda", 0, 85.2, 0, 10.0, 0)
        perf_db.insert_disk(con, "server", 1377616554.4, "sdb", 0, 71.4, 0, 18.0, 0)
        perf_db.insert_disk(con, "server", 1377616554.4, "sdc", 0, 5.2, 0, 36.5, 0)
        perf_db.insert_disk(con, "server", 1377616554.5, "sda", 0, 104.1, 0, 47.8, 0)
        perf_db.insert_disk(con, "server", 1377616554.5, "sdb", 0, 3, 0, 0.0, 0)
        perf_db.insert_disk(con, "server", 1377616554.5, "sdc", 0, 150.7, 0, 0.0, 0)
        perf_db.insert_disk(con, "server", 1377616554.6, "sda", 0, 63.7, 0, 1.5, 0)
        perf_db.insert_disk(con, "server", 1377616554.6, "sdb", 0, 57.4, 0, 84.6, 0)
        perf_db.insert_disk(con, "server", 1377616554.6, "sdc", 0, 14.8, 0, 98.4, 0)
        perf_db.insert_disk(con, "server", 1377616554.7, "sda", 0, 98.6, 0, 56.3, 0)
        perf_db.insert_disk(con, "server", 1377616554.7, "sdb", 0, 74.5, 0, 47.1, 0)
        perf_db.insert_disk(con, "server", 1377616554.7, "sdc", 0, 48.5, 0, 96.1, 0)
        perf_db.insert_disk(con, "server", 1377616554.8, "sda", 0, 25.6, 0, 87.4, 0)
        perf_db.insert_disk(con, "server", 1377616554.8, "sdb", 0, 49.8, 0, 24.8, 0)
        perf_db.insert_disk(con, "server", 1377616554.8, "sdc", 0, 57.9, 0, 63.6, 0)
        perf_db.insert_disk(con, "server", 1377616554.9, "sda", 0, 32.6, 0, 14.5, 0)
        perf_db.insert_disk(con, "server", 1377616554.9, "sdb", 0, 19.4, 0, 74.2, 0)
        perf_db.insert_disk(con, "server", 1377616554.9, "sdc", 0, 1.3, 0, 85, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.1, "sda", 0, 32.2, 0, 23.2, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.1, "sdb", 0, 52.2, 0, 63.5, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.1, "sdc", 0, 123.4, 0, 12.5, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.2, "sda", 0, 63, 0, 21.9, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.2, "sdb", 0, 214, 0, 52, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.2, "sdc", 0, 63, 0, 98.2, 0)        
        perf_db.insert_disk(con, "thirdparty", 1377616554.3, "sda", 0, 47, 0, 36.2, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.3, "sdb", 0, 84.4, 0, 41.4, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.3, "sdc", 0, 63.9, 0, 96.3, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.4, "sda", 0, 85.2, 0, 10.0, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.4, "sdb", 0, 71.4, 0, 18.0, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.4, "sdc", 0, 5.2, 0, 36.5, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.5, "sda", 0, 104.1, 0, 47.8, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.5, "sdb", 0, 3, 0, 0.0, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.5, "sdc", 0, 150.7, 0, 0.0, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.6, "sda", 0, 63.7, 0, 1.5, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.6, "sdb", 0, 57.4, 0, 84.6, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.6, "sdc", 0, 14.8, 0, 98.4, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.7, "sda", 0, 98.6, 0, 56.3, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.7, "sdb", 0, 74.5, 0, 47.1, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.7, "sdc", 0, 48.5, 0, 96.1, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.8, "sda", 0, 25.6, 0, 87.4, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.8, "sdb", 0, 49.8, 0, 24.8, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.8, "sdc", 0, 57.9, 0, 63.6, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.9, "sda", 0, 32.6, 0, 14.5, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.9, "sdb", 0, 19.4, 0, 74.2, 0)
        perf_db.insert_disk(con, "thirdparty", 1377616554.9, "sdc", 0, 1.3, 0, 85, 0)
        perf_db.insert_network(con, 1377616554.1, "client_to_server", 1000,  "TCP/IP")
        perf_db.insert_network(con, 1377616554.2, "client_to_server", 500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.30, "client_to_server", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.34, "client_to_server", 500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.36, "client_to_server", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.41, "client_to_server", 1400, "TCP/IP")
        perf_db.insert_network(con, 1377616554.43, "client_to_server", 300, "TCP/IP")
        perf_db.insert_network(con, 1377616554.48, "client_to_server", 600, "TCP/IP")
        perf_db.insert_network(con, 1377616554.49, "client_to_server", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.51, "client_to_server", 200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.53, "client_to_server", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.70, "client_to_server", 1000, "TCP/IP")
        perf_db.insert_network(con, 1377616554.80, "client_to_server", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.85, "client_to_server", 1100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.87, "client_to_server", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.90, "client_to_server", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.1, "server_to_client", 1000, "TCP/IP")
        perf_db.insert_network(con, 1377616554.2, "server_to_client", 500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.30, "server_to_client", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.34, "server_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.36, "server_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.39, "server_to_client", 1400, "TCP/IP")
        perf_db.insert_network(con, 1377616554.43, "server_to_client", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.48, "server_to_client", 200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.53, "server_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.57, "server_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.63, "server_to_client", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.70, "server_to_client", 800, "TCP/IP")
        perf_db.insert_network(con, 1377616554.80, "server_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.85, "server_to_client", 1100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.87, "server_to_client", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.90, "server_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.1, "client_to_thirdparty", 1000, "TCP/IP")
        perf_db.insert_network(con, 1377616554.2, "client_to_thirdparty", 500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.30, "client_to_thirdparty", 800, "TCP/IP")
        perf_db.insert_network(con, 1377616554.31, "client_to_thirdparty", 300, "TCP/IP")
        perf_db.insert_network(con, 1377616554.32, "client_to_thirdparty", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.35, "client_to_thirdparty", 400, "TCP/IP")
        perf_db.insert_network(con, 1377616554.39, "client_to_thirdparty", 1300, "TCP/IP")
        perf_db.insert_network(con, 1377616554.41, "client_to_thirdparty", 900, "TCP/IP")
        perf_db.insert_network(con, 1377616554.49, "client_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.61, "client_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.68, "client_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.70, "client_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.80, "client_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.85, "client_to_thirdparty", 1100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.87, "client_to_thirdparty", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.90, "client_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.1, "thirdparty_to_client", 1000, "TCP/IP")
        perf_db.insert_network(con, 1377616554.2, "thirdparty_to_client", 500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.28, "thirdparty_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.44, "thirdparty_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.46, "thirdparty_to_client", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.48, "thirdparty_to_client", 1400, "TCP/IP")
        perf_db.insert_network(con, 1377616554.485, "thirdparty_to_client", 1300, "TCP/IP")
        perf_db.insert_network(con, 1377616554.49, "thirdparty_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.493, "thirdparty_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.51, "thirdparty_to_client", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.53, "thirdparty_to_client", 1300, "TCP/IP")
        perf_db.insert_network(con, 1377616554.70, "thirdparty_to_client", 600, "TCP/IP")
        perf_db.insert_network(con, 1377616554.80, "thirdparty_to_client", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.85, "thirdparty_to_client", 1100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.87, "thirdparty_to_client", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.90, "thirdparty_to_client", 1500, "TCP/IP")        
        perf_db.insert_network(con, 1377616554.1, "server_to_thirdparty", 1000, "TCP/IP")
        perf_db.insert_network(con, 1377616554.2, "server_to_thirdparty", 500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.30, "server_to_thirdparty", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.34, "server_to_thirdparty", 200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.36, "server_to_thirdparty", 150, "TCP/IP")
        perf_db.insert_network(con, 1377616554.363, "server_to_thirdparty", 50, "TCP/IP")
        perf_db.insert_network(con, 1377616554.3643, "server_to_thirdparty", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.3648, "server_to_thirdparty", 150, "TCP/IP")
        perf_db.insert_network(con, 1377616554.3649, "server_to_thirdparty", 50, "TCP/IP")
        perf_db.insert_network(con, 1377616554.51, "server_to_thirdparty", 400, "TCP/IP")
        perf_db.insert_network(con, 1377616554.53, "server_to_thirdparty", 800, "TCP/IP")
        perf_db.insert_network(con, 1377616554.70, "server_to_thirdparty", 1100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.80, "server_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.85, "server_to_thirdparty", 1100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.87, "server_to_thirdparty", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.90, "server_to_thirdparty", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.1, "thirdparty_to_server", 1000, "TCP/IP")
        perf_db.insert_network(con, 1377616554.2, "thirdparty_to_server", 500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.30, "thirdparty_to_server", 700, "TCP/IP")
        perf_db.insert_network(con, 1377616554.34, "thirdparty_to_server", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.36, "thirdparty_to_server", 100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.41, "thirdparty_to_server", 1400, "TCP/IP")
        perf_db.insert_network(con, 1377616554.43, "thirdparty_to_server", 800, "TCP/IP")
        perf_db.insert_network(con, 1377616554.548, "thirdparty_to_server", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.549, "thirdparty_to_server", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.551, "thirdparty_to_server", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.63, "thirdparty_to_server", 700, "TCP/IP")
        perf_db.insert_network(con, 1377616554.70, "thirdparty_to_server", 1000, "TCP/IP")
        perf_db.insert_network(con, 1377616554.80, "thirdparty_to_server", 1500, "TCP/IP")
        perf_db.insert_network(con, 1377616554.85, "thirdparty_to_server", 1100, "TCP/IP")
        perf_db.insert_network(con, 1377616554.87, "thirdparty_to_server", 1200, "TCP/IP")
        perf_db.insert_network(con, 1377616554.90, "thirdparty_to_server", 1500, "TCP/IP")
        
        return con

    
    def test_ram_graph(self):
        '''Unit test for create_perf_graphs.produce_ram_graph'''
        pgg = cpg.PerfGraphGenerator(self._create_database())
        
        graph_as_str = pgg.produce_ram_graph("2013-08-27 15:15:54.3", "2013-08-27 15:15:54.7");

        self.assertNotEqual(graph_as_str, "")
        
        # un-comment the below for a visual spot-check
        # 'pip install pillow' may be required
        #if (Image):
        #    Image.open(StringIO.StringIO(graph_as_str)).show();
        
        
    def test_cpu_graph(self):
        '''Unit test for create_perf_graphs.produce_cpu_graph'''
        pgg = cpg.PerfGraphGenerator(self._create_database())
        
        graph_as_str = pgg.produce_cpu_graph("2013-08-27 15:15:54.3", 
                                             "2013-08-27 15:15:54.7", 
                                             ignored_cpus = {
                                                "client" : ["cpu_0", "cpu_1"],
                                                "server" : ["cpu_0", "cpu_2"],
                                                "thirdparty" : ["cpu_3"]})

        self.assertNotEqual(graph_as_str, "")
        
        # un-comment the below for a visual spot-check
        # 'pip install pillow' may be required
        #if (Image):
        #    Image.open(StringIO.StringIO(graph_as_str)).show();
        
    def test_disk_graph(self):
        '''Unit test for create_perf_graphs.produce_disk_graph'''
        pgg = cpg.PerfGraphGenerator(self._create_database())
        
        graph_as_str = pgg.produce_disk_graph("2013-08-27 15:15:54.3", 
                                             "2013-08-27 15:15:54.7", 
                                             ignored_disks = {
                                                "client" : ["sda", "sdb"],
                                                "server" : ["sdc"]})

        self.assertNotEqual(graph_as_str, "")
        
        # un-comment the below for a visual spot-check
        # 'pip install pillow' may be required
        #if (Image):
        #    Image.open(StringIO.StringIO(graph_as_str)).show();
        
    def test_network_graph(self):
        '''Unit test for create_perf_graphs.produce_network_graph'''
        pgg = cpg.PerfGraphGenerator(self._create_database())
        
        graph_as_str = pgg.produce_network_graph("2013-08-27 15:15:54.3", 
                                             "2013-08-27 15:15:54.7", 
                                             numbins=4)

        self.assertNotEqual(graph_as_str, "")
        
        # un-comment the below for a visual spot-check
        # 'pip install pillow' may be required
        #if (Image):
        #    Image.open(StringIO.StringIO(graph_as_str)).show();

        
