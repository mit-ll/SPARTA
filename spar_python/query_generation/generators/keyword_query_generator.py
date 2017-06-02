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
Takes in a field, and associated distribution, a list of ranges and 
corresponding number of queries. Contains the logic to generate 
wildcard queries. 
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
import spar_python.query_generation.BOQs.atomic_query_batches as aqb
import spar_python.query_generation.query_schema as qs
import logging

logger = logging.getLogger(__name__)

NOTEFIELD_WEIGHTS =     { sv.VARS.NOTES1:75,
                          sv.VARS.NOTES2:12,
                          sv.VARS.NOTES3:10,
                          sv.VARS.NOTES4:2 }

#Dummy value for row width
OVER_GENERATION_RATIO = 2

class KeywordQueryGenerator(query_object.QueryGenerator):
  
    
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
         *other_fields: ['no_queries','r_lower','r_upper',keyword_len','type'] OR
                        [no_queries, rss, key_word_len, type]
         *other_cols: [[10,1,10,8,'word'],[10,1,10,7,'stem'],... OR
                      [[10,1,8,'word'],[10,1,8,'stem'],...
       
        '''
        
        self.__cat = cat  
        self.__sub_cat = sub_cat
        self.__perf = perf
        self.__fields = fields
        self.__dists = dict(zip(fields, dists))
        self.__db_size = db_size
        self.__row_width = row_width
        self.__queries = [dict(zip(other_fields,x)) for x in other_cols]
        self.__calculate_cdf()
        self.__count = 0
        self.__total = len(fields) * sum([x[0] for x in other_cols]) *\
                       OVER_GENERATION_RATIO
        
    def __calculate_cdf(self):
        """
        Calculates the cdf values for the generate_cdf function
        """
        
        for (f, dist) in self.__dists.iteritems():
            for dict in self.__queries:
               try: 
                   dict['rss_u_pdf']=min(1,(dict[qs.QRY_RSS]*1.5)/(self.__db_size*(NOTEFIELD_WEIGHTS[f])))
                   dict['rss_l_pdf']=min(1,(dict[qs.QRY_RSS]/1.5)/(self.__db_size*(NOTEFIELD_WEIGHTS[f])))
               except KeyError:
                   dict['rss_u_pdf']=min(1,(dict[qs.QRY_URSS])/(self.__db_size*(NOTEFIELD_WEIGHTS[f])))
                   dict['rss_l_pdf']=min(1,(dict[qs.QRY_LRSS])/(self.__db_size*(NOTEFIELD_WEIGHTS[f])))
                                               
    
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
                    self.__count += 1
                    logger.info('P3/P4: Created %d out of %d queries' % (self.__count, self.__total))
                    field = self.__fields[f]
                    r_u_pdf = self.__queries[q]['rss_u_pdf']
                    r_l_pdf = self.__queries[q]['rss_l_pdf']
                    kw_len = self.__queries[q][qs.QRY_KEYWORDLEN]
                    if self.__queries[q][qs.QRY_TYPE] == 'word':
                        enum = qs.CAT.P3
                        value = self.__dists[field].generate_word(kw_len, r_l_pdf, r_u_pdf)
                        where_clause = 'CONTAINED_IN(%s, \'\'%s\'\')' % (sv.sql_info[field][0],value.replace('\'',"\\'").lower())
                    else:
                        enum = qs.CAT.P4
                        (value,word) = self.__dists[field].generate_antistem(kw_len, r_l_pdf, r_u_pdf)
                        where_clause = 'CONTAINS_STEM(%s, \'\'%s\'\')' % (sv.sql_info[field][0], word.replace('\'',"\\'").lower())
                    try:
                        RSS = self.__queries[q][qs.QRY_RSS]
                        LRSS = int(self.__queries[q][qs.QRY_RSS]*1.1)
                        URSS = int(self.__queries[q][qs.QRY_RSS]/1.1)
                    except KeyError:
                        RSS = (self.__queries[q][qs.QRY_LRSS]+
                              self.__queries[q][qs.QRY_URSS])/2.0
                        LRSS = self.__queries[q][qs.QRY_LRSS]
                        URSS = self.__queries[q][qs.QRY_URSS]
                    
                    qid = qids.query_id()
                    if qid != qids.full_where_has_been_seen(qid,where_clause):
                            continue
                    query_dicts.append({ 
                           qs.QRY_ENUM : enum,
                           qs.QRY_QID : qid,
                           qs.QRY_CAT : self.__cat, 
                           qs.QRY_SUBCAT : '', 
                           qs.QRY_DBNUMRECORDS : self.__db_size,
                           qs.QRY_DBRECORDSIZE : self.__row_width,
                           qs.QRY_PERF : self.__perf,
                           qs.QRY_FIELD: sv.sql_info[field][0],
                           qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                           qs.QRY_WHERECLAUSE : where_clause,
                           qs.QRY_TYPE : self.__queries[q][qs.QRY_TYPE],
                           qs.QRY_RSS : RSS,
                           qs.QRY_LRSS : LRSS,
                           qs.QRY_URSS : URSS,
                           qs.QRY_KEYWORDLEN : kw_len,
                           qs.QRY_SEARCHFOR : value })

                self.bobs.append(aqb.KeywordQueryBatch(query_dicts, count,
                                                       int((count+1)/OVER_GENERATION_RATIO),
                                                       True))        
        return self.bobs    
                
