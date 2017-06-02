# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Generates P9 alarm word queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 November 2013  ATLH            Original file
# *****************************************************************

"""
Takes in a field, and associated distribution, a list of ranges and 
corresponding number of queries. Using that information it determines
what the cdf value is for each range for that field is calculated 
"""
from __future__ import division 
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import spar_python.query_generation.generators.query_object as query_object
import spar_python.query_generation.query_ids as qids
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import spar_python.query_generation.BOQs.atomic_query_batches as aqb
import spar_python.common.spar_random as spar_random
import logging 

LOGGER = logging.getLogger(__name__)

OVER_GENERATION_RATIO = 2

class AlarmQueryGenerator(query_object.QueryGenerator):
    
    def __init__(self, cat, sub_cat, perf, dists, fields, db_size, row_width, other_fields,
                 other_cols):
        '''
        Args:
         *sub_cat: the catagory of the query, all correspond to a type of 
                   query object
         *fields: the field that the query relies on, each has its own distribution
                  object in dists
         *dists: the distribution objects that the query relies on in a list 
         *db_size: the size of the db being generated and run against
         *other_fields: [no_queries, rss_lower, rss_upper, distance] 
         *other_cols: [[5, 1, 10, 50],[5,1,10,50]]
       
        '''
        self.__cat = cat
        self.__sub_cat = sub_cat
        self.__fields = fields
        self.__dists = dict(zip(fields, dists))
        self.__db_size = db_size
        self.__row_width = row_width
        self.__queries = [dict(zip(other_fields,x)) for x in other_cols]
        self.__count = 0
        self.__total = len(fields) * sum([x[0] for x in other_cols]) *\
                       OVER_GENERATION_RATIO
        self.__perf = perf
        self.__bobs = []
                                                
    def produce_query_batches(self):
        self._generate_queries()
        return self.__bobs
    
    def _generate_queries(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        query_dicts = []
        for (field, dist) in self.__dists.iteritems():
            for q_template in self.__queries:
                query_dicts = []
                for count in xrange(q_template['no_queries']*\
                                    OVER_GENERATION_RATIO):
                    self.__count += 1
                    LOGGER.info('P9: Created %d out of %d queries' % \
                                (self.__count, self.__total))
                    lrss = (q_template[qs.QRY_LRSS]/self.__db_size)
                    urss = (q_template[qs.QRY_URSS]/self.__db_size)
                    (word_one, word_two) = dist.generate_alarmword(lrss, urss)
                    where = 'WORD_PROXIMITY(%s, \'\'%s\'\', \'\'%s\'\')' % \
                                        (sv.sql_info[field][0],
                                         word_one, word_two)
                    where_clause = "%s <= %d ORDER BY %s" % (where, q_template['distance'], where)
                    qid = qids.query_id()
                    if qid != qids.full_where_has_been_seen(qid,where_clause):
                        continue
                    query_dicts.append({ 
                           qs.QRY_ENUM : qs.CAT.P9_ALARM_WORDS,
                           qs.QRY_QID : qid,
                           qs.QRY_CAT : self.__cat, 
                           qs.QRY_SUBCAT : 'alarm-words', 
                           qs.QRY_DBNUMRECORDS : self.__db_size,
                           qs.QRY_DBRECORDSIZE : self.__row_width,
                           qs.QRY_PERF : self.__perf,
                           qs.QRY_FIELD: sv.sql_info[field][0],
                           qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                           qs.QRY_WHERECLAUSE : where_clause,
                           qs.QRY_LRSS : q_template[qs.QRY_LRSS],
                           qs.QRY_URSS : q_template[qs.QRY_URSS],
                           qs.QRY_ALARMWORDONE : word_one,
                           qs.QRY_ALARMWORDTWO : word_two,
                           qs.QRY_ALARMWORDDISTANCE : q_template['distance']})

                self.__bobs.append(aqb.AlarmQueryBatch(query_dicts, count,
                                                       int(count/OVER_GENERATION_RATIO),
                                                       True))        
        return self.__bobs   

    
            
            
            
            
            
            
            
            
      

            
