#!/bin/bash

# Launches tcpdump and saves its stdout to the specified file. Tailored for
# usage on the SPAR testbed.
# 
# Arguments:
# $1 - interface number to analyze (use 'tcpdump -D' to see the available
# interfaces)
# $2 - host IP of interest (where you want to see traffic to/from)
# $3 - output file
#
# TODO: Make this a proper script with help options, etc
#
# Note the following, which outlines how the tcpdump filters are set up. These
# are generally sources of traffic that are inherent to the network, or are not
# interesting for our purposes.
# ARP - address resolution protocol, excluded with 'arp'
# STP - spanning tree protocol, excluded with 'stp'
# CDPv2 - Cisco discovery protocol, excluded with 'ether[20:2] == 0x2000'
# LLDP - link layer discovery protocol, excluded with 'ether proto 0x88cc'
# PTPd UDP traffic - excluded with 'host $ptp_server'
# SSH TCP traffic - excluded with 'tcp and port 22'

ptp_server=224.0.1.129

# TODO allow more IP addresses to be blacklisted

sudo tcpdump -s 0 -i $1 ip and not arp and not stp and not ether proto 0x88cc and not ether[20:2] == 0x2000 and not \(tcp and port 22\) and not host $ptp_server and host $2 -l -w $3
