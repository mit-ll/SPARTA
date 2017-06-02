#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module performs a number of utility
#                      functions regarding time that can be used
#                      by the various performance monitoring tools
# *****************************************************************

import datetime

def divide_timedelta(numerator, denominator):
    '''Divides one datetime.timedelta by another.
    
    For example: how many (size) bins are between
    (beginning) and (end):
    numbins = math.ceil(divide_timedelta(end - beginning, size))
    
    Or: which bin should (this_timestamp) fall into?
    bin = int(divide_timedelta(this_timestamp - beginning, size))
    
    Returns a float.'''
    assert isinstance(numerator, datetime.timedelta)
    assert isinstance(denominator, datetime.timedelta)
    numerator_in_s = numerator.total_seconds()
    denominator_in_s = denominator.total_seconds()
    if (denominator_in_s == 0):
        raise ValueError("Denominator is 0 seconds")
    result = (numerator_in_s / denominator_in_s)
    return result


def epoch_to_sql(seconds_since_epoch):
    '''Converts a time from seconds since the epoch to
    the YYYY-MM-DD HH:MM:SS.SSS format used by sqlite3
    
    Input: Seconds since the epoch (optionally including fractional seconds)
    Output: String of the format YYYY-MM-DD HH:MM:SS.SSS'''
    return datetime.datetime.utcfromtimestamp(seconds_since_epoch).strftime("%Y-%m-%d %H:%M:%S.%f")

def date_and_time_to_epoch(date_str, time_str):
    '''Converts a day and time (20130731,11:33:33.003) to seconds
    since the epoch
    
    Input:
    date_value: date in form YYYYMMDD (20130731)
    time_value: time in format HH:MM:SS.SSS (11:33:33.003)
    
    Returns: seconds since epoch (float)'''
    try:
        datetime_obj = datetime.datetime.strptime(date_str + time_str, "%Y%m%d%H:%M:%S.%f")
    except ValueError:
        datetime_obj = datetime.datetime.strptime(date_str + time_str, "%Y%m%d%H:%M:%S")

    
    return (datetime_obj - datetime.datetime(1970, 1, 1)).total_seconds()
    

