# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Represents a single query type
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  1 August 2013  ATLH            Original file
# *****************************************************************

import abc

"""
This is the abstract class for the classes which will holds the logic
of how to interact with the distribution objects used in query generation
when given the associated request for a query. It is essentially the 
interpretor between the values held in the query schema and the functionality
of the distribution object. 
"""

class QueryGenerator(object):

    
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def __init__(self, cat, sub_cat, perf, dists, fields, db_size, row_width, other_fields,
                 other_cols):
        """
        All query objects have the same basic inputs when initialized:
        * cat: P* associated with the query.
        
        * sub_cat: the sub_catagory that the query_object represents, 
          the list of the available ones can be found testing plan
        
        * dists: a list of distribution object(s) that the query object 
          must generate from, each distribution ojbect has an associated
          entry in the fields argument
          
        * fields: a list of fields that the query object must generate
          from, each relates to a distribution object at the same indice
          in the dists argument
          
        * db_size: the size of the database the queries are being 
          generated for 
          
        * db_size: the size of the database rows the queries are being
          generated for
          
        * **args: whatever other information is needed to generate enough
          queries, this varies for each separate type of QueryObject.

        """
        pass
    
    @abc.abstractmethod
    def produce_query_batches(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        pass
