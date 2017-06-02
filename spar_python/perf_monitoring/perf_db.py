#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module creates the sqlite3 database
#                      that will store the SPAR performance
#                      monitoring results                       
# *****************************************************************

import sqlite3 as sql
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.time_utils import epoch_to_sql

NETWORK_TABLE = "Network"
NETWORK_SCHEMA = "Network(id INTEGER PRIMARY KEY AUTOINCREMENT, " + \
    "time TEXT, " + \
    "direction TEXT, " + \
    "payloadlength INTEGER, " + \
    "protocol TEXT)"
CPU_TABLE = "Cpu"
CPU_SCHEMA = "Cpu(id INTEGER PRIMARY KEY AUTOINCREMENT, " + \
    "host TEXT, " + \
    "cpu_identifier TEXT, " + \
    "time TEXT, " + \
    "user_pct REAL, sys_pct REAL, " + \
    "wait_pct REAL, " + \
    "irq_pct REAL, " + \
    "idle_pct REAL, " + \
    "total_pct REAL)"
RAM_TABLE = "Ram" 
RAM_SCHEMA = "Ram(id INTEGER PRIMARY KEY AUTOINCREMENT, " + \
    "host TEXT, " + \
    "time TEXT, " + \
    "used_kb REAL, " + \
    "free_kb REAL, " + \
    "swap_total REAL, " + \
    "swap_used REAL, " + \
    "swap_free REAL)"
DISK_TABLE = "Disk"
DISK_SCHEMA = "Disk(id INTEGER PRIMARY KEY AUTOINCREMENT, " + \
    "host TEXT, " + \
    "time TEXT, " + \
    "disk_name TEXT, " + \
    "reads_per_sec REAL, " + \
    "reads_kbps REAL, " + \
    "writes_per_sec REAL, " + \
    "writes_kbps REAL)"

def create_perf_db(filename):
    '''Creates the database to store performance monitoring results
    
    Input: filename to for the database.  ":memory:" is a special value
    indicating that the database should remain in memory only
    and not be written to disk
    
    Returns: a connection to the created database
    '''
    con = sql.connect(filename)
    
    con.execute("CREATE TABLE IF NOT EXISTS " + NETWORK_SCHEMA + ";")
    con.execute("CREATE TABLE IF NOT EXISTS " + CPU_SCHEMA + ";")
    con.execute("CREATE TABLE IF NOT EXISTS " + RAM_SCHEMA + ";")
    con.execute("CREATE TABLE IF NOT EXISTS " + DISK_SCHEMA + ";")
    
    con.commit()
    
    return con

def insert_network(con, time, direction, payload_size, protocol, commit=True):
    '''Inserts a row into the network table in the performance database.
    
    Inputs:
    con: a connection to the database: squlite3 connection
    time: time in the form of seconds since the epoch: float
    direction: the direction of traffic ("client_to_server, etc): string
    payload_size: number of bytes in the payload: integer
    protocol: the network protocol ("IP/TCP", etc): string
    commit (optional): whether or not to commit the insertion to disk (default=True)
    '''
    con.execute("INSERT INTO " + NETWORK_TABLE + " Values(Null,?,?,?,?);", 
                   (epoch_to_sql(time), direction, payload_size, protocol))
    if (commit):
        con.commit()
    return con
    
def insert_cpu(con, host, identifier, time, user_pct, 
               sys_pct, wait_pct, irq_pct, idle_pct, total_pct, commit=True):
    '''Inserts a row into the cpu table in the performance database.
    
    Inputs:
    con: a connection to the database: squlite3 connection
    host: hostname ("server"): string
    identifier: cpu identifier ("cpu 1"): string
    time: time in the form of seconds since the epoch: float
    user_pct: percentage of time spent on userland processes 
    sys_pct: percentage of time spent on system processes
    wait_pct: percentage of time spent waiting on I/O
    irq_pct: percentage of time spent processing interrupts
    idle_pct: percentage of time spent idle
    total_pct: percentage of time spent on (user+sys) processes
    commit (optional): whether or not to commit the insertion to disk (default=True)
    '''
    con.execute("INSERT INTO " +CPU_TABLE+ " Values(Null,?,?,?,?,?,?,?,?,?);",
                   (host, identifier, epoch_to_sql(time), user_pct, 
                    sys_pct, wait_pct, irq_pct, idle_pct, total_pct))
    if (commit):
        con.commit()
    return con

def insert_ram(con, host, time, used_kb, free_kb, 
               swap_total, swap_used, swap_free, commit=True):
    '''Inserts a row into the ram table in the performance database.
    
    Inputs:
    con: a connection to the database: squlite3 connection
    host: hostname ("server"): string
    time: time in the form of seconds since the epoch: float
    used_kb: amount of memory used: float
    free_kb: amount of free memory: float
    swap_total: amount of swap allocated by the system: float
    swap_used: amount of swap in use: float
    swap_free: amount of available swap: float
    commit (optional): whether or not to commit the insertion to disk (default=True)
    '''
    con.execute("INSERT INTO " + RAM_TABLE + " Values(Null,?,?,?,?,?,?,?);", 
                (host, epoch_to_sql(time), used_kb, free_kb, 
                 swap_total, swap_used, swap_free))
    if (commit):
        con.commit()
    return con

def insert_disk(con, host, time, disk_name, reads_per_sec, 
                reads_kbps, writes_per_sec, writes_kbps, commit=True):
    '''Inserts a row into the disk table in the performance database.
    
    Inputs:
    con: a connection to the database: squlite3 connection
    host: hostname ("server"): string
    time: time in the form of seconds since the epoch: float
    disk_name: name of the disk ("/dev/sda"): string
    reads_per_sec: number of reads per second: float
    reads_kbps: amount of data read in kbps: float
    writes_per_sec: number of writes per second: float
    writes_kbps: amount of data written in kbps: float
    commit (optional): whether or not to commit the insertion to disk (default=True)
    '''
    con.execute("INSERT INTO " + DISK_TABLE + " Values(Null, ?,?,?,?,?,?,?);", 
                (host, epoch_to_sql(time), disk_name, reads_per_sec, 
                 reads_kbps, writes_per_sec, writes_kbps))
    if (commit):
        con.commit()
    return con
