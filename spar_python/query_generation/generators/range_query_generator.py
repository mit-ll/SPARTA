# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Generates range queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  29 October 2013  ATLH            Original file
# *****************************************************************

"""
Query generator engine for range  related queries, includes double sided
ranges and greater than queries. 

"""

from __future__ import division 
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.query_generation.generators.query_object as query_object
import spar_python.query_generation.query_ids as qids
import spar_python.data_generation.spar_variables as sv
import spar_python.common.distributions.bespoke_distributions as bd
import spar_python.query_generation.BOQs.atomic_query_batches as aqb
import spar_python.query_generation.query_schema as qs
import logging

LOGGER = logging.getLogger(__name__)


#Dummy value for row width
OVER_GENERATION_RATIO = 2

class RangeQueryGenerator(query_object.QueryGenerator):
    '''
    Generates P2 queries
    '''
    
    def __init__(self, cat, sub_cat, perf, dists, fields, db_size, row_width, 
                 other_fields, other_cols):
        '''
        Args:
         *cat: P* of the query
         *sub_cat: the catagory of the query, all correspond to a type of 
                   query object
         *fields: the field that the query relies on, each has its own distribution
                  object in dists, in this case the field is always foo.
         *dists: the distribution objects that the query relies on in a list, this
                 case will always be foo
         *db_size: the size of the db being generated and run against
         *other_fields: [no_queries, rss_lower, rss_upper, range_exponent, type] 
                        where range_exponent is the range_size exponent and type is
                        either 'range' (two-sided), or 'greater' (one-sided)
         *other_cols: [[200, 1, 10, 5, 'range'],[100, 11, 100, 5, 'range'],...
       
        '''
        assert(len(fields)==len(dists))
        self.__perf = perf
        self.__cat = cat
        self.__sub_cat = sub_cat
        self.__fields = fields
        self.__dists = dict(zip(fields, dists))
        self.__db_size = db_size
        self.__row_width = row_width
        self.__queries = [dict(zip(other_fields, x)) for x in other_cols]
        self.__count = 0
        self.__total = len(fields) * sum([x[0] for x in other_cols]) *\
                       OVER_GENERATION_RATIO
        self.bobs = []
        self.__calculate_cdf()
    
    def __calculate_cdf(self):
        """
        Calculates the cdf values for the generate_cdf function
        """
        
        for template in self.__queries:
            template['rss_lower_cdf'] = (template[qs.QRY_LRSS] / self.__db_size)
            template['rss_upper_cdf'] = (template[qs.QRY_URSS] / self.__db_size)
                 
    def produce_query_batches(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        
        for (f, dist) in self.__dists.iteritems():
            for q in self.__queries:
                if q[qs.QRY_TYPE] == 'range':
                    self.bobs.append(self._generate_range_queries(f, dist, q))
                else:
                    self.bobs.append(self._generate_than_queries(f, dist, q))
        return self.bobs
                
    def _generate_range_queries(self, field, dist, q):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """

        query_dicts = []
        num_queries = 0
        for count in xrange(q['no_queries']*OVER_GENERATION_RATIO):
            num_queries = count
            self.__count += 1
            LOGGER.info('P2: Created %d out of %d queries' % (self.__count, 
                                                              self.__total))
            r_lower_cdf = q['rss_lower_cdf']
            r_upper_cdf = q['rss_upper_cdf'] 
            (lower, upper) = dist.generate_double_range(r_lower_cdf, r_upper_cdf,
                                                       db_size = self.__db_size)
            qid = qids.query_id()
            if field in [sv.VARS.INCOME, sv.VARS.LAST_UPDATED]:
                where_clause = '%s BETWEEN %s AND %s' % \
                                    (sv.sql_info[field][0], 
                                    sv.VAR_CONVERTERS[field].to_csv(lower),
                                    sv.VAR_CONVERTERS[field].to_csv(upper))
            else:
                where_clause = '%s BETWEEN \'\'%s\'\' AND \'\'%s\'\'' % \
                                    (sv.sql_info[field][0], 
                                    sv.VAR_CONVERTERS[field].to_csv(lower),
                                    sv.VAR_CONVERTERS[field].to_csv(upper))
            if qid != qids.full_where_has_been_seen(qid,where_clause):
                continue
            query_dicts.append({qs.QRY_ENUM : qs.CAT.P2_RANGE, 
                                qs.QRY_QID : qid,
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_CAT : self.__cat,
                                qs.QRY_SUBCAT : 'range', 
                                qs.QRY_WHERECLAUSE : where_clause,
                                qs.QRY_FIELD : sv.sql_info[field][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                qs.QRY_LRSS : q[qs.QRY_LRSS],
                                qs.QRY_URSS : q[qs.QRY_URSS],
                                qs.QRY_LBOUND : lower,
                                qs.QRY_UBOUND : upper,
                                qs.QRY_RANGE : 0
                                })
        
        return aqb.RangeQueryBatch(query_dicts, num_queries, 
                                    int((num_queries+1)/OVER_GENERATION_RATIO),
                                    True)   
        
    def _generate_than_queries(self, field, dist, q):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """

        query_dicts = []
        num_queries = 0
        for count in xrange(q['no_queries']*OVER_GENERATION_RATIO):
            num_queries = count
            self.__count += 1
            LOGGER.info('P2: Created %d out of %d queries' % (self.__count, self.__total))
            r_lower_cdf = q['rss_lower_cdf']
            r_upper_cdf = q['rss_upper_cdf'] 
            if q[qs.QRY_TYPE] == 'greater':
                value = dist.generate_greater_than(r_lower_cdf, r_upper_cdf,
                                                   db_size = self.__db_size)
                enum = qs.CAT.P2_GREATER
                if field in [sv.VARS.INCOME, sv.VARS.LAST_UPDATED]:
                    where_clause = '%s >= %s' % (sv.sql_info[field][0], 
                                        sv.VAR_CONVERTERS[field].to_csv(value))
                else:
                    where_clause = '%s >= \'\'%s\'\'' % (sv.sql_info[field][0], 
                                        sv.VAR_CONVERTERS[field].to_csv(value))
            else:
                value = dist.generate_less_than(r_lower_cdf, r_upper_cdf,
                                                db_size = self.__db_size)
                enum = qs.CAT.P2_LESS
                if field in [sv.VARS.INCOME, sv.VARS.LAST_UPDATED]:
                    where_clause = '%s <= %s' % (sv.sql_info[field][0], 
                                         sv.VAR_CONVERTERS[field].to_csv(value))
                else:
                    where_clause = '%s <= \'\'%s\'\'' % (sv.sql_info[field][0], 
                                         sv.VAR_CONVERTERS[field].to_csv(value))
            qid = qids.query_id()
            if qid != qids.full_where_has_been_seen(qid,where_clause):
                continue
            query_dicts.append({qs.QRY_ENUM : enum, 
                                qs.QRY_QID : qid,
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_CAT : self.__cat,
                                qs.QRY_SUBCAT : q[qs.QRY_TYPE], 
                                qs.QRY_WHERECLAUSE : where_clause,
                                qs.QRY_FIELD : sv.sql_info[field][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                qs.QRY_LRSS : q[qs.QRY_LRSS],
                                qs.QRY_URSS : q[qs.QRY_URSS],
                                qs.QRY_VALUE : value,
                                qs.QRY_RANGE : 0
                                })
        
        return aqb.RangeQueryBatch(query_dicts, num_queries, 
                                    int((num_queries+1)/OVER_GENERATION_RATIO),
                                    True)   
  
                         
    
