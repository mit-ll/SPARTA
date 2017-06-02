#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        Unit tests for pcap_parser 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  15 Jul 2012   mjr           Original Version
# *****************************************************************

import unittest
import csv
from spar_python.perf_monitoring.pcap_parser import get_packet_direction, pcap_to_csv, get_mappings_from_handle
import os
import StringIO

THIS_DIRECTORY = os.path.dirname(__file__)

class PcapParserTest(unittest.TestCase):
    '''Unit tests for pcap_parser.py'''
        
    # IP addresses for use by test_packet_direction
    client = "1.1.1.1"
    server = "1.1.1.2"
    thirdparty = "1.1.1.3"
    other_ip = "1.1.1.4"
    direction_mappings = { client : "client",
                server : "server",
                thirdparty : "thirdparty"
    }
    config_mappings = {
        "172.16.0.135" : "client", 
        "172.16.0.2" : "server", 
        "172.25.8.10" : "thirdparty"
    }
    
    
    # expected output of parsing test.pcap    
    fieldnames = ["time", "direction", "payloadlength", "protocol"]
    rows = [
        {"time":"1373902408.279699","direction":"client_to_server","payloadlength":"32","protocol":"IP/UDP"},
        {"time":"1373902408.283685","direction":"server_to_client","payloadlength":"48","protocol":"IP/UDP"},
        {"time":"1373902408.284399","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"}, 
        {"time":"1373902408.286417","direction":"thirdparty_to_client","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.286550","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.287903","direction":"client_to_thirdparty","payloadlength":"225","protocol":"IP/TCP"}, 
        {"time":"1373902408.288277","direction":"thirdparty_to_client","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.290489","direction":"thirdparty_to_client","payloadlength":"1460","protocol":"IP/TCP"}, 
        {"time":"1373902408.290514","direction":"thirdparty_to_client","payloadlength":"1460","protocol":"IP/TCP"},
        {"time":"1373902408.291185","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.291865","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.292883","direction":"thirdparty_to_client","payloadlength":"1460","protocol":"IP/TCP"}, 
        {"time":"1373902408.292903","direction":"thirdparty_to_client","payloadlength":"657","protocol":"IP/TCP"},
        {"time":"1373902408.293020","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.293174","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.341200","direction":"client_to_thirdparty","payloadlength":"326","protocol":"IP/TCP"}, 
        {"time":"1373902408.341527","direction":"thirdparty_to_client","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902408.348738","direction":"thirdparty_to_client","payloadlength":"59","protocol":"IP/TCP"}, 
        {"time":"1373902408.348851","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902411.586889","direction":"client_to_thirdparty","payloadlength":"90","protocol":"IP/TCP"}, 
        {"time":"1373902411.587769","direction":"thirdparty_to_client","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902411.747023","direction":"client_to_thirdparty","payloadlength":"74","protocol":"IP/TCP"}, 
        {"time":"1373902411.747551","direction":"thirdparty_to_client","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902411.754033","direction":"thirdparty_to_client","payloadlength":"607","protocol":"IP/TCP"}, 
        {"time":"1373902411.754534","direction":"client_to_thirdparty","payloadlength":"37","protocol":"IP/TCP"},
        {"time":"1373902411.754740","direction":"client_to_thirdparty","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902411.754890","direction":"thirdparty_to_client","payloadlength":"0","protocol":"IP/TCP"},
        {"time":"1373902411.754983","direction":"thirdparty_to_client","payloadlength":"0","protocol":"IP/TCP"} ]

    def test_packet_direction(self):
        '''tests get_packet_direction'''
        # shorter names for readability
        client = PcapParserTest.client
        server = PcapParserTest.server
        thirdparty = PcapParserTest.thirdparty
        maps = PcapParserTest.direction_mappings 
        other = PcapParserTest.other_ip
        
        self.assertEqual(get_packet_direction(client, client, maps), "client_to_client")
        self.assertEqual(get_packet_direction(client, server, maps), "client_to_server")
        self.assertEqual(get_packet_direction(client, thirdparty, maps), "client_to_thirdparty")
        self.assertEqual(get_packet_direction(server, client, maps), "server_to_client")
        self.assertEqual(get_packet_direction(server, server, maps), "server_to_server")
        self.assertEqual(get_packet_direction(server, thirdparty, maps), "server_to_thirdparty")
        self.assertEqual(get_packet_direction(thirdparty, client, maps), "thirdparty_to_client")
        self.assertEqual(get_packet_direction(thirdparty, server, maps), "thirdparty_to_server")
        self.assertEqual(get_packet_direction(thirdparty, thirdparty, maps), "thirdparty_to_thirdparty")
        self.assertEqual(get_packet_direction(client, other, maps), "client_to_other")
        self.assertEqual(get_packet_direction(server, other, maps), "server_to_other")
        self.assertEqual(get_packet_direction(thirdparty, other, maps), "thirdparty_to_other")
        self.assertEqual(get_packet_direction(other, client, maps), "other_to_client")
        self.assertEqual(get_packet_direction(other, server, maps), "other_to_server")
        self.assertEqual(get_packet_direction(other, thirdparty, maps), "other_to_thirdparty")
        self.assertEqual(get_packet_direction(other, other, maps), "other_to_other")
    def test_pcap_to_csv(self):
        '''tests pcap_to_csv.  Relies on test.pcap in this directory'''
        filename = os.path.join(THIS_DIRECTORY, "test.pcap")
        csvdata = StringIO.StringIO()
        pcap_to_csv(filename, csvdata, 
                  {"172.16.0.135" : "client",
                    "172.16.0.2" :  "server", 
                    "172.25.8.10" : "thirdparty"} )
        csvdata.seek(0)
        csvfile = csv.DictReader(csvdata)
        self.assertEqual(csvfile.fieldnames, PcapParserTest.fieldnames)
        for expected in PcapParserTest.rows:
            self.assertEqual(csvfile.next(), expected)
    def test_mappings_from_handle(self):
        '''tests get_mappings_from_handle.'''
        configdata = StringIO.StringIO()
        configdata.write("#testcomment\n")
        configdata.write("172.16.0.135 = client\n")
        configdata.write("172.16.0.2 = server\n")
        configdata.write("172.25.8.10 = thirdparty\n")
        configdata.seek(0)
        actual_mappings = get_mappings_from_handle(configdata)
        self.assertEqual(actual_mappings, PcapParserTest.config_mappings)
   
if (__name__ == "__main__"):
    unittest.main()     
        
