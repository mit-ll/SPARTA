# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Various classes to inform user of progress
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  19 Oct 2012  jch            Original file
# *****************************************************************

"""
This module holds various progress-informers: classes which will keep track
of various forms of progress (file-processing, row-generating, etc) and
keep the user appropriately informed of progress.

"""

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import datetime

class RowAggregatorProgressReporter(object):
    
    def __init__(self, logger, rows_expected):
        self.__logger = logger
        self.__num_created_rows = 0
        self.__notification_rate = 1000
        self.__start_t = datetime.datetime.now()
        self.__num_total_rows = rows_expected
        
        
    def add(self, num_rows):
        self.__num_created_rows += num_rows
 
        num_so_far = self.__num_created_rows
        if num_so_far % self.__notification_rate == 0:
            now_t = datetime.datetime.now()
            elapsed = now_t - self.__start_t
            rows_per_sec = \
                float(num_so_far) / elapsed.total_seconds()
            seconds_left = \
                float(self.__num_total_rows - num_so_far) / rows_per_sec
            left_td = datetime.timedelta(0, seconds_left)
            self.__logger.info("%d rows processed. "
                               "Estimated time remaining: %s"
                               % (num_so_far, left_td))


    def add_list(self, results_list):
        self.add( len(results_list) )
    
    
    def done(self):
        end_t = datetime.datetime.now()
        elapsed = end_t - self.__start_t
        self.__logger.info("Done. %s rows successfully generated. "
                           "Elapsed time: %s" 
                           % (self.__num_created_rows, 
                              elapsed))
    
    
 
