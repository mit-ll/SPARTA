# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Example aggregators for compound queries
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  13 Aug 2013   jch            original file
# *****************************************************************




import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)


import abc
import collections
import logging

LOGGER = logging.getLogger(__name__)

import spar_python.common.aggregators.base_aggregator \
    as base_aggregator


CompoundResult = collections.namedtuple('CompoundResult', 
                                        ['top_level_result', 'sub_results'])


class BooleanCollector(base_aggregator.BaseAggregator):
    """
    Example aggregator for a Boolean aggregator: one which 
    manages a list of sub-aggregators and will return the row-IDs collected
    by all/any of them. Each sub-aggregator needs to be a collector:
    
    * map(row) should return set([row_id]) if the row matches, empty set
    otherwise.
    
    * reduce(result1, result2) should return the union of reduce1 and reduce2
    """
    __metaclass__ = abc.ABCMeta


    def __init__(self, sub_aggregators):
        '''
        `sub_aggregators` should be a list of aggregators matching the
        sub-terms of the compound match.
        '''
        self.sub_aggregators = sub_aggregators



    def fields_needed(self):
        individual_answers = [set(agg.fields_needed()) 
                              for agg in self.sub_aggregators]
        return set.union(*individual_answers)

    @abc.abstractmethod
    def _extract_top_level_result(self, sub_answers):
        pass

    def map(self, row_dict):
        sub_answers = [agg.map(row_dict) for agg in self.sub_aggregators]
        LOGGER.debug("sub_answers: %s", sub_answers)

        def sub_answer_as_set(sub_answer):
            try:
                return sub_answer.top_level_result
            except AttributeError:
                return sub_answer
        
        sub_answers_as_sets = [sub_answer_as_set(sa) 
                               for sa in sub_answers]
        LOGGER.debug("sub_answers_as_sets: %s", sub_answers_as_sets)

        
        top_level_answer = self._extract_top_level_result(sub_answers_as_sets)
        return CompoundResult(top_level_answer, sub_answers)
                
                    
    def reduce(self, result1, result2):

        triples = zip(self.sub_aggregators, 
                     result1.sub_results, 
                     result2.sub_results)

        new_subs = [agg.reduce(r1, r2) for (agg, r1, r2) in triples]

        new_top = result1.top_level_result | result2.top_level_result
        return CompoundResult(new_top, new_subs)



class ConjunctiveCollector(BooleanCollector):
    
    def _extract_top_level_result(self, sub_answers):
        return set.intersection(*sub_answers)
    
    



class DisjunctiveCollector(BooleanCollector):
    
    def _extract_top_level_result(self, sub_answers):
        return set.union(*sub_answers)
        

    