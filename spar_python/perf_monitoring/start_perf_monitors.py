#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        Starts performance monitors.  Pairs with 
#                      stop_perf_monitors
# *****************************************************************

'''Starts the performance monitoring tools.  Must be run as root
(a requirement to start tcpdump).  Writes pids to stdout (to be
redirected to the desired file)'''

import subprocess
import os
import sys
import time
import argparse

def build_commands(output_dir, interval, network_interface, ip_blacklist):
    '''Builds the system commands/arguments to be run,
    returned as an array of arguments for subprocess.Popen'''
    
    current_time = str(time.time())
    
    '''An explanation of the cpu arguments:
    -sC: subsys=cpu, detailed form
    -i <interval> how often to poll for status
    --filename <filename> output filename
    -P plot mode (roughly csv mode)
    -om2z: options=
      m: report milliseconds in output
      2: 2 decimal places in output
    --sep ,: use comma as delimeter
    '''
    cpu_command = ['collectl', '-sC', '-i', str(interval), '--filename', 
                   os.path.join(output_dir, 'cpu_log_' + current_time), 
                   '-P', '-om2', '--sep', ',']
    '''An explanation of the disk arguments:
    -sD: subsys=Disk, detailed
    -i <interval>: how often to poll for status
    --filename <filename>: filename to write to
    -P plot mode (roughly csv mode)
    -om2z: options=
        m: report milliseconds in output
        2: 2 decimal places in output
    --sep ,: use comma as delimeter
    '''
    disk_command = ['collectl', '-sD', '-i', str(interval), '--filename',
                    os.path.join(output_dir, 'disk_log_' + current_time), 
                    '-P', '-om2', '--sep', ',']

    '''An explanation of the arguments:
    -sm: subsys=memory
    -i <interval>: how often to poll
    --filename <filename>: filename to write to
    -P plot mode (roughly csv mode)
    -omz: options=
        m: report milliseconds in output
    --sep ,: use comma as delimeter
    '''
    ram_command = ['collectl', '-sm', '-i', str(interval), '--filename',
                   os.path.join(output_dir, 'ram_log_' + current_time), 
                   '-P', 'om', '--sep', ',']
    #ptp_server = '224.0.1.129'
    if (len(ip_blacklist) == 0 or len(ip_blacklist[0]) == 0):
        ip_blacklist_str = ''
    else:
        #and not 1.1.1.1 and not 2.2.2.2 ...
        ip_blacklist_str = 'and not host '+' and not host '.join(ip_blacklist)
    
    network_command = ['tcpdump', '-s', '0', '-i', network_interface, 
                       'ip and not arp and not stp and not ether proto 0x88cc'
                       ' and not ether[20:2] == 0x2000 and not (tcp and '
                       'port 22) ' + ip_blacklist_str, '-l', '-w',
                       os.path.join(output_dir, 
                                    'network_' + current_time + '.pcap')]
    
    return [cpu_command, disk_command, ram_command, network_command]


def is_root_user():
    '''Returns True if user is root'''
    return (os.geteuid() == 0)


def start_monitors(commands):
    '''Starts monitors, returns an array of pids corresponding
     to the monitoring processes'''
    pids = []
    for command in commands:
        proc = subprocess.Popen(command)
        pids.append(proc.pid)
        
    return pids

def write_pids(pids):
    '''Writes the pids to stdout, so that the caller can redirect
    them as they desire'''
    pids_str = ','.join(str(x) for x in pids)
    print pids_str
    return pids_str
        
        

def main():
    '''Main'''
    if (not is_root_user()):
        sys.stderr.write("ERROR: %s must be run as root\n" % sys.argv[0])
        sys.exit(-1)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interface', dest = 'network_interface',
          type = str, required = True,
          help = 'network interface (eth0, for example)')
    parser.add_argument('-o', '--output-dir', dest = 'output_dir',
          type = str, required = True,
          help = 'output directory for log files')
    parser.add_argument('-t', '--time-interval', dest = 'interval',
          type = float, required = True,
          help = 'interval at which system utilization should be polled. '
                 'Value is in seconds, use decimals for sub-second intervals '
                 '(.1, .01, etc.)')
    parser.add_argument('-b', '--ip-blacklist', dest='ip_blacklist',
            type = str, required = False, default='',
            help = 'list of ips to blacklist for network capture, as a'
                   'comma-separated list of ip addresses (1.1.1.1,2.2.2.2)')
    
    options = parser.parse_args()
    
    assert os.path.isdir(options.output_dir), \
                         "output directory must exist and be a directory"
    assert options.interval > 0, "interval must be greater than 0"
    

    commands = build_commands(options.output_dir, options.interval, 
                    options.network_interface, options.ip_blacklist.split(','))
    pids = start_monitors(commands)
    write_pids(pids)
    
                              
if __name__ == '__main__':
    main()
