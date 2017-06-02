#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This reads through a pcap file and extracts 
#                      metadata regarding packets of interest and 
#                      ignores packets of non-interest.  Specifically
#                      it extracts:
#                      sender and receiver (CLIENT_TO_TP / TP_TO_SERVER / etc)
#                      packet timestamp
#                      payload size (where "payload" is 
#                      everything after the TCP/UDP header
# *****************************************************************

from scapy.utils import rdpcap
from scapy.layers.inet import IP, UDP, TCP
import csv
import argparse
import socket
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.network_log_parser import NetworkLogReader
from spar_python.perf_monitoring.network_log_parser import NetworkLogEntry


def pcap_to_csv(input_filename, output_handle, mappings):
    '''This funciton takes a pcap (by filename), and for each packet between
    any two of (client, server, thirdparty) and extracts:
    timestamp
    sender/receiver
    size of payload (where "payload" is defined as everything after the TCP/UDP header
    protocol ("IP/TCP", etc).
    
    input_filename: filename of the input file ("foo.pcap")
    output_handle: handle to direct output to (open("foo.csv"))
    mappings: a dict mapping of ip address to role, where role is one of:
        "client", "server", or "thirdparty".  For example:
        { "10.10.5.7" : "client1", "192.168.2.7" : "client2", 
        "10.15.20.30": "server", "10.40.50.70" : "thirdparty" }
    returns: nothing
    '''

    fields = ["time", "direction", "payloadlength", "protocol"]
    
    # rdpcap returns pcap, essentially an array of packets
    # Packet fields can be read via packet[layer].field
    # layers are in scapy.layers
    # packet.show() displays the contents of each packet
    pcap = rdpcap(input_filename)
    csvwriter = csv.DictWriter(output_handle, fields, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writeheader()

    for packet in pcap:        
        row = get_packet_info(packet, mappings)
        if row != None:
            csvwriter.writerow(row)


def pcap_to_log(input_filename, mappings):
    '''This function returns a NetworkLogReader containing
    all the relevant information, instead of writing the output
    to a csv (like pcap_to_csv)'''
    pcap = rdpcap(input_filename)
    log = NetworkLogReader()

    for packet in pcap:
        log_entry = get_packet_info(packet, mappings)       
        if log_entry != None:   
            log.entries.append(NetworkLogEntry(log_entry))
    
    return log

def get_packet_info(packet, mappings):
    '''Takes in a packet and returns a dictionary containing
    packet information (time, direction, lengtgh, protocol)
    
    Inputs: 
    packet (a network packet via scapy)
    mappings: a dict that maps ip address to hosts/roles ("client")
    
    Returns: a dict containing information about the packet, or
    None if either it wasn't an IP packet, or the packet was not
    between hosts of interest'''
    
    # If it's not IP, ignore
    if IP not in packet:
        return None   
    source_ip = packet[IP].src
    dest_ip = packet[IP].dst

    # ensure packet is from/to an IP of interest
    if (source_ip not in mappings):
        return None
    if (dest_ip not in mappings):
        return None
    
    packet_info = {}        
        
    packet_info["time"] = "%0.6f" % packet.time
    packet_info["direction"] = \
        get_packet_direction(source_ip, dest_ip, mappings)
        
    if (TCP in packet):
        # For TCP, take the IP packet length (which includes IP 
        # and TCP headers) then substract off the length of the
        # TCP and IP headers
        packet_info["payloadlength"] = packet[IP].len - \
            packet[IP].ihl*4 - packet[TCP].dataofs * 4
        packet_info["protocol"] = "IP/TCP"
    elif (UDP in packet):
        # For UDP, take the UDP packet length (which include the UDP 
        # header) then subtract the length of the UDP header (always 8)
        packet_info["payloadlength"] = packet[UDP].len - 8 
        packet_info["protocol"] = "IP/UDP"
    else:
        # for anything other than TCP or UDP, take the IP packet length 
        # (includes IP header) and subtract the IP header length
        # if a performer is actively using something other than TCP 
        # or UDP a separate case statement should be written 
        packet_info["payloadlength"] = packet[IP].len - packet[IP].ihl*4
        packet_info["protocol"] = "IP/UNKNOWN"
        
    return packet_info

    

def get_packet_direction(source_ip, dest_ip, mappings):
    '''This function determines the direction of a packet as a string.
    Given the source and destination ip addresses of the packet, and the 
    ip addresses of the systems of interest, this detects whether the packet 
    was sent from the server to the client, or the third party to the client, 
    etc.
    
    source_ip: the source IP address of the packet ("10.10.5.7")
    dest_ip: the destination IP address of the packet ("192.168.2.7")
    mappings: a dict mapping of ip address to role, where role is one of:
        "client", "server", or "thirdparty".  For example:
        { "10.10.5.7" : "client1", "192.168.2.7" : "client2", 
        "10.15.20.30": "server", "10.40.50.70" : "thirdparty" }
    returns: a string representing the packet direction 
        ("client2_to_thirdparty")''' 
    
    if (source_ip in mappings):
        direction = mappings[source_ip] + "_to_"
    else:
        direction = "other_to_" # shouldn't happen
    if (dest_ip in mappings):
        direction += mappings[dest_ip]
    else:
        direction += "other" # shouldn't happen
    return direction

def get_mappings_from_handle(handle):
    '''This function creates a dictionary of mappings of ip addresses to
    names from a config file.  Names should not have spaces or special
    characters.
    The format of the config file is lines of ip_address = name, such as:
    
    # comment
    192.168.1.2 = client
    10.10.5.6 = server
    # another comment
    10.10.8.20 = thirdparty
    
    Input: handle to config file (open("mappings.txt"))
    
    Returns: a dictionary of mappings
    '''
    mappings = {}
    for line in handle.readlines():
        if line.strip()[0] == '#':
            continue
        if '=' not in line:
            continue
        parts = line.split('=', 1)
        # ensure the first part a well-formed IP address
        try:
            socket.inet_aton(parts[0].strip())
        except Exception:
            continue
        mappings[parts[0].strip()] = parts[1].strip()
    
    return mappings
    
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
                                     "Process a pcap file and output a csv")
    parser.add_argument("-i", "--infile",  default=None, type=str, 
                        required=True, help="pcap file to read")
    parser.add_argument("-o", "--outfile",  default=None, type=str, 
                        required=True, help="csv file to write")
    parser.add_argument("-c", "--config", default=None, type=str, 
                        required=True, 
                        help="file containing mapping from ip's to names")    
    options = vars(parser.parse_args())
    
    pcap_to_csv(options['infile'], open(options['outfile'], "w"), 
                get_mappings_from_handle(open(options['config'], "r")))



