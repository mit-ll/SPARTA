# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Generates P6 and P7 queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  21 August 2013  ATLH            Original file
# *****************************************************************

"""
Takes in a field, and associated distribution, a list of ranges and 
corresponding number of queries. Using that information it determines
what the pdf value is for each range for that field is calculated 
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
import spar_python.common.spar_random as spar_random
import math
import spar_python.query_generation.query_schema as qs
import spar_python.query_generation.BOQs.atomic_query_batches as aqb
import logging

LOGGER = logging.getLogger(__name__)

OVER_GENERATION_RATIO = 2

class WildcardQueryGenerator(query_object.QueryGenerator):
    """
    Generate P6 & P7 queries
    """
           
    def __init__(self, cat, sub_cat, perf, dists, fields, db_size, row_width, other_fields,
                 other_cols):
        '''
        Args:
         *cat: Category of the query, in this case P6 or P7
         *sub_cat: the sub_category of the query, for P6: 'initial-one', 'middle-one','final-one'
                   and 'middle-many', and for P7: 'initial','both','final'
         *fields: the field that the query relies on, each has its own distribution
                  object in dists
         *dists: the distribution objects that the query relies on in a list 
         *db_size: the size of the db being generated and run against
         *other_fields: ['no_queries','r_lower','r_upper',keyword_len','type'] OR
                        [no_queries, rss, key_word_len, type] 
         *other_cols: [[10,10,100,8,'initial-one'],[10,10,100,8,'middle-one'],... OR
                      [[10,100,8,'initial-one'],[10,100,8,'middle-one'],....
       
        '''

        assert(len(fields)==len(dists))
        self.__perf = perf
        self.__cat = cat
        self.__sub_cat = sub_cat
        self.__fields = fields
        self.__dists = dict(zip(fields, dists))
        self.__db_size = db_size
        self.__row_width = row_width
        self.__query_temp = [dict(zip(other_fields, x)) for x in other_cols]
        self.__queries = []
        self.__bobs = []
        self.__count = 0
        self.__total = len(fields) * sum([x[0] for x in other_cols]) *\
                       OVER_GENERATION_RATIO

        
    def __format_search_exp_sql(self, f, value, string_type, length):
        """
        Converts the generated values into sql and reg expression format
        """
        def _format_sql(value):
            '''
            Specific format for sql 
            '''
            return value.replace('\'',"\\'")
        def _format_exp(value):
            '''
            Specific format for search expression
            '''
            return value.replace('.',"\.") 
        
        field = sv.sql_info[f][0]
        search_exp = None
        search_exp_front = None
        search_exp_back = None 
        if self.__cat == 'P6':
            if string_type == 'initial-one':
                sql = "%s LIKE ''_%s''" % (field, _format_sql(value[1:]))
                search_exp = _format_exp(value[1:])
                enum = qs.CAT.P6_INITIAL_ONE          
            elif string_type == 'middle-one':
                assert len(value) >= 9
                offset = spar_random.randint(4, len(value)-5)
                sql = "%s LIKE ''%s_%s''"% (field, _format_sql(value[:offset]), 
                                             _format_sql(value[offset+1:]))
                search_exp_front = _format_exp(value[:offset]) 
                search_exp_back = _format_exp(value[offset+1:])
                enum = qs.CAT.P6_MIDDLE_ONE
            elif string_type == 'final-one':
                sql = "%s LIKE ''%s_''" % (field, _format_sql(value[:-1]))
                search_exp = _format_exp(value[:-1])
                enum = qs.CAT.P6_FINAL_ONE
            else:
                raise Exception
            
        elif self.__cat == 'P7':
            if string_type == 'initial':
                enum = qs.CAT.P7_INITIAL
                if (f <= sv.VARS.NOTES4) and (f >= sv.VARS.NOTES1):
                    diff = len(value) - length + 2
                    sql = "%s LIKE ''%%%s.''" % (field, \
                                                 _format_sql(value[diff:]))
                    search_exp = '%s.' % (_format_exp(value[diff:]))
                else:
                    diff = len(value) - length - 1
                    sql = "%s LIKE ''%%%s''" % (field, 
                                                _format_sql(value[diff:]))
                    search_exp = _format_exp(value[diff:])
            elif string_type == 'both':
                enum = qs.CAT.P7_BOTH
                diff = len(value) - length
                start_offset = int(math.floor(diff/2.0))+1
                end_offset = int(math.ceil(diff/2.0))+1
                sql = "%s LIKE ''%%%s%%''" % (field, 
                            _format_sql(value[start_offset:-end_offset]))
                search_exp = _format_exp(value[start_offset:-end_offset])
            elif string_type == 'final':
                enum = qs.CAT.P7_FINAL
                diff = len(value) - length + 2
                sql = "%s LIKE ''%s%%''" % (field, _format_sql(value[:-diff]))
                search_exp = _format_exp(value[:-diff])
            else:
                raise Exception
        else:
            raise Exception
    
        return (sql, search_exp, search_exp_front, search_exp_back, enum)
    
    def __length_to_gen(self, f, t):
        """
         Specifies the len of the thing we are attempting to 
         generate
        """
        string_type = t['type']
        
        if string_type in ['middle-many', 'initial', 'final']:
            return t['keyword_len'] + spar_random.randint(2, 4)
        
        elif string_type =='both' and f != sv.VARS.FIRST_NAME and \
          f != sv.VARS.LAST_NAME:
            
            return t['keyword_len'] + spar_random.randint(4, 6)
        
        else:
            
            return t['keyword_len']
    
    def __non_note_queries(self, f, dist):
        """
        Generates the queries for non note fields
        """
        for t in self.__query_temp:
            query_dicts = []
            for _ in xrange(t['no_queries']*OVER_GENERATION_RATIO):
                self.__count += 1
                LOGGER.info('P6/P7: Created %d out of %d queries'%(self.__count, 
                                                                 self.__total))
                if t.has_key('r_lower'):
                    r_lower = t['r_lower']/self.__db_size
                    r_upper = t['r_upper']/self.__db_size
                else:
                    r_lower = t['rss']/1.5/self.__db_size
                    r_upper = t['rss']*1.5/self.__db_size
                
                value = ""
                count = 0
                length = self.__length_to_gen(f, t)
                
                if self.__cat == 'P6':
                    comp = lambda x, y: x != y
                else:
                    comp = lambda x, y: x < y
                    
                while comp(len(value),length) and count < dist.size_pdf():
                    count += 1
                    value = dist.generate_pdf(r_lower, r_upper, {})
                    
                if comp(len(value),length):
                    continue
                (where_clause, value, value_front, value_back, enum) = \
                                    self.__format_search_exp_sql(f, value, 
                                                                 t['type'],
                                                          t['keyword_len'])
                if t.has_key(qs.QRY_RSS):
                    rss = t[qs.QRY_RSS]
                    lrss = 0
                    urss = 0
                else:
                    rss = 0
                    lrss = t[qs.QRY_LRSS]
                    urss = t[qs.QRY_URSS]
                qid = qids.query_id()
                if qid != qids.full_where_has_been_seen(qid,where_clause):
                    continue
                query_dicts.append({
                        qs.QRY_ENUM : enum, 
                        qs.QRY_QID : qid,
                        qs.QRY_CAT : self.__cat, 
                        qs.QRY_SUBCAT : t['type'], 
                        qs.QRY_DBNUMRECORDS : self.__db_size,
                        qs.QRY_DBRECORDSIZE : self.__row_width,
                        qs.QRY_PERF : self.__perf,
                        qs.QRY_FIELD: sv.sql_info[f][0],
                        qs.QRY_FIELDTYPE : sv.sql_info[f][1],
                        qs.QRY_WHERECLAUSE : where_clause,
                        qs.QRY_RSS : rss,
                        qs.QRY_LRSS : lrss,
                        qs.QRY_URSS : urss,
                        qs.QRY_KEYWORDLEN : t['keyword_len'],
                        qs.QRY_SEARCHFOR : value,
                        qs.QRY_SEARCHFORLIST : [value_front, value_back],
                        qs.QRY_SEARCHDELIMNUM : 1 })
            if query_dicts != []:
                self.__bobs.append(aqb.WildcardQueryBatch(query_dicts, 
                                                          len(query_dicts),
                                                          t['no_queries'], 
                                                          True))
    
    def __notes_queries(self, f, dist):
        """
        Generates the queries for note fields
        """
        for t in self.__query_temp:
            query_dicts = []
            for _ in xrange(t['no_queries']*OVER_GENERATION_RATIO):
                self.__count += 1
                LOGGER.info('P6/P7: Created %d out of %d queries' % \
                                        (self.__count, self.__total))
                length = self.__length_to_gen(f, t)
                if t.has_key('r_lower'):
                    r_lower = t['r_lower']/self.__db_size
                    r_upper = t['r_upper']/self.__db_size
                else:
                    r_lower = t['rss']/1.5/self.__db_size
                    r_upper = t['rss']*1.5/self.__db_size
                
                value = ""
                count = 0
                while len(value) < length and \
                        count < dist.trigram_cardinality():
                    count += 1
                    value = dist.generate_trigram(r_lower, r_upper)
                if len(value) < length:
                    continue
                (where_clause, value, value_front, value_back, enum) = \
                                     self.__format_search_exp_sql(f, value, 
                                                                  t['type'],
                                                          t['keyword_len'])
                if t.has_key(qs.QRY_RSS):
                    rss = t[qs.QRY_RSS]
                    lrss = 0
                    urss = 0
                else:
                    rss = 0
                    lrss = t[qs.QRY_LRSS]
                    urss = t[qs.QRY_URSS]
                qid = qids.query_id()
                if qid != qids.full_where_has_been_seen(qid,where_clause):
                    continue
                query_dicts.append({ 
                        qs.QRY_ENUM : enum, 
                        qs.QRY_QID : qid,
                        qs.QRY_CAT : self.__cat, 
                        qs.QRY_SUBCAT : t['type'], 
                        qs.QRY_DBNUMRECORDS : self.__db_size,
                        qs.QRY_DBRECORDSIZE : self.__row_width,
                        qs.QRY_PERF : self.__perf,
                        qs.QRY_FIELD: sv.sql_info[f][0],
                        qs.QRY_FIELDTYPE : sv.sql_info[f][1],
                        qs.QRY_WHERECLAUSE : where_clause,
                        qs.QRY_TYPE : t['type'],
                        qs.QRY_RSS : rss,
                        qs.QRY_LRSS : lrss,
                        qs.QRY_URSS : urss,
                        qs.QRY_KEYWORDLEN : t['keyword_len'],
                        qs.QRY_SEARCHFOR : value,
                        qs.QRY_SEARCHFORLIST : [value_front, value_back],
                        qs.QRY_SEARCHDELIMNUM : 1 })
            if query_dicts != []:   
                self.__bobs.append(aqb.WildcardQueryBatch(query_dicts,
                                                          len(query_dicts),
                                                    t['no_queries'],True))
   
     
    def __generate_queries(self):
        """
        Manages the queries for the three different types of fields for P6&P7
        """

        for (f, dist) in self.__dists.iteritems():
            if (f >= sv.VARS.NOTES1 and f <= sv.VARS.NOTES4):
                self.__notes_queries(f, dist)
            else:
                self.__non_note_queries(f, dist) 
                                            
    def produce_query_batches(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        self.__generate_queries()
        return self.__bobs

    
  
