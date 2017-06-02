# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JL
#  Description:        This takes the results from one function and compares
#                      it to another and if the results all correspond in a
#                      predetermined way, the code will return True.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  31 July 2012  JL             Original Version
# *****************************************************************

#The percentile_finder is used to compare the lists at all possible percentiles
#to ensure the accuracy of the times.

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.common.percentile_finder as pf
from types import *

#The function is not predefined in order to allow for redefinition of
#comparison criteria.

def distribution_compare (function, a_list, b_list):
    """
    This function is designed to compare two lists of times using a criteria
    determined in the function.  It individually compares two elements of the
    lists and if the elements meet the criteria, then a value, True, is appended
    to the compare_list.  If all of the items in the compare_list are True,
    then True is returned.
    
    Simple use:

    import single_percentile_comparator as sp
    
    if:
        a_list = [1,2,3,4,5,6,7,8]
        b_list = [50,100,150,200,250,300,350,400]
        function() = sp.baa_criteria
    then:
        10 * 50 + 15 >= 1
        10 * 100 + 15 >= 2
        10 * 150 + 15 >= 3
        10 * 200 + 15 >= 4
        10 * 250 + 15 >= 5
        10 * 300 + 15 >= 6
        10 * 350 + 15 >= 7
        10 * 400 + 15 >= 8
    and:
        distribution_compare(sp.baa_criteria, a_list, b_list) returns True
    """
        
    #Every possible percentile needs to be checked,
    #which is why there is a range from 1 to 100.
        
    a_list_percentile_finder = pf.PercentileFinder(a_list)
    b_list_percentile_finder = pf.PercentileFinder(b_list)
    for i in range(1,101):
        if not function(a_list_percentile_finder.getPercentile(i),
                        b_list_percentile_finder.getPercentile(i)):
            return False
    return True

        
