# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JL
#  Description:        This code finds a time from a list_of_times that 
#                      corresponds with a certain percentile.  The
#                      time that will appear from this code will be the
#                      closest time from the given list that is from below
#                      the threshold of the percentile.  
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  26 July 2012  JL             Original Version
#  27 July 2012  JL             Added class and floor functions
#  28 July 2012  JL             Changed floor to ceil - 1
#  29 July 2012  JL             Changed class name and consequences of empty
#                               list
# *****************************************************************

# general imports:
import math

#A class function is used in order to ensure that the the list is sorted before
#the getPercentile function is used on it.  Once this class is applied to a
#list, the list will be sorted in increasing numerical order.  
class PercentileFinder:
    def __init__(self, list_of_times):
        self._times = list_of_times
        self._times.sort()
            
    def getPercentile(self, percentile):
        """
        This function is designed to find the time, t, that corresponds
        to the given percentile from the list_of_times. Given the list
        [10, 20, 30, 40] and asked to find the 50th percentile, the answer
        will be 20.
        """
        assert ((percentile > 0) and (percentile <= 100))
        if self._times == []:
            return None
        else:
            #The variable less_than_time is the amount of numbers in the
            #list_of_times that are less than the time at the given
            #percentile.
            #It has to be converted to float data type to ensure that
            #percentile/100 isn't simplified to zero.
            less_than_time = (float(percentile) / 100) * float(len(self._times))
            #less_than_time has to be converted back to integer data type
            #so that it will be recognized by the list function.
            #The math.ceil function rounds the float up and then 1 is
            #subtracted, which gives us a valid index.
            return self._times[int(math.ceil(less_than_time) - 1)]

            
       
       
    
    


