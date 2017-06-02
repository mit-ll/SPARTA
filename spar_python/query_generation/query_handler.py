# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Generates all the calculated queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  2 August 2013  ATLH            Original file
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.query_generation.query_schema as qs
import spar_python.query_generation.query_ids as qids
"""
Takes in a list of query_object and generates/outputs them until they return 
none and then it moves onto the next until all in the list are done. It writes 
the results of these to a csv file as specified by the user on the command line.
"""

class QueryHandler(object):
    
    def __init__(self,query_objects):
        """
        Args:
          *query_objects: list of query objects that will generate
                          the queries
          *file: file to print the queries to 
        """
        
        self.__query_obj = query_objects

    def run(self, logger):
        """
        Runs through list of query_generators and creates list of 
        queries, then returns that list. 
        """
        query_batches = []
        count = 0
        for qobject in self.__query_obj:
            count += 1
            logger.info('Processed %d out of %d query objects' 
                            % (count, len(self.__query_obj)))
            query_batches += qobject.produce_query_batches()
        queries = qids.total_num_queries()
        logger.info("%d total queries created" % queries)  
        return query_batches


