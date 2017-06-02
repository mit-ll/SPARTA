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
import spar_python.query_generation.BOQs.compound_query_batch as cqb
import spar_python.query_generation.BOQs.atomic_query_batches as aqb
import logging 
import math

logger = logging.getLogger(__name__)

#Dummy value for row width
DUMMY = 100
OVER_GENERATION_RATIO = 2
CLAUSE_OVER_GENERATION_RATIO = 3
TAIL = 'ZZZZZZZZZZZZZ'

class AndTA2QueryGenerator(query_object.QueryGenerator):
    
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
        assert(len(fields)==len(dists))
        self.__cat = cat
        self.__sub_cat = sub_cat
        self.__perf = perf
        self.__fields = fields
        self.__dists = dict(zip(fields, dists))
        self.__db_size = db_size
        self.__row_width = row_width
        self.__queries = [dict(zip(other_fields,x)) for x in other_cols]
        self.__count = 0
        self.__total = sum(x[0] for x in other_cols)  * OVER_GENERATION_RATIO
        self.__bobs = []
        

    def __generate_queries(self):
        """
        Manages the queries for the component clauses 
        """
        
        for q in self.__queries:
            query_dicts = []
            for count in xrange(int(q['no_queries']*OVER_GENERATION_RATIO)):
                self.__count += 1
                logger.info('P1-eq-and: Created %d out of %d queries' % (self.__count, self.__total))
                if q['range'] != "none":
                    query_dicts.append(self.range_eq(q))
                else:
                    query_dicts.append(self.compound_eq(q))
            self.__bobs.append(cqb.AndTA2QueryBatch(query_dicts,count,
                                           int(math.ceil(count/OVER_GENERATION_RATIO)),
                                           True))

    
    def range_eq(self, q):
        sub_bobs = []
        pdf_lower_total = q[qs.QRY_LRSS]/self.__db_size
        pdf_upper_total = q[qs.QRY_URSS]/self.__db_size
        pdf_lower = pow(pdf_lower_total,1.0/len(self.__dists))
        pdf_upper = pow(pdf_upper_total,1.0/len(self.__dists))
        for f in self.__fields[:-1]:
            dist = self.__dists[f] 
            if f in [sv.VARS.FIRST_NAME, sv.VARS.LAST_NAME]:
                sub_bobs.append(self._string_equality_queries(f, dist, pdf_lower, pdf_upper))
            else:
                sub_bobs.append(self._equality_queries(f, dist, pdf_lower, pdf_upper))
        
        f = self.__fields[-1]
        dist = self.__dists[f]
        if q['range'] == 'range':    
            sub_bobs.append(self._range_queries(f, dist, pdf_lower, pdf_upper))
        else:
            sub_bobs.append(self._than_queries(f, dist, pdf_lower, pdf_upper,q['range']))
            
        return {qs.QRY_ENUM : qs.CAT.P1_EQ_AND,
                qs.QRY_QID : qids.query_id(),
                qs.QRY_DBNUMRECORDS : self.__db_size,
                qs.QRY_DBRECORDSIZE : self.__row_width, 
                qs.QRY_PERF : self.__perf,
                qs.QRY_CAT : self.__cat,
                qs.QRY_SUBCAT : 'eq-and' if len(self.__dists) > 1 else q['range'], 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : q['r_lower'],
                qs.QRY_URSS : q['r_upper'],
                qs.QRY_NUMCLAUSES :  len(self.__dists), 
                qs.QRY_NUMTERMSPERCLAUSE : 1, 
                qs.QRY_FTMLOWER : 1,
                qs.QRY_FTMUPPER : self.__db_size, 
                qs.QRY_SUBBOBS : sub_bobs}
    
    def compound_eq(self, q):
        
        sub_bobs = []
        pdf_lower_total = q[qs.QRY_LRSS]/self.__db_size
        pdf_upper_total = q[qs.QRY_URSS]/self.__db_size
        pdf_lower = pow(pdf_lower_total,1.0/len(self.__dists))
        pdf_upper = pow(pdf_upper_total,1.0/len(self.__dists))
        for (f, dist) in self.__dists.iteritems(): 
            if f in [sv.VARS.FIRST_NAME, sv.VARS.LAST_NAME]:
                sub_bobs.append(self._string_equality_queries(f, dist, pdf_lower, pdf_upper))
            else:
                sub_bobs.append(self._equality_queries(f, dist, pdf_lower, pdf_upper))
            
        return {qs.QRY_ENUM : qs.CAT.P1_EQ_AND,
                qs.QRY_QID : qids.query_id(),
                qs.QRY_DBNUMRECORDS : self.__db_size,
                qs.QRY_DBRECORDSIZE : self.__row_width, 
                qs.QRY_PERF : self.__perf,
                qs.QRY_CAT : self.__cat,
                qs.QRY_SUBCAT : 'eq-and' if len(self.__dists) > 1 else '', 
                qs.QRY_WHERECLAUSE : '',
                qs.QRY_NEGATE : False,
                qs.QRY_LRSS : q['r_lower'],
                qs.QRY_URSS : q['r_upper'],
                qs.QRY_NUMCLAUSES :  len(self.__dists), 
                qs.QRY_NUMTERMSPERCLAUSE : 1, 
                qs.QRY_FTMLOWER : 1,
                qs.QRY_FTMUPPER : self.__db_size, 
                qs.QRY_SUBBOBS : sub_bobs}
            
                                                
    def produce_query_batches(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        self.__generate_queries()
        return self.__bobs
    
        
    def _string_equality_queries(self, field, dist, pdf_lower, pdf_upper):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """

        query_dicts = []
        for _ in xrange(CLAUSE_OVER_GENERATION_RATIO):
            value = self.__dists[field].generate_pdf(pdf_lower, pdf_upper, {})
            qid = qids.query_id()
            where = 'SUBSTR(%s,1,9) = \'\'%s\'\'' % (sv.sql_info[field][0], value[:9])
            query_dicts.append({qs.QRY_ENUM : qs.CAT.P7_FINAL, 
                                qs.QRY_QID : qids.full_where_has_been_seen(qid, where),
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_CAT : 'P7',
                                qs.QRY_SUBCAT : 'final', 
                                qs.QRY_WHERECLAUSE : where,
                                qs.QRY_FIELD : sv.sql_info[field][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                qs.QRY_KEYWORDLEN : 9,
                                qs.QRY_SEARCHFOR : value[:9],
                                qs.QRY_SEARCHDELIMNUM : 1 })
    
        return aqb.WildcardQueryBatch(query_dicts, CLAUSE_OVER_GENERATION_RATIO,
                                      1, False)     
    def _equality_queries(self, field, dist, pdf_lower, pdf_upper):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """

        query_dicts = []
        for x in xrange(CLAUSE_OVER_GENERATION_RATIO):
            value = self.__dists[field].generate_pdf(pdf_lower, pdf_upper, {})
            qid = qids.query_id()
            (value, where) = aqb.EqualityFishingQueryBatch.format_value_and_where(field, value)                       
            query_dicts.append({qs.QRY_ENUM : qs.CAT.EQ, 
                                qs.QRY_QID : qids.full_where_has_been_seen(qid, where),
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_CAT : 'EQ',
                                qs.QRY_SUBCAT : '', 
                                qs.QRY_WHERECLAUSE : where,
                                qs.QRY_FIELD : sv.sql_info[field][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                qs.QRY_VALUE : value})
    
        return aqb.EqualityQueryBatch(query_dicts, CLAUSE_OVER_GENERATION_RATIO,
                                      1, False)  
    def _range_queries(self, field, dist, pdf_lower, pdf_upper):
        query_dicts = []
        tail = 'ZZZZZZZZZZZZZ'
        for x in xrange(CLAUSE_OVER_GENERATION_RATIO):
            (lower, upper) = dist.generate_double_range(pdf_lower, pdf_upper,
                                                            db_size = self.__db_size)
            qid = qids.query_id()
            if field in [sv.VARS.INCOME, sv.VARS.LAST_UPDATED]:
                where_clause = '%s BETWEEN %s AND %s' % (sv.sql_info[field][0], 
                                                     sv.VAR_CONVERTERS[field].to_csv(lower),
                                                     sv.VAR_CONVERTERS[field].to_csv(upper))
            elif field in [sv.VARS.FIRST_NAME, sv.VARS.LAST_NAME]:
                where_clause = 'SUBSTR(%s,1,9) BETWEEN \'\'%s\'\' AND \'\'%s\'\'' % (sv.sql_info[field][0], 
                                                     sv.VAR_CONVERTERS[field].to_csv(lower)[:9],
                                                     sv.VAR_CONVERTERS[field].to_csv(upper)[:9])
                lower = sv.VAR_CONVERTERS[field].to_csv(lower)[:9]
                upper = sv.VAR_CONVERTERS[field].to_csv(upper)[:9]+TAIL
            else:
                where_clause = '%s BETWEEN \'\'%s\'\' AND \'\'%s\'\'' % (sv.sql_info[field][0], 
                                                     sv.VAR_CONVERTERS[field].to_csv(lower),
                                                     sv.VAR_CONVERTERS[field].to_csv(upper))
            query_dicts.append({qs.QRY_ENUM : qs.CAT.P2_RANGE, 
                                qs.QRY_QID : qids.full_where_has_been_seen(qid, where_clause),
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_CAT : 'P2',
                                qs.QRY_SUBCAT : 'range', 
                                qs.QRY_WHERECLAUSE : where_clause,
                                qs.QRY_FIELD : sv.sql_info[field][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                qs.QRY_LBOUND : lower,
                                qs.QRY_UBOUND : upper,
                                qs.QRY_RANGE : 0
                                })
    
        return aqb.RangeQueryBatch(query_dicts, CLAUSE_OVER_GENERATION_RATIO,
                                      1, False)  
           
    def _than_queries(self, field, dist, pdf_lower, pdf_upper, range_type):
        query_dicts = []
        for x in xrange(CLAUSE_OVER_GENERATION_RATIO):
            #generate the range specific aspects of the queries
            if range_type == 'greater':
                value = dist.generate_greater_than(pdf_lower, pdf_upper,
                                                   db_size = self.__db_size)
                enum = qs.CAT.P2_GREATER
                tail = ''
                comp = '>='
            else:
                value = dist.generate_less_than(pdf_lower, pdf_upper,
                                                db_size = self.__db_size)
                enum = qs.CAT.P2_LESS
                tail = TAIL
                comp = '<='
            #generate the where clauses    
            if field in [sv.VARS.INCOME, sv.VARS.LAST_UPDATED]:
                where_clause = '%s %s %s' % (sv.sql_info[field][0], comp,
                                             sv.VAR_CONVERTERS[field].to_csv(value))
            elif field in [sv.VARS.FIRST_NAME, sv.VARS.LAST_NAME]:
                
                where_clause = 'SUBSTR(%s,1,9) %s \'\'%s\'\'' % (sv.sql_info[field][0], comp, 
                                                 sv.VAR_CONVERTERS[field].to_csv(value)[:9])
                value = value + tail
            else:
                where_clause = '%s %s \'\'%s\'\'' % (sv.sql_info[field][0], comp,
                                             sv.VAR_CONVERTERS[field].to_csv(value))
            
            qid = qids.query_id()
            query_dicts.append({qs.QRY_ENUM : enum, 
                                qs.QRY_QID : qids.full_where_has_been_seen(qid, where_clause),
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_CAT : 'P2',
                                qs.QRY_SUBCAT : range_type,
                                qs.QRY_WHERECLAUSE : where_clause,
                                qs.QRY_FIELD : sv.sql_info[field][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                                qs.QRY_VALUE : value,
                                qs.QRY_RANGE : 0
                                })
        return aqb.RangeQueryBatch(query_dicts, CLAUSE_OVER_GENERATION_RATIO,
                                      1, False)   

            
