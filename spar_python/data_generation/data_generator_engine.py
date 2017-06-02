# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Generate a rows of data according to distributions
#                      from learn_distributions, and feed them to aggregators.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Sept 2012  jch            Original file, but derived from oliver's
#                               quick_data_gen/quick_data_gen.py
#  6 May 2013    jch            Module-level functions removed.
# *****************************************************************

"""
This module contains a data generator/aggregator class which will be used
to generate rows, feed rows to aggregators and get back row-level results,
and to reduce these row-level results into aggregate results.
"""

import copy
import logging

import spar_python.common.spar_random as spar_random
import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.generated_row as generated_row

LOGGER = logging.getLogger(__name__)


class DataGeneratorEngine(object):
    """
    A class for generating data rows, feeding them to aggregators, and managing
    both row-level and aggregate results from the aggregators.
    """

    # Notes on multiprocessing:
    #
    # See the mega comment in generate_data for the overview on how
    # multiprocessing works. The upshot for this module is that
    # workers will be creating and using instances of this class.
    

    #
    # Methods to be called on objects of this class
    #

    def __init__(self, options, dist_holder):
        
        self.dist_holder = dist_holder
        self.multiprocess = (options.num_processes > 1)
        self.aggregators = options.aggregators
            
        for agg in self.aggregators:
            agg.start()
            
        self.fields_to_gen = \
            self._select_fields_to_generate(dist_holder, self.aggregators)

    @staticmethod
    def _select_fields_to_generate(dist_holder, aggregators):
        """
        Given a dist_holder and a list of aggregators, determine the smallest
        list of fields which should be generated from the dist_holder in order
        to generate every field needed by every aggregator. The catch here is
        that we need to generate all fields listed (in dist_holder.var_order)
        *before* the last field needed by an aggregator. The reason is RNG state:
        in order to make sure that we generate values in a repeatable way,
        we need to ensure that the RNG is in the same state for a given field
        for each run. And currently, the only way to do this is to actually
        generate every field which comes before a needed one.
        """
        fields_needed = set()
        for agg in aggregators:
            new_fields = set(agg.fields_needed())
            fields_needed.update(new_fields) 

            
        dist_vars = copy.copy(dist_holder.var_order)
        # Take elements of the *back* of the list until we either
        # run out of elements or find one that we need
        dist_vars.reverse()
        while dist_vars:
            if dist_vars[0] in fields_needed:
                break
            else:
                dist_vars.pop(0)
        
        # Sanity check: are we going to generate all fields needed by the 
        # aggregators?
        
        missing_fields = fields_needed.difference(dist_vars)
        # We do not need the dist_holder to make the ID field
        missing_fields = missing_fields - set([sv.VARS.ID])
        error_message = \
            "Error: cannot generate needed fields %s" % missing_fields
        
        assert (not missing_fields), error_message
        
        dist_vars.reverse()
        return dist_vars
        


    def done(self):
        """
        Finalizes aggregators. Calls same-named method in all 
        registered aggregators. No return value.
        """
        # Note that we are ignoring any return values from the aggreators'
        # done() methods. If we ever change this in the future, be sure to 
        # update the documentation in common/base_aggregator.py to describe how
        # these return values are used. 
        
        for aggregator in self.aggregators:
            aggregator.done()        
        return
   
    
    #
    # And now the nitty-gritty of generating rows
    #


    def generate_and_aggregate_rows(self, row_id_seed_pairs):
        """
        Given a list of (row_id, seed) pairs,
        generate the rows, aggregate the results, return aggregate results.
        """
        
        rows = map(self.generate_row_dict, row_id_seed_pairs)

        this_batch_results = [aggregator.map_reduce_row_list(rows)
                              for aggregator in self.aggregators]
        
        return this_batch_results
        
        
    def generate_row_dict(self, row_id_seed_pair):
        """
        Given a (row_id, seed) pairt, generates a row with the given ID and 
        from the given seed, and returns it in a dictionary.
        """
        (row_id, seed) = row_id_seed_pair
        spar_random.seed(seed)
        row_dict = generated_row.GeneratedRow()
        dist_dict = self.dist_holder.dist_dict
        for var in self.fields_to_gen:
            dist = dist_dict[var]
            v = dist.generate(row_dict)
            row_dict[var] = v
        row_dict[sv.VARS.ID] = row_id
        return row_dict
