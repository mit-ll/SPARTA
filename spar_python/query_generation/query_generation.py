# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Top-level program for generating queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  1 August 2012  ATLH            Original file
# *****************************************************************

"""
This module contains the top-level 'main' function for query-generation. It 
takes in distribution objects and a schema file as well as database. Once 
it unpacks the distribution objects, it builds 'Query Objects' around them 
which hold the logic to interact with the distribution given what is in the 
provided schema file. When the queries have been generated it returns a list
of query objects (dictionaries with predermined keys)
"""

import os
import sys

this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import learn_query_types as lqt
import query_handler as qh 
import time 
import spar_python.common.spar_random as spar_random

def query_generation(schema_file, logger, dist_holder, db_size, row_width, start_seed):
      
    start_time = time.time()
    #Create query_types around the distributions
    logger.info("Creating query generators.")
    seed = int(start_seed)
    spar_random.seed(seed)
    my_learner = lqt.Learner(dist_holder, schema_file, db_size, row_width)
    #feed them into a handler
    logger.info("Creating queries.")
    handler = qh.QueryHandler(my_learner.generate_query_objects())
    #runs all of the queries and outputs them
    query_sets = handler.run(logger)
    print "LEN OF QUERY_SETS is ", len(query_sets)
    elapsed_time = time.time() - start_time
    logger.info('Done generating queries. %d seconds elapsed' % elapsed_time)
    return query_sets

