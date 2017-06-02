#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      time_utils.py 
# *****************************************************************

import unittest
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.time_utils import divide_timedelta, epoch_to_sql, date_and_time_to_epoch
import datetime

class TimeUtilsTest(unittest.TestCase):
    '''Unit tests for time_utils.py'''
        
    def test_divide_timedelta(self):
        '''
        Tests for divide_timedelta in time_utils
        '''
        five_ms = datetime.timedelta(microseconds=5)
        ten_ms = datetime.timedelta(microseconds=10)
        twelve_ms = datetime.timedelta(microseconds=12)
        fifteen_seconds = datetime.timedelta(seconds=15)
        twenty_seconds = datetime.timedelta(seconds=20)
        thirty_seconds = datetime.timedelta(seconds=30)
        
        self.assertEqual(int(divide_timedelta(ten_ms, five_ms)), 2)
        self.assertEqual(int(divide_timedelta(twelve_ms, five_ms)), 2)
        self.assertEqual(int(divide_timedelta(five_ms, five_ms)), 1)
        self.assertEqual(int(divide_timedelta(ten_ms, twelve_ms)), 0)      
        self.assertEqual(int(divide_timedelta(twenty_seconds, fifteen_seconds)), 1)
        self.assertEqual(int(divide_timedelta(thirty_seconds, fifteen_seconds)), 2)
        self.assertEqual(int(divide_timedelta(fifteen_seconds, fifteen_seconds)), 1)
        self.assertEqual(int(divide_timedelta(twenty_seconds, thirty_seconds)), 0)

    def test_epoch_to_sql(self):
        '''
        Tests for epoch_to_sql
        '''
        inputs = [
                  datetime_to_epoch(datetime.datetime(2013, 7, 29, 4, 8, 15, 100000)),
                  datetime_to_epoch(datetime.datetime(2011, 12, 9, 8, 56, 27, 465123)),
                  datetime_to_epoch(datetime.datetime(2013, 1, 31, 9, 0, 0, 874216)),
                  datetime_to_epoch(datetime.datetime(2014, 8, 18, 15, 59, 59, 555555)),
                  datetime_to_epoch(datetime.datetime(2016, 4, 5, 23, 37, 47, 852741)),
                  datetime_to_epoch(datetime.datetime(2012, 10, 23, 17, 43, 32, 963258))
                  ]
        outputs = [
                   "2013-07-29 04:08:15.100000",
                   "2011-12-09 08:56:27.465123",
                   "2013-01-31 09:00:00.874216",
                   "2014-08-18 15:59:59.555555",
                   "2016-04-05 23:37:47.852741",
                   "2012-10-23 17:43:32.963258"
                   ]
        
        for i in range(len(inputs)):
            self.assertEqual(epoch_to_sql(inputs[i]), outputs[i])
            
    def test_date_and_time_to_epoch(self):
        '''tests for date_and_time_to_epoch'''
        dates = ["20110523", "20130607", "20130930"]
        times = ["04:05:08.1", "23:34:45.678901", "15:43:23.000"]
        datetimes = [datetime.datetime(2011, 5, 23, 4, 5, 8, 100000),
                     datetime.datetime(2013, 6, 7, 23, 34, 45, 678901),
                     datetime.datetime(2013, 9, 30, 15, 43, 23)]
        #Generated from bash: date 'May 23 2011 04:05:08 UTC'
        epochs = [1306123508.1, 1370648085.678901, 1380555803] 
        
        for i in range(len(dates)):
            #self.assertEqual(date_and_time_to_epoch(dates[i], times[i]), datetime_to_epoch(datetimes[i]))
            self.assertEqual(date_and_time_to_epoch(dates[i], times[i]), epochs[i])
            
        
def datetime_to_epoch(dt):
    ''' Helper function '''
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds()
    
