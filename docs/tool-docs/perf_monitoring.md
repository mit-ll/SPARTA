Performance Monitoring
===============================================================================
The subsystem measures resource utilization by the system under test (SUT).  It  captures four components: CPU, Disk, Memory (RAM), and Network.  It has  dependencies of `collectl` for measuring CPU, Disk, and Memory, and `tcpdump` for measuring Network utilization.  It requires root privilege as this is a requirement for network capture.

##Setup
### Dependencies
Data collection dependencies:
* `collectl`: [project site](http://collectl.sourceforge.net/)
* `tcpdump`: [project site](http://www.tcpdump.org/)

Data analysis dependency:
* `scapy`: [project site](http://www.secdev.org/projects/scapy/)
* `matplotlib`: [project site](http://matplotlib.org/)

### Installation Notes
Follow the [Installation Instructions](../INSTALL.md). If you want to do your own install, you generally need to run the following:
```
sudo apt-get install collectl
sudo apt-get install tcpdump
pip install scapy-real
pip install matplotlib
```
### Unit Test Notes
Most tests run autmomatically with `scons test` or `nosetests`. The tests for the graphing component of this subsystem (found in `create_perf_graphs_test.py`) require human interaction and are commented out by default. To run these tests, uncomment the appropriate lines and make sure you install the pillow package if it isn't already (`pip install pillow`).

## User Manual 
Performance monitoring happens in a number of steps:

1. Collect data
2. Insert data into a results database
3. Produce graphs from results database for specified time periods

### Collect data
Data collection must be initiated individually on each host.  On each host, run:
```
sudo python start_perf_monitors.py [FLAGS] > pid_file.txt
```

The flags for this program are:
- `-i` network_interface: network interface to capture on (eth0, for example)
- `-o` output_dir: directory to write log files to 
- `-t` interval: rate at which to capture metrics, in seconds (60 for once per minute, .1 for 10 times per second)
- `-b` ip_blacklist: list of ips to blacklist for network capture, as a comma-separted list (e.g., `"1.1.1.1,2.2.2.2"`)

This program launches 4 process, one per component captured. It writes the pids of these processes to stdout for later use. It is recommended that this output be redirected to a file.

Upon completion of the event being measured, the collection processes must be stopped. To do this, on each host, run:
```
python stop_perf_monitors.py < pid_file.txt
```

`pid_file.txt` must be the captured output from `start_perf_monitors.py`.

### Insert data into a results database

The cpu, disk, and memory log files will be compressed and must first be uncompressed via a compression tool such as `gunzip`. Once that is done, the data can be loaded into a database by running:
```
python perf_logs_to_db.py [FLAGS]
```

The flags for this program are:

- `-e` endpoint: the name of this endpoint ("client")
- `-c` cpu_file: the uncompressed cpu log file
- `-d` disk_file: the uncompressed disk log file
- `-r` ram_file: the uncompressed memory log file
- `-n` network_file: the pcap log file
- `-m` network_map: a file containing a map from IP address to host ("client"). Each mapping should be a on a single line and be of the form: `IP = host` (e.g., `192.168.4.5 = client\n192.168.7.8 = server`)
- `-o` sqlite_file: the database file to write to/append to

### Produce graphs from results database for specified time periods
Once the database has ingested all of the data, it can produce graphs (as .png files) covering specified time periods.  To do this, run:
```
python create_perf_graphs.py [FLAGS]
```  

The flags for this program are:
- `-i` sqlite_file: the input database file (produced by the previous step)
- `-s` starttime: beginning of the time period to be graphed, in the form
YYYY-MM-DD SS.SSS
- `-e` endtime: end of the time period to be graphed, in the form
YYYY-MM-DD SS.SSS
- `-b` numbins: the number of bins to use when graphing network data (default=20)
- `-o` output_dir: the directory to write the graphs to.

Additionally, one can create these graphs programatically by using the `create_[component]_graph` methods in `create_perf_graphs.py`. The returned value from each of these functions is a png as a string.

## Known Issues
* This subsystem measures the usage of the entire host system and does not break apart resource usage by process. Our use case required sub-second measurement intervals. The utilities we found that would gather per-process metrics were not capable of supporting sub-second measurement intervals. The effect of this issue can be mitigated by limiting the number of non-system-under-test processes running on the measured system.

* If measurement of disk activity is desired, the log files produced by this subsystem should be written to a separate physical disk from the one used by the system under test. This is so that the disk usage of the system under test can be distinguished from the disk usage of this subsystem.

