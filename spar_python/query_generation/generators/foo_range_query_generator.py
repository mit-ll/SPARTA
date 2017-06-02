# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Generates equality queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  2 August 2013  ATLH            Original file
# *****************************************************************

"""
Query generator engine for foo related queries, includes double sided
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

logger = logging.getLogger(__name__)


#Dummy value for row width
OVER_GENERATION_RATIO = 2
class FooRangeQueryGenerator(query_object.QueryGenerator):
    
    def __init__(self, cat, sub_cat, perf, dists, fields, db_size, row_width, other_fields,
                 other_cols):
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
        assert(sub_cat == 'foo-range' or sub_cat == 'foo-greater')
        assert(len(fields)==1 and fields[0]==sv.VARS.FOO)
        assert(len(fields)==len(dists))
        self.__perf = perf
        self.__cat = cat
        self.__sub_cat = sub_cat
        self.__fields = fields
        self.__dists = dict(zip(fields, dists))
        self.__db_size = db_size
        self.__row_width = row_width
        self.__queries = [dict(zip(other_fields,x)) for x in other_cols]
        self.__count = 0
        self.__total = len(fields) \
                        * sum([(q[qs.QRY_RANGEEXPU]-q[qs.QRY_RANGEEXPL])*q['no_queries'] 
                                                                for q in self.__queries])\
                        * OVER_GENERATION_RATIO
        
    def produce_query_batches(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        
        self.bobs = []
        query_dicts = []
        for f in xrange(len(self.__dists)):
            for q in xrange(len(self.__queries)):
                query_dicts = []
                for count in xrange(self.__queries[q]['no_queries']*OVER_GENERATION_RATIO):
                    for r in xrange(self.__queries[q][qs.QRY_RANGEEXPL],
                                    self.__queries[q][qs.QRY_RANGEEXPU]+1):
                        self.__count += 1
                        logger.debug('P2-foo: Created %d out of %d queries' % (self.__count, self.__total))
                        field = sv.sql_info[self.__fields[f]][0]
                        rss_lower = self.__queries[q][qs.QRY_LRSS]
                        rss_upper = self.__queries[q][qs.QRY_URSS]
                        rss_avg = (rss_lower + rss_upper) / 2
                        range = 2**r
                        if self.__queries[q][qs.QRY_TYPE] == 'range':
                            try:
                                (lower, upper) = self.__dists[self.__fields[f]].generate_two_sided(
                                                            rss_avg, range, self.__db_size)
                            except bd.FooInputs:
                                (lower, upper) = (0,0)
                            enum = qs.CAT.P2_RANGE_FOO
                            where_clause = '%s BETWEEN %d AND %d' % (field, lower, upper)
                        else:
                            try:
                                lower = self.__dists[self.__fields[f]].generate_greater_than(
                                                                rss_avg, self.__db_size)
                            except bd.FooInputs:
                                lower = 0
                            upper = 2**64 - 1
                            enum = qs.CAT.P2_GREATER_FOO
                            where_clause = '%s >= %d' % (field, lower)
                        qid = qids.query_id()
                        if qid != qids.full_where_has_been_seen(qid,where_clause):
                            continue
                        query_dicts.append({ 
                          qs.QRY_ENUM : enum,
                          qs.QRY_QID : qid,
                          qs.QRY_CAT : self.__cat,
                          qs.QRY_SUBCAT: self.__queries[q][qs.QRY_TYPE],
                          qs.QRY_DBNUMRECORDS : self.__db_size,
                          qs.QRY_DBRECORDSIZE : self.__row_width,
                          qs.QRY_PERF : self.__perf,
                          qs.QRY_WHERECLAUSE : where_clause, 
                          qs.QRY_FIELD : field,
                          qs.QRY_FIELDTYPE : sv.sql_info[self.__fields[f]][1],
                          qs.QRY_TYPE : self.__queries[q][qs.QRY_TYPE],
                          qs.QRY_LRSS : rss_lower,
                          qs.QRY_URSS : rss_upper,
                          qs.QRY_RANGEEXP : r,
                          qs.QRY_LBOUND : lower,
                          qs.QRY_UBOUND : upper,
                          qs.QRY_RANGE : upper-lower
                          })        
     
                self.bobs.append(aqb.FooRangeQueryBatch(query_dicts,len(query_dicts),
                                                        int(len(query_dicts)/OVER_GENERATION_RATIO),
                                                        True))        
        return self.bobs   
                         
    
