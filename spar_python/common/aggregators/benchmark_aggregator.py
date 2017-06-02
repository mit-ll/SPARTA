# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        A class for benchmarking pure generation
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  18 June 2013    jch            Original file
# *****************************************************************





import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.data_generation.aggregators.base_aggregator \
    as base_aggregator
import spar_python.data_generation.spar_variables as sv

class BenchmarkingAggregator(base_aggregator.BaseAggregator):
    """
    A small helper class for benchmarking runs. Causes the data-generation
    engine to generate all fields, but will do nothing with them.
    """


    def __init__(self):
        '''
        Constructor. Currently does nothing.
        '''
        pass

    def map(self, row_dict):
        '''
        Returns None.
        '''
        return None

    @staticmethod
    def reduce(a, b):
        '''
        Do nothing.
        '''
        pass

    def fields_needed(self):
        return set(sv.VARS.numbers_generator())

    def done(self):
        pass
