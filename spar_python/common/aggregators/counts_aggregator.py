# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        A class to count the number of rows fed to it
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  7 May 2013    jch            Original file
# *****************************************************************





import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.common.aggregators.base_aggregator \
    as base_aggregator


class CountsAggregator(base_aggregator.BaseAggregator):
    """
    A small helper class for counting rows generated. This can be though
    of as a minimal instance of the aggregator interface.
    
    """


    def __init__(self):
        '''
        Constructor. Currently does nothing.
        '''
        pass

    def map(self, row_dict):
        '''
        Returns 1.
        '''
        return 1

    @staticmethod
    def reduce(a, b):
        '''
        Returns the sum of the arguments.
        '''
        return a + b

    def fields_needed(self):
        return set()

    def done(self):
        pass
