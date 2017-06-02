# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Tim Meunier
#  Description:        Utility class for log parser scripts.
# *****************************************************************
import logging
import os
import sys
import re
import tempfile


class LogParserUtil:
    ''' Utility class to hold functionality used by multiple log parsing
        scripts'''

    LOGGER = None

    def __init__(self):
        self.LOGGER = logging.getLogger(__name__)
        # Define known lines in the log that can be ignored without warning
        self.ignore_regex = [re.compile('\[[0-9.]+\] Invoked from .*'),
                             re.compile('\[[0-9.]+\] (Unloaded|VariableDelay)QueryRunner .*'),
                             re.compile('\[[0-9.]+\] ID .+ queued.*'),
                             re.compile('\[[0-9.]+\] NOTE: .*')]

    def hwclock_to_epoch_log_converter(self, read_f, write_f):
        ''' Parses a log file to find real clock time stamps and updates
        the logging tmestamps normalized to the clock time.  A new file
        is writren with the updated timestamps. '''

        epoch_patt = re.compile("^\[([0-9]+\.[0-9]+)\] EPOCH_TIME: "
                                "([0-9]+\.[0-9]+)$") 
        reg_patt = re.compile("^\[([0-9]+\.[0-9]+)\] (.*)") 

        # find first EPOCH_TIME stamp
        base_rel = None
        base_sys = None
        for line in read_f:
            result = epoch_patt.match(line)
            if result:
                groups = result.groups()
                base_rel = float(groups[0])
                base_sys = float(groups[1])
                log_str = "EPOCH_TIME @ " + ("%.9f" % base_sys) + \
                          " will be synced with " + \
                          "CLOCK_MONOTONIC_RAW @ " + ("%.9f" % base_rel) + "\n"
                self.LOGGER.info(log_str[:-1])
                break
        if not base_rel or not base_sys:
            self.LOGGER.info("No epoch timestamp could be found; no " + \
                             "conversion to be done.")
            #sys.exit(0)
        read_f.seek(0)

        # write new log file with resolved relative timestamps
        last_ts = -1.0
        for line in read_f:
            epoch_result = epoch_patt.match(line)
            reg_result = reg_patt.match(line)
            if epoch_result:
                groups = epoch_result.groups()
                new_base_rel = float(groups[0])
                new_base_sys = float(groups[1])
                if new_base_rel != base_rel and new_base_sys != base_sys:
                    drift = ((new_base_sys - new_base_rel) - \
                             (base_sys - base_rel))
                    log_str = "EPOCH_TIME re-synced with " + \
                              "CLOCK_MONOTONIC_RAW.  CLOCK_MONOTONIC_RAW " + \
                              "drifted by " + ("%.9f" % drift) + \
                              " relative to EPOCH_TIME at last sync\n"
                    self.LOGGER.info(log_str[:-1])
                base_rel = new_base_rel
                base_sys = new_base_sys
            elif reg_result:
                groups = reg_result.groups()
                timestamp = float(groups[0])
                if timestamp < last_ts:
                    try:
                        filename = read_f.name
                    except AttributeError:
                        filename = "StringIO_object"
                    self.LOGGER.warning("log entry @ " + str(timestamp) + \
                                   " has a timestamp earlier " + \
                                   "than the previous entry @ " + \
                                   str(last_ts) + " in file=" + filename)
                last_ts = timestamp
                log_str = "[" + ("%.9f" % (base_sys + \
                                           (timestamp - base_rel))) + \
                          "] " + groups[1] + "\n"
                write_f.write(log_str)
            else:
                write_f.write(line)


    def resolve_ts_to_temp(self, orig_file):
        ''' Call the hwclock_to_epoch_log_converter method on orig_file
        producing a new temporary file.  Returns the updated temporary
        file handle.
        '''
        ts_modified_file = tempfile.TemporaryFile()

        try:
            infile = open(orig_file, 'r')
        except IOError:
            self.LOGGER.error('Could not open log file %s, skipping', orig_file)
            return None

        self.hwclock_to_epoch_log_converter(infile, ts_modified_file)

        infile.close()
        ts_modified_file.seek(0)

        return ts_modified_file

    def compute_latency(self, time1, time2):
        '''Computes the latency from two times.
        param time1 - the begin time - in string format 
            e.g. "1360089945.0922334455"
        param time2 - the end time - in string format 
             e.g. "1360089945.0922334455"
        return the latency - as a float
        '''
        num1 = float(time1)
        num2 = float(time2)
        return float(num2 - num1)

    def expand_path(self, path):
        '''Expands a path for ~ and environment variables, normalizes it
           and follows symlinks.'''
        return os.path.realpath( \
                   os.path.normpath( \
                       os.path.expanduser( \
                           os.path.expandvars(path))))

    def find_logs(self, in_dir, file_pattern):
        '''Searches a given directory for files matching the expected log file
        naming convention and returns the list of files found.'''
        file_list = []
        if not os.path.isdir(in_dir):
            raise Exception("Input directory does not exist")
        for path in os.listdir(in_dir):
            full_path = self.expand_path(os.path.join(in_dir, path))
            if os.path.isdir(full_path):
                # Skip directories
                continue
            # Look for a matching file pattern
            file_match = file_pattern.match(path)
            if file_match:
                file_list.append(full_path)
        if len(file_list) < 1:
            raise Exception("No matching log files found")
        return file_list 

    def capture_failure(self, in_file):
        '''Grabs the failure message from the log and returns a list of
        lines contaiing the error message.  It always starts with FAILED
        in order to separate multiple failures.'''
        fail_msgs = ['FAILED']
        for line in in_file:
            line = line.strip()
            if line == 'ENDFAILED':
                break
            fail_msgs.append(line)
        return fail_msgs

    def verify_result(self, result, columns):
        '''Takes a result dict and a list of required keys.  If all keys are
        present in the dict, return true, false otherwise.'''
        for key in columns:
            if key not in result:
                return False
        return True

    def ignorable_line(self, line):
        '''Checks line against known ignorable lines to squelch warnings'''
        for ignore in self.ignore_regex:
            match = ignore.match(line)
            if match:
                return True
        return False 

    def process_events(self, events):
        """Sort and separate the list of events and timestamps.  Returns a 
           list of timestamps and a list of event ids sorted by timestamp."""
        ts_list = []
        event_list = []
        val_list = []
        for ts in sorted(events, key=float):
            ts_list.append(ts)
            event_list.append(events[ts][0])
            if events[ts][1]:
                val_list.append(events[ts][1])
            else:
                val_list.append('')
        return (ts_list, event_list, val_list)
