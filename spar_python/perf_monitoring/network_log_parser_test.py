#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      network_log_parser.py 
# *****************************************************************

import unittest
import StringIO
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.perf_monitoring.network_log_parser as nlp
import spar_python.perf_monitoring.perf_db as perfdb
from spar_python.perf_monitoring.time_utils import epoch_to_sql as epoch_to_sql


TEST_NETWORK_LOG_FILE_1 = '''time,direction,payloadlength,protocol
1373902408.279699,client_to_server,32,IP/UDP
1373902408.283685,server_to_client,48,IP/UDP
1373902408.284399,client_to_thirdparty,0,IP/TCP
1373902408.286417,thirdparty_to_client,0,IP/TCP
1373902408.286550,client_to_thirdparty,0,IP/TCP
1373902408.287903,client_to_thirdparty,225,IP/TCP'''


TEST_NETWORK_LOG_FILE_2 = '''time,direction,payloadlength,protocol
1373902408.288277,thirdparty_to_client,0,IP/TCP
1373902408.290489,thirdparty_to_client,1460,IP/TCP
1373902408.290514,thirdparty_to_client,1460,IP/TCP
1373902408.291185,client_to_thirdparty,0,IP/TCP
1373902408.291865,client_to_thirdparty,0,IP/TCP
1373902408.292883,thirdparty_to_client,1460,IP/TCP
1373902408.292903,thirdparty_to_client,657,IP/TCP
1373902408.293020,client_to_thirdparty,0,IP/TCP
1373902408.293174,client_to_thirdparty,0,IP/TCP
1373902408.341200,client_to_thirdparty,326,IP/TCP'''

TEST_NETWORK_LOG_FILE_3 = '''time,direction,payloadlength,protocol
1373902408.341527,thirdparty_to_client,0,IP/TCP
1373902408.348738,thirdparty_to_client,59,IP/TCP
1373902408.348851,client_to_thirdparty,0,IP/TCP
1373902411.586889,client_to_thirdparty,90,IP/TCP
1373902411.587769,thirdparty_to_client,0,IP/TCP
1373902411.747023,client_to_thirdparty,74,IP/TCP
1373902411.747551,thirdparty_to_client,0,IP/TCP
1373902411.754033,thirdparty_to_client,607,IP/TCP
1373902411.754534,client_to_thirdparty,37,IP/TCP
1373902411.754740,client_to_thirdparty,0,IP/TCP
1373902411.754890,thirdparty_to_client,0,IP/TCP
1373902411.754983,thirdparty_to_client,0,IP/TCP'''


class NetworkLogParserTest(unittest.TestCase):
    '''Unit tests for network_log_parser.py'''
        
    def test_network_log_entry_init(self):
        '''Unit test for NetworkLogEntry.__init__
        
        Create a few objects, verify the contents'''
        times = [1373902408.283685, 1373902408.284399, 1373902408.286417]
        directions = ["server_to_client", "client_to_thirdparty", "thirdparty_to_client"]
        payloadlengths = [48, 1460, 0]
        protocols = ["IP/UDP", "IP/TCP", "IP/TCP"]
        
        for i in range(len(times)):
            row = { "time" : times[i], "direction" : directions[i],
                    "payloadlength" : payloadlengths[i], "protocol" : protocols[i]}
            entry = nlp.NetworkLogEntry(row)
            self.assertEqual(entry.time, times[i])
            self.assertEqual(entry.direction, directions[i])
            self.assertEqual(entry.payloadlength, payloadlengths[i])
            self.assertEqual(entry.protocol, protocols[i])
            
    def test_add_handle(self):
        '''Unit test for NetworkLogReader.add_handle
        
        Add multiple files, ensure contents from each file
        are contained in the result'''
        reader = nlp.NetworkLogReader()
        reader.add_handle(StringIO.StringIO(TEST_NETWORK_LOG_FILE_1))
        reader.add_handle(StringIO.StringIO(TEST_NETWORK_LOG_FILE_2))
        reader.add_handle(StringIO.StringIO(TEST_NETWORK_LOG_FILE_3))
        
        expected_entries = [{
            "time" : 1373902408.284399,
            "direction" : "client_to_thirdparty",
            "payloadlength" : 0,
            "protocol" : "IP/TCP"},
            {"time" : 1373902408.292883,
            "direction" : "thirdparty_to_client",
            "payloadlength" : 1460,
            "protocol" : "IP/TCP"},                    
            {"time" : 1373902411.754983,
            "direction" : "thirdparty_to_client",
            "payloadlength" : 0,
            "protocol" : "IP/TCP"}
            ]
        
        for entry in expected_entries:
            self.assertIn(nlp.NetworkLogEntry(entry), reader.entries)
            

    def test_write_to_database(self):
        '''Unit test for write_to_database
        
        Generate some records, write them to database
        query database, ensure records in db'''
        
        reader = nlp.NetworkLogReader(StringIO.StringIO(TEST_NETWORK_LOG_FILE_1))
        reader.add_handle(StringIO.StringIO(TEST_NETWORK_LOG_FILE_2))
        reader.add_handle(StringIO.StringIO(TEST_NETWORK_LOG_FILE_3))
        
        con = perfdb.create_perf_db(":memory:")
        reader.write_to_database(con)
                
        expected_entries = [{
            "time" : 1373902408.284399,
            "direction" : "client_to_thirdparty",
            "payloadlength" : 0,
            "protocol" : "IP/TCP"},
            {"time" : 1373902408.292883,
            "direction" : "thirdparty_to_client",
            "payloadlength" : 1460,
            "protocol" : "IP/TCP"},                    
            {"time" : 1373902411.754983,
            "direction" : "thirdparty_to_client",
            "payloadlength" : 0,
            "protocol" : "IP/TCP"}
            ]

        expected_rows = []
        for entry in expected_entries:
            expected_rows.append((epoch_to_sql(entry["time"]), entry["direction"], 
                                  entry["payloadlength"], entry["direction"])) 
        
        query = "SELECT time, direction, payloadlength, direction FROM Network;"
        cursor = con.cursor()
        cursor.execute(query)
        actual_rows = cursor.fetchall()
        
        for entry in expected_rows:
            self.assertIn(entry, actual_rows)
            
        


