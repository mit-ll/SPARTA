#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module creates graphs of perfrmance data
# *****************************************************************


import datetime
import math
import os
import sys
import argparse
import time
import re
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.report_generation.common.graphing import graph2d
from spar_python.perf_monitoring.time_utils import divide_timedelta, epoch_to_sql
from spar_python.perf_monitoring.perf_db import create_perf_db
from spar_python.analytics.common.log_parser_util import LogParserUtil


class PerfGraphGenerator(object):
    '''Object to generate graphs from performance monitoring data'''
    
    def __init__(self, con):
        '''Initializer.
        
        Inputs:
        con : connection to the sqlite3 performance monitoring database
        '''
        self._con = con


    def _produce_graph(self, plot_name, dataset, x_label, y_label):
        '''Calls MZ's graphing code.
        
        Inputs:
        plot_name: The name of the plot.
        datasets: A list of (x value list, y value list, data_set_name,
            best_fit_function) tuples.
        x_label: The x-axis label
        y_label: The y-axis label
        
        Returns: the graph as a png in the form of a string
        '''
        return graph2d(plot_name, dataset, x_label, y_label, drawlines=True)


    def produce_ram_graph(self, starttime, endtime):
        '''Produces a graph of ram usage, per-system, between
        starttime and endtime, or None if there are no data points
        
        Inputs:
        starttime: beginning of time frame over which to graph ram usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
        endtime: end of time frame over which to graph ram usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
            
        returns: the graph as a png in the form of a string
        '''
        # get the points from the database
        query = \
            "SELECT host, time, used_kb from Ram WHERE time BETWEEN ? AND ?;"
        
    
        # MZ's graphing code needs a dataset of the form:
        # datasets: A list of (x value list, y value list, data_set_name,
        #       best_fit_function) tuples.
        results = { }
        datetime_start = datetime.datetime.strptime(starttime, 
                                                    "%Y-%m-%d %H:%M:%S.%f")
        for row in self._con.execute(query, (starttime, endtime)):
            host = row[0]
            datetime_measure = datetime.datetime.strptime(row[1], 
                                                    "%Y-%m-%d %H:%M:%S.%f")
            used = row[2]
            
            if host not in results.keys():
                results[host] = ([], [], host + ' ram usage', None)
            results[host][0].append((datetime_measure - 
                                     datetime_start).total_seconds())
            results[host][1].append(used)
        
        if len(results) == 0:
            return None
            
        # sort results by time, in case they aren't initially
        sortedresults = {}
        for k in results.keys():
            x_values, y_values = \
                (list(x) for x in 
                 zip(*sorted(zip(results[k][0], results[k][1]))))
            sortedresults[k] = \
                (x_values, y_values, results[k][2], results[k][3])
        
        return self._produce_graph("Ram usage", sortedresults.values(), 
                             "time (seconds since start of measurement)", 
                             "Ram used (kb)")

    def produce_cpu_graph(self, starttime, endtime, ignored_cpus=None):
        '''Produces a graph of cpu usage, per-system, between
        starttime and endtime, or None if there are no data points
        
        Inputs:
        starttime: beginning of time frame over which to graph cpu usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
        endtime: end of time frame over which to graph cpu usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
        ignored_cpus (optional, default=empty): a dictionary of cpus to ignore,
            usually because those are the cpus the test harness itself was 
            pinned to.  Format is a dictionary, with keys set to hosts, and 
            values a list of cpus to ignore for that host
            for example:
            { "client" : ["cpu_0", "cpu_1"],
              "server" : ["cpu_3", "cpu_7"] }
              
        returns: the graph as a png in the form of a string
        '''
        if ignored_cpus is None:
            ignored_cpus = {}
        # get the points from the database
        query = "SELECT host, time, cpu_identifier, total_pct "  + \
            "from Cpu WHERE time BETWEEN ? AND ?;"
    
        # MZ's graphing code needs a dataset of the form:
        # datasets: A list of (x value list, y value list, data_set_name,
        #       best_fit_function) tuples.
        '''Note: Should think about how to best represent this.
        
        Options:
        one datapoint per cpu
        one datapoint per host, each datapoint average(cpus on host)
        anything else?  other ways to "average"?

        Initially tried an average of all CPUs, and the graph looks...
        strange.
        
        Going with per-cpu, as that will help distinguish between
        'we need more cores' and 'we need faster cores'
        
        '''
        
        datetime_start = datetime.datetime.strptime(starttime, 
                                                    "%Y-%m-%d %H:%M:%S.%f")
        
        results = {}
        for row in self._con.execute(query, (starttime, endtime)):
            host = row[0]
            timestr = row[1]
            cpu = row[2]
            used = row[3]
            
            if (host in ignored_cpus.keys()):
                if (cpu in ignored_cpus[host]):
                    continue
            
            hostcpu = host + " " + cpu
            if hostcpu not in results.keys():
                results[hostcpu] = ([], [], hostcpu + ' utilization', None)
           
            datetime_measure = datetime.datetime.strptime(timestr, 
                                                  "%Y-%m-%d %H:%M:%S.%f")
            results[hostcpu][0].append(
                        (datetime_measure - datetime_start).total_seconds())
            results[hostcpu][1].append(used)
            
        # end for each row in database
        if len(results) == 0:
            return None

        # sort results by time, in case they aren't initially
        sortedresults = {}
        for k in results.keys():
            x_values, y_values = \
                (list(x) for x in 
                 zip(*sorted(zip(results[k][0], results[k][1]))))
            sortedresults[k] = \
                (x_values, y_values, results[k][2], results[k][3])
        
        return self._produce_graph("CPU Utilization", sortedresults.values(), 
                         "time (seconds since start of measurement)", 
                         "CPU utilization (percent)")

        
    def produce_disk_graph(self, starttime, endtime, ignored_disks=None):
        '''Produces a graph of disk usage, per-system, between
        starttime and endtime, or None if there are no data points
        
        Inputs:
        starttime: beginning of time frame over which to graph disk usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
        endtime: end of time frame over which to graph disk usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
        ignored_disks (optional, default=empty): a dictionary of disks to 
            ignore, usually because those are only used by the test harness, 
            and not the performers.  Format is a dictionary, with keys set to 
            hosts, and  values a list of disks to ignore for that host
            for example:
            { "client" : ["sda", "sdb"],
              "server" : ["sda"] }
              
        returns: the graph as a png in the form of a string
        '''
        if ignored_disks is None:
            ignored_disks = {}
        # get the points from the database
        query = "SELECT host, time, disk_name, reads_kbps, writes_kbps " + \
            "from Disk WHERE time BETWEEN ? AND ?;"
                
        # MZ's graphing code needs a dataset of the form:
        # datasets: A list of (x value list, y value list, data_set_name,
        #       best_fit_function) tuples.
        '''Talking this over with Sophia, we agreed that the important metric
        is reading/writing per-host, and not per-disk-per-host
        '''
        
        alldatapoints = { }
        datetime_start = datetime.datetime.strptime(starttime, 
                                                    "%Y-%m-%d %H:%M:%S.%f")
        for row in self._con.execute(query, (starttime, endtime)):
            host = row[0]
            timestr = row[1]
            disk = row[2]
            reads = row[3]
            writes = row[4]

            if (host in ignored_disks.keys()):
                if (disk in ignored_disks[host]):
                    continue
            
            hosttime = (host, timestr)
            
            if hosttime not in alldatapoints.keys():
                alldatapoints[hosttime] = [0.0, 0.0] # reads_kbps, writes_kbps
            alldatapoints[hosttime] = [
                                alldatapoints[hosttime][0] + float(reads), 
                                alldatapoints[hosttime][1] + float(writes)
                                ]
            
        # end for each row in database
        if len(alldatapoints) == 0:
            return None

        # now create datapoints for graphing 
        results = {}
        for key in alldatapoints.keys():
            host = key[0]
            timestr = key[1]
            reads = alldatapoints[key][0]
            writes = alldatapoints[key][1]
            datetime_measure = datetime.datetime.strptime(timestr, 
                                                  "%Y-%m-%d %H:%M:%S.%f")

            host_read = host + " r"
            host_write = host + " w"
            if host_read not in results.keys():
                results[host_read] = ([], [], 
                                  host + ' disk utilization (reading)', None)
                results[host_write] = ([], [], 
                                  host + ' disk utilization (writing)', None)
            results[host_read][0].append(
                        (datetime_measure - datetime_start).total_seconds())
            results[host_read][1].append(reads)
            results[host_write][0].append(
                        (datetime_measure - datetime_start).total_seconds())
            results[host_write][1].append(writes)

        # sort results by time, in case they aren't initially
        sortedresults = {}
        for k in results.keys():
            x_values, y_values = \
                (list(x) for x in 
                 zip(*sorted(zip(results[k][0], results[k][1]))))
            sortedresults[k] = \
                (x_values, y_values, results[k][2], results[k][3])

        
        return self._produce_graph("Disk Utilization", sortedresults.values(), 
                             "time (seconds since start of measurement)", 
                             "Disk utilization (kbps)")
        
    def produce_network_graph(self, starttime, endtime, numbins=20):
        '''Produces a graph of network usage, per-system, between
        starttime and endtime, or None if there are no data points
        
        Inputs: 
        starttime: beginning of time frame over which to graph network usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
        endtime: end of time frame over which to graph network usage
            format: YYYY-MM-DD HH:MM:SS.SSS (epoch_to_sql may be helpful)
        numbins (optional): The data points of the graph will be the amount
            of data sent from one party to another during a given time 
            interval, where is time interval is equal in length and there are
            [numbins] number of intervals.  If (endtime-starttime) is 
            2 seconds, and numbins is 5, then the first data point is the 
            amount of data sent between (starttime, starttime+0.4), the second 
            (startime+0.4, starttime+0.8), etc.
            
            Default value: 20       
             
        returns: the graph as a png in the form of a string
        '''
        # get the points from the database
        query = "SELECT time, direction, payloadlength FROM Network WHERE " + \
            "time BETWEEN ? AND ?;"
                
        # MZ's graphing code needs a dataset of the form:
        # datasets: A list of (x value list, y value list, data_set_name,
        #       best_fit_function) tuples.
        
        results = { }
        datetime_start = datetime.datetime.strptime(starttime, 
                                                    "%Y-%m-%d %H:%M:%S.%f")
        datetime_end = datetime.datetime.strptime(endtime, 
                                                    "%Y-%m-%d %H:%M:%S.%f")
        time_window = (datetime_end - datetime_start)
        binsize = time_window / numbins
        binsize_str = "%d.%d secoonds" % \
            (binsize.seconds, binsize.microseconds) 
        
        for row in self._con.execute(query, (starttime, endtime)):
            timestr = row[0]
            direction = row[1]
            payload_size = int(row[2])
            
            timestamp = datetime.datetime.strptime(timestr, 
                                                    "%Y-%m-%d %H:%M:%S.%f")
            bin_number = int(math.floor(
                    divide_timedelta(timestamp - datetime_start, binsize)))
            
          
            
            if (direction not in results.keys()):
                results[direction] = (range(1, numbins+1), [0]*numbins, 
                                      direction + ' network utilization', None)
            results[direction][1][bin_number] += payload_size

        if len(results) == 0:
            return None

        # sort results by time, in case they aren't initially
        sortedresults = {}
        for k in results.keys():
            x_values, y_values = \
                (list(x) for x in 
                 zip(*sorted(zip(results[k][0], results[k][1]))))
            sortedresults[k] = \
                (x_values, y_values, results[k][2], results[k][3])
            
        return self._produce_graph("Network Utilization", 
                     sortedresults.values(), 
                     "interval number (interval size = " + binsize_str + " )", 
                     "Disk utilization (kbps)")
 
    def produce_all_graphs(self, starttime, endtime, output_dir, test_name):
        '''Produce all four graphs between starttime, endtime
        Write to output_dir/<type>_test_name.png
        
        Returns: nothing'''
    
      
        image = self.produce_cpu_graph(starttime, 
                                                  endtime)
        if (image != None):
            imagefile = open(os.path.join(options.output_dir, 
                                      "cpu_" + test_name + ".png"), "w")
            imagefile.write(image)
            imagefile.close()
        image = self.produce_disk_graph(starttime, 
                                                   endtime)
        if (image != None):
            imagefile = open(os.path.join(options.output_dir, 
                                      "disk_" + test_name + ".png"), "w")
            imagefile.write(image)
            imagefile.close()
        
        image = self.produce_ram_graph(starttime, 
                                                   endtime)    
        if (image != None):
            imagefile = open(os.path.join(options.output_dir, 
                                      "ram_" + test_name + ".png"), "w")
            imagefile.write(image)
            imagefile.close()
        
        image = self.produce_network_graph(starttime, 
                                                      endtime)
        if (image != None):
            imagefile = open(os.path.join(options.output_dir, 
                                      "network_" + test_name + ".png"), "w")
            imagefile.write(image)
            imagefile.close()    


    def produce_graphs_from_log(self, filename, output_dir):
        '''Gets the first and last timestamp from a given log file,
        and the test name.
        Generates performance graphs over the start/end times and
        writes them to the output directory.

        Parameter is a filename (not a handle) because 
        resolve_ts_to_temp wants a filename
        
        Returns: a tuple of (test name, start time, end time),
        where times are floats representing seconds since the epoch
        '''
        
        
        handle = LogParserUtil().resolve_ts_to_temp(filename) # returns a handle
        
        timestamp_regex = re.compile("^\[([0-9]+\.[0-9]+)\] ")
        start_time = None
        test_name = None
        # start_time is from first_line
        for line in handle:
            match = timestamp_regex.match(line)
            if match:
                start_time = float(match.groups()[0])
                splits = line.split()
                test_name = splits[len(splits)-1]
                break
        
        assert start_time is not None, "Could not retrieve timestamp from log file " + filename
        assert test_name is not None, "Could not retrieve filename from log file " + filename
    
        # end_time is the last time found
        end_time = None
        for line in handle:
            match = timestamp_regex.match(line)
            if match:
                end_time = float(match.groups()[0])
        assert end_time is not None, "Could not retrieve timestamp from log file " + filename
        
        start_time_str = epoch_to_sql(start_time)
        end_time_str = epoch_to_sql(end_time)
        
        self.produce_all_graphs(start_time_str, end_time_str, output_dir, test_name)
        
                            
def main():
    '''Produce graphs between starttime and stoptime'''
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-i', '--input_file', dest = 'sqlite_file',
          type = str, required = True,
          help = 'sqlite3 file to read from')
    parser.add_argument('-s', '--starttime', dest = 'starttime',
          type = str, required = True, 
          help = 'start of desired range, in YYYY-MM-DD HH:MM:SS.SSS format')
    parser.add_argument('-e', '--endtime', dest = 'endtime',
          type = str, required = True, 
          help = 'end of desired range, in YYYY-MM-DD HH:MM:SS.SSS format')
    parser.add_argument('-b', '--bins', dest = 'numbins',
          type = int, required = False, default=20,
          help = 'Number of bins to use for network data (default=20)')
    parser.add_argument('-o', '--output_dir', dest = 'output_dir',
          type = str, required = True,
          help = 'directory to write graphs to')
    
    options = parser.parse_args()    

    assert os.path.isdir(options.output_dir)
    assert os.path.isfile(options.sqlite_file)
    
    con = create_perf_db(options.sqlite_file)
    graph_generator = PerfGraphGenerator(con)
    test_name = str(time.time())
    
    graph_generator.produce_all_graphs(options.starttime, options.endtime, options.output_dir, test_name)
   
   
                              
if __name__ == '__main__':
    main()

