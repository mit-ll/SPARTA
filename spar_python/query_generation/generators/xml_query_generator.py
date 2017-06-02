# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Generates xml queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  8 October 2013  ATLH            Original file
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
import spar_python.common.distributions.xml_generator as xg
import logging 

LOGGER = logging.getLogger(__name__)

OVER_GENERATION_RATIO = 2

#key is proportion of the total db-size that it can maximally represent
PDF_TO_FIELDS = { 
      0.0001 :  [sv.VARS.FIRST_NAME],
      0.001  :  [sv.VARS.FIRST_NAME],
      0.01   :  [sv.VARS.FIRST_NAME, sv.VARS.STATE,
                 sv.VARS.AGE],
      0.1    :  [sv.VARS.STATE, sv.VARS.RACE, sv.VARS.CITIZENSHIP, sv.VARS.AGE],
      0.5    :  [sv.VARS.SEX],
      1.0    :  [sv.VARS.SEX, sv.VARS.RACE, sv.VARS.CITIZENSHIP]  }



class XmlQueryGenerator(query_object.QueryGenerator):
    """
    Generates P11 queries
    """
    
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
         *other_fields: [no_queries, rss_lower, rss_upper, path_type] 
         *other_cols: [[5, 1, 10, 'full'],[5,1,10,'short']]
       
        '''
        assert(len(fields)==1)
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
        self.__perf = perf
        self.__bobs = []
                                                
    def produce_query_batches(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        self._generate_queries()
        return self.__bobs
    
        
    def _create_equality_leaf(self, dist, r_lower, r_upper): 
        '''
        Generates the values for a leaf for equality type queries
        '''   
        fields = PDF_TO_FIELDS[0.0001]
        for key in sorted(PDF_TO_FIELDS.keys(), reverse=False):
            if key < r_lower and r_lower > 0.0001:
                fields = PDF_TO_FIELDS[key]
            elif key >= r_lower:
                break 
        spar_random.shuffle(fields)
        field = fields[0]
        value = dist.generate_leaf_pdf(field, r_lower, r_upper)
        return (sv.sql_info[field][0], value)
        
    def _generate_short_queries(self, dist, q):
        '''
        Generates queries of the form .//LEAF
        '''
        query_dicts = []
        query_count = 0
        for count in xrange(q['no_queries']*OVER_GENERATION_RATIO):
            self.__count += 1
            query_cout = count
            LOGGER.info('P11: Created %d out of %d queries' % \
                        (self.__count, self.__total))
            r_lower = q[qs.QRY_LRSS]/(self.__db_size*xg.XML_DEPTH*xg.FAN_OUT)
            r_upper = q[qs.QRY_URSS]/(self.__db_size*xg.XML_DEPTH*xg.FAN_OUT)
            (field, value) = self._create_equality_leaf(dist, r_lower, r_upper)
            value = sv.VAR_CONVERTERS[sv.sql_name_to_enum(field)].to_csv(value)
            try:
                value = value.replace('\'', '\'\'')
            except TypeError:
                pass 
            except AttributeError:
                pass
            if field in ['foo', 'age', 'income']:
                where = "xml_value(xml,\'//%s\', %s)" % (field, value) 
            else:
                where = "xml_value(xml,\'//%s\', \'%s\')" % (field, value) 
            xpath = field  
            qid = qids.query_id()
            if qid != qids.full_where_has_been_seen(qid,where):
                continue
            query_dicts.append({qs.QRY_ENUM : qs.CAT.P11_SHORT, 
                                qs.QRY_QID : qid,
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_CAT : self.__cat,
                                qs.QRY_SUBCAT : 'eq-double-slash', 
                                qs.QRY_WHERECLAUSE : where,
                                qs.QRY_FIELD : sv.sql_info[sv.VARS.XML][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : 'string',
                                qs.QRY_LRSS : q[qs.QRY_LRSS],
                                qs.QRY_URSS : q[qs.QRY_URSS],
                                qs.QRY_VALUE : value,
                                qs.QRY_XPATH : xpath })
        return aqb.XmlQueryBatch(query_dicts, query_count, 
                                 max(int((query_count+1)/OVER_GENERATION_RATIO),1),
                                 True)
        
    def _generate_full_queries(self, dist, q):
        '''
        Generates queries of the form ./node1/node2/LEAF
        '''
        query_dicts = []
        for count in xrange(q['no_queries']*OVER_GENERATION_RATIO):
            self.__count += 1
            LOGGER.info('P11: Created %d out of %d queries' % \
                        (self.__count, self.__total))
            r_lower_total = q[qs.QRY_LRSS]/self.__db_size
            r_upper_total = q[qs.QRY_URSS]/self.__db_size
            branch_r_lower = pow(r_lower_total/xg.XML_DEPTH, 1.0/(xg.XML_DEPTH))
            branch_r_upper = pow(r_upper_total/xg.XML_DEPTH, 1.0/(xg.XML_DEPTH))
          
            tags = []
            for level in xrange(xg.XML_DEPTH-1):
                tags.append(dist.generate_node_pdf(level, branch_r_lower, 
                                                   branch_r_upper))
            tag_string = ''
            for tag in tags:
                tag_string += "/%s" % (tag)
            (field, value) = self._create_equality_leaf(dist, branch_r_lower, 
                                                        branch_r_upper)
         
            value = sv.VAR_CONVERTERS[sv.sql_name_to_enum(field)].to_csv(value)
            try:
                value = value.replace('\'', '\'\'')
            except TypeError:
                pass 
            except AttributeError:
                pass
            if field in ['foo', 'age', 'income']:
                where = "xml_value(xml,\'/xml%s/%s\',%s)" % (tag_string, 
                                                             field, value) 
            else:
                where = "xml_value(xml,\'/xml%s/%s\',\'%s\')" % (tag_string, 
                                                                 field, value) 
            
            xpath = ['xml']+tags
            xpath.append(field)   
            qid = qids.query_id()
            if qid != qids.full_where_has_been_seen(qid,where):
                continue
            query_dicts.append({qs.QRY_ENUM : qs.CAT.P11_FULL,  
                                qs.QRY_QID : qid,
                                qs.QRY_DBNUMRECORDS : self.__db_size,
                                qs.QRY_DBRECORDSIZE : self.__row_width, 
                                qs.QRY_CAT : self.__cat,
                                qs.QRY_SUBCAT : 'eq-full', 
                                qs.QRY_PERF : self.__perf,
                                qs.QRY_WHERECLAUSE : where,
                                qs.QRY_FIELD : sv.sql_info[sv.VARS.XML][0],
                                qs.QRY_NEGATE : False,
                                qs.QRY_FIELDTYPE : 'string',
                                qs.QRY_LRSS : q[qs.QRY_LRSS],
                                qs.QRY_URSS : q[qs.QRY_URSS],
                                qs.QRY_VALUE : value,
                                qs.QRY_XPATH : xpath })
        return aqb.XmlQueryBatch(query_dicts,count, max(int((count+1)/OVER_GENERATION_RATIO),1),
                                 True)
        
    def _generate_queries(self):
        """
        This generates returns a query_batch object that holds the logic
        for creating aggregators for the queries, and also contains the 
        logic for processing the results and printing the query
        """
        field = self.__fields[0]
        dist = self.__dists[field]
        for q in self.__queries:
            if q['path_type']=='short':
                bob = self._generate_short_queries(dist, q)
            else:
                bob = self._generate_full_queries(dist, q)
            self.__bobs.append(bob)
            
            
            
            
            
            
            
            
            
      

            
