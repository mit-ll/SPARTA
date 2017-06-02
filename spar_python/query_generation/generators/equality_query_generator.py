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
import logging 

logger = logging.getLogger(__name__)

#Dummy value for row width
OVER_GENERATION_RATIO = 2
FISHING_FIELDS = [sv.VARS.STREET_ADDRESS,
                  sv.VARS.LAST_UPDATED, sv.VARS.SSN]

    
class EqualityQueryGenerator(query_object.QueryGenerator):
    
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
         *other_fields: [no_queries, rss_lower, rss_upper] 
         *other_cols: [[no_query, rss_lower, rss_upper],[no_query, rss_lower, ...
       
        '''
        assert(sub_cat == 'eq')
        assert(len(fields)==len(dists))
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
        self.__bobs = []
        
   
    def __calculate_cdf(self):
        """
        Calculates the cdf values for the generate_cdf function
        """
        
        for (f, dist) in self.__dists.iteritems():
            for dict in self.__queries:
               dict['rss_lower_cdf']=(dict[qs.QRY_LRSS]/self.__db_size)
               dict['rss_upper_cdf']=(dict[qs.QRY_URSS]/self.__db_size)

    def __generate_queries(self):
        """
        Manages the queries for the three different types of fields for P6&P7
        """

        for (f, dist) in self.__dists.iteritems():
            if f not in FISHING_FIELDS:
                self._equality_queries(f, dist)
            else:
                self._equality_fishing_queries(f,dist) 
                                            
    def produce_query_batches(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        self.__generate_queries()
        return self.__bobs
    

        
    def _get_fishing_values(self, f, dist, cdf_lower, cdf_upper):
        
        if f == sv.VARS.SSN:
            digits = len(str(self.__db_size))-1
            search_value = dist.generate_pdf(0,1)[:digits]
            lbound = None
            ubound = None
            enum = qs.CAT.EQ_FISHING_STR
            
        elif f == sv.VARS.STREET_ADDRESS:
            search_value = dist.generate_street_pdf(cdf_lower, cdf_upper, {})
            lbound = None
            ubound = None
            enum = qs.CAT.EQ_FISHING_STR
        
        elif f == sv.VARS.INCOME or f == sv.VARS.LAST_UPDATED:
            search_value = None
            value1 = dist.generate_pdf(cdf_lower, cdf_lower, {})
            value2 = dist.generate_pdf(cdf_upper, cdf_upper, {})
            lbound = min(value1,value2)
            ubound = max(value1,value2)
            enum = qs.CAT.EQ_FISHING_INT
        return (search_value, lbound, ubound, enum)
            
            
            
    def _equality_fishing_queries(self, f, dist):
        """
        Creates the logic for creating queries for fields with high entropy
        that cannot be generated before hand
        """
        query_dicts = []
        for q in xrange(len(self.__queries)):
            query_dicts = []
            for count in xrange(self.__queries[q]['no_queries']*OVER_GENERATION_RATIO):
                self.__count += 1
                logger.info('EQ: Created %d out of %d queries' % (self.__count, self.__total))
                field = f
                r_lower_cdf = self.__queries[q]['rss_lower_cdf']
                r_upper_cdf = self.__queries[q]['rss_upper_cdf'] 
                (search_value, lbound, ubound, enum) = \
                             self._get_fishing_values(f, dist, r_lower_cdf, r_upper_cdf)
                   
                query_dicts.append({qs.QRY_ENUM : enum, 
                                    qs.QRY_QID : qids.query_id(),
                                    qs.QRY_DBNUMRECORDS : self.__db_size,
                                    qs.QRY_DBRECORDSIZE : self.__row_width, 
                                    qs.QRY_PERF : self.__perf,
                                    qs.QRY_CAT : self.__cat,
                                    qs.QRY_SUBCAT : '', 
                                    qs.QRY_WHERECLAUSE : '',
                                    qs.QRY_FIELD : sv.sql_info[field][0],
                                    qs.QRY_NEGATE : False,
                                    qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                    qs.QRY_LRSS : self.__queries[q][qs.QRY_LRSS],
                                    qs.QRY_URSS : self.__queries[q][qs.QRY_URSS],
                                    qs.QRY_VALUE : None,
                                    qs.QRY_SEARCHFOR : search_value,
                                    qs.QRY_LBOUND : lbound,
                                    qs.QRY_UBOUND : ubound })
    
            self.__bobs.append(aqb.EqualityFishingQueryBatch(query_dicts,count, 
                                                    int((count+1)/OVER_GENERATION_RATIO),
                                                    True))   
        
    def _equality_queries(self, field, dist):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """

        query_dicts = []
        for q in xrange(len(self.__queries)):
            query_dicts = []
            for count in xrange(self.__queries[q]['no_queries']*OVER_GENERATION_RATIO):
                self.__count += 1
                logger.info('EQ: Created %d out of %d queries' % (self.__count, self.__total))
                r_lower_cdf = self.__queries[q]['rss_lower_cdf']
                r_upper_cdf = self.__queries[q]['rss_upper_cdf'] 
                value = self.__dists[field].generate_pdf(r_lower_cdf, r_upper_cdf, {})
                qid = qids.query_id()
                (value, where) = aqb.EqualityFishingQueryBatch.format_value_and_where(field, value)
                if qid != qids.full_where_has_been_seen(qid,where):
                     continue
                query_dicts.append({qs.QRY_ENUM : qs.CAT.EQ, 
                                    qs.QRY_QID : qid,
                                    qs.QRY_DBNUMRECORDS : self.__db_size,
                                    qs.QRY_DBRECORDSIZE : self.__row_width, 
                                    qs.QRY_PERF : self.__perf,
                                    qs.QRY_CAT : self.__cat,
                                    qs.QRY_SUBCAT : '', 
                                    qs.QRY_WHERECLAUSE : where,
                                    qs.QRY_FIELD : sv.sql_info[field][0],
                                    qs.QRY_NEGATE : False,
                                    qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                    qs.QRY_LRSS : self.__queries[q][qs.QRY_LRSS],
                                    qs.QRY_URSS : self.__queries[q][qs.QRY_URSS],
                                    qs.QRY_VALUE : value})
    
            self.__bobs.append(aqb.EqualityQueryBatch(query_dicts,count, 
                                                    int((count+1)/OVER_GENERATION_RATIO),
                                                    True))        

            
