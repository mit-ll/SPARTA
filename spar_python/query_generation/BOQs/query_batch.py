# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH 
#  Description:        Represents a single query batch
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  4 September 2013  ATLH            Original file
# *****************************************************************

import abc
import spar_python.query_generation.query_schema as qs

"""
This class represents the vertical integration of creating aggregators
for queries, refining the queries within the batch, and writing the
selected queries and their results to the results database within one
object. 
"""

class QueryBatch(object):

    
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def __init__(self, *args):
        """
        Queries, and args needed to initialize that BOQ
        """
        pass
    
    @abc.abstractmethod
    def produce_queries(self):
        """
        Returns the query dicts that the bob is based around, used primarily
        for debugging purposes
        """
        pass
        
    @abc.abstractmethod
    def make_aggregator(self):
        """
        Returns a gen_choose aggregator which wraps the associated 
        aggregators for the queries contained in the query batch
        """
        pass
    @abc.abstractmethod
    def refine_queries(self, agg_result):
        """
        Takes in the results of the aggregators and refines queries. 
        Selects which queries should be recorded in the results database. 
        To discard a query it simple does not add it to the refined list of 
        queries and their results. It then sets that equal to self.refined_queries_results. 
        It also returns a list of the refined queries and their results, which 
        can be ignored or used at top level.
        """
        pass
    
    @abc.abstractmethod
    def process_results(self, agg_results, db_object, query_file_handle, refined_queries = None):
        """
        Takes in the aggregator results, with those results, determines
        which queries in the batch are 'interesting' it then instantiates
        query_results for those queries and uses it to write it to the 
        results database. 
        
        Refine arguement is a list of already refined queries if the user 
        does not wish to rely on the pre-defined refine queries function
        """
        
    @staticmethod
    def _print_query(q, query_file_handler):
        """
        Prints passed in query in specific format to the passed in file.
        This is here so that it can toggle between * and id easily for now
        """
        sql_line = '%d SELECT * FROM main WHERE %s\n' % \
                        (q[qs.QRY_QID], q['where_clause'].replace('\'\'','\''))
        query_file_handler.write(sql_line)
    
