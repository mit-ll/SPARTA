# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH 
#  Description:        Represents a equality query batch
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  4 September 2013  ATLH            Original file
# *****************************************************************


from __future__ import division 
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.query_generation.BOQs.query_batch as query_batch
import spar_python.query_generation.query_result as qr
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.data_generation.spar_variables as sv
import spar_python.query_generation.query_ids as qids
import spar_python.common.aggregators.query_aggregator as qa
import spar_python.query_generation.query_schema as qs
import logging
import abc
import spar_python.common.spar_random as random
import collections as c  
import spar_python.query_generation.query_bounds as qbs

logger = logging.getLogger(__name__)

Q_CLASS = c.namedtuple('Q_class',['aggregator','result_class'])                                                                   
                                                                                                                                              
CAT_TO_CLASSES = {  qs.CAT.EQ : Q_CLASS(qa.EqualityQueryAggregator, qr.EqualityQueryResult),                                                                                  
                    qs.CAT.EQ_FISHING_INT : Q_CLASS(qa.RangeFishingQA, qr.EqualityQueryResult),                                                                                  
                    qs.CAT.EQ_FISHING_STR : Q_CLASS(qa.SearchFishingQA, qr.EqualityQueryResult),                                                                                  
                    qs.CAT.P1_EQ_AND : Q_CLASS(qa.AndQueryAggregator, None),                                                                                                   
                    qs.CAT.P1_EQ_OR : Q_CLASS(qa.OrQueryAggregator, None),                                                                                                                                                                                                       
                    qs.CAT.P2_RANGE_FOO : Q_CLASS(qa.RangeQueryAggregator, qr.P2QueryResult),                                                                                                                                                                                          
                    qs.CAT.P2_GREATER_FOO : Q_CLASS(qa.RangeQueryAggregator, qr.P2QueryResult),
                    qs.CAT.P2_LESS : Q_CLASS(qa.LessThanQueryAggregator, qr.P2QueryResult),
                    qs.CAT.P2_RANGE : Q_CLASS(qa.RangeQueryAggregator, qr.P2QueryResult),
                    qs.CAT.P2_GREATER : Q_CLASS(qa.GreaterThanQueryAggregator, qr.P2QueryResult),                                                                                        
                    qs.CAT.P3 : Q_CLASS(qa.P3P4QueryAggregator, qr.P3P4P6P7QueryResult),                                                                                  
                    qs.CAT.P4 : Q_CLASS(qa.P3P4QueryAggregator, qr.P3P4P6P7QueryResult),                                                           
                    qs.CAT.P6_INITIAL_ONE : Q_CLASS(qa.SearchInitialNumQA, qr.P3P4P6P7QueryResult),                                                                                  
                    qs.CAT.P6_MIDDLE_ONE : Q_CLASS(qa.SearchMultipleNumQA, qr.P3P4P6P7QueryResult),                                                                                  
                    qs.CAT.P6_FINAL_ONE : Q_CLASS(qa.SearchFinalNumQA, qr.P3P4P6P7QueryResult),                                                                                  
                    qs.CAT.P7_INITIAL : Q_CLASS(qa.P7InitialQA, qr.P3P4P6P7QueryResult),                                                                                  
                    qs.CAT.P7_BOTH : Q_CLASS(qa.P7BothQA, qr.P3P4P6P7QueryResult),                                                                                  
                    qs.CAT.P7_FINAL : Q_CLASS(qa.P7FinalQA, qr.P3P4P6P7QueryResult), 
                    qs.CAT.P8_EQ : Q_CLASS(qa.ThresholdQueryAggregator, None),
                    qs.CAT.P9_ALARM_WORDS : Q_CLASS(qa.AlarmwordAggregator, qr.P9AlarmQueryResult),                                                                             
                    qs.CAT.P11_SHORT : Q_CLASS(qa.XMLLeafQueryAggregator, qr.EqualityQueryResult),
                    qs.CAT.P11_FULL : Q_CLASS(qa.XMLPathQueryAggregator, qr.EqualityQueryResult)}  

class AtomicQueryBatch(query_batch.QueryBatch):

    
    def __init__(self, queries, gen_num, choose_num, full_query):
        """
            Args
             * 'queries' - the queries which is a list of dictionaries
                           containing the values and the meta information
                           for a single sql query
             * 'gen_num' - the number of queries generated
             * 'choose_num' - the number to choose
             * 'full_query' - boolean whether a full query or not
        """
        
        self.gen_num = gen_num
        self.choose_num = choose_num
        self.queries = queries
        self.full_query = full_query
        self.refined_queries_results = None
        for q in self.queries:
            try:
                qbs.set_result_set_size_range_lower(q[qs.QRY_ENUM], q[qs.QRY_LRSS])
                qbs.set_result_set_size_range_upper(q[qs.QRY_ENUM], q[qs.QRY_URSS])
            except KeyError:
                pass 
            
    def make_aggregator(self):
        """
        Returns a gen_choose aggregator which wraps the associated 
        aggregators for the queries contained in the query batch
        """
        aggregators = [CAT_TO_CLASSES[q[qs.QRY_ENUM]].aggregator(q) for q in self.queries]
        return qa.GenChooseAggregator(aggregators)
    
    
    def produce_queries(self):
        """
        Returns the query dicts that the bob is based around, used primarily
        for debugging purposes and nested refinement. Returns a list of query 
        dictionaries. 
        """
        if self.refined_queries_results != None:
            return self.refined_queries_results
        else:
            return self.queries
    
    def refine_queries(self, agg_result):
        """
        Takes in 'agg_result' which is the result from the aggregator
        for this BOQ.
        Selects which queries should be recorded in the results database. 
        To do this it creates a new list of associated selected queries
        and pairs them with their results. 
        """
        #selecting queries that match.
        queries = []
        assert len(self.queries) == len(agg_result[qs.QRY_SUBRESULTS])
        for q, r  in zip(self.queries, agg_result[qs.QRY_SUBRESULTS]):
            assert q
            assert r
            assert q[qs.QRY_QID] >= r[qs.QRY_QID]
            count = len(r[rdb.DBF_MATCHINGRECORDIDS])
            if all([qbs.get_rss_lower(q[qs.QRY_ENUM]) <= count, 
                    qbs.get_rss_upper(q[qs.QRY_ENUM]) >= count,
                   r[qs.QRY_VALID]]):
                queries.append((q, r))
    
        #capping at choose-num number of queries
        self.refined_queries_results = queries 
                
    
    def process_results(self, agg_results, db_object, query_file_handle, refined_queries = None):
        """
        Takes in the aggregator results, with those results, determines
        which queries in the batch are 'interesting' it then instantiates
        query_results for those queries and uses it to write it to the 
        results database. 
        
        Refine arguement is a list of already refined queries if the user 
        does not wish to rely on the pre-defined refine queries function
        """
        
        #refine queries if not already refined.
        if not refined_queries:
            self.refine_queries(agg_results)
        else:
            self.refined_queries_results = refined_queries
        #create result objects and write to ground truth database
        for (q, r) in self.refined_queries_results:
            query_result = CAT_TO_CLASSES[q[qs.QRY_ENUM]].result_class(q,r,db_object, self.full_query)
            try:
                query_result.write_query()
            except Exception as detail:
                logger.critical("ERROR failed to write query with qid=%d"
                                ". Got error: %s" % (q[qs.QRY_QID], detail))
                
        #writing queries in sql format to file
        if self.full_query:        
            for (q,r) in self.refined_queries_results:
                if q != None:
                    self._print_query(q, query_file_handle)
                                          
                                                             
class EqualityFishingQueryBatch(AtomicQueryBatch):
 
    @staticmethod
    def format_value_and_where(field, value):
        #tries to replace ' with '' in string values, 
        #different types that are not strings raise different
        #exceptions (Type and Attribute Errors) which means
        #there is no ' that needs to be replaced, so they
        #may pass
        where_val = sv.VAR_CONVERTERS[field].to_csv(value)
        agg_val = sv.VAR_CONVERTERS[field].to_agg_fmt(value)
        try:
            where_val = where_val.replace('\'', '\'\'')
        except TypeError:
            pass 
        except AttributeError:
            pass
        if sv.sql_info[field][0] in ['foo','age','income', 'last_updated', 
                                      'weeks_worked_last_year', "hours_worked_per_week"]:
            where = '%s = %s' % (sv.sql_info[field][0], where_val)
        else:
            where = '%s = \'\'%s\'\'' % (sv.sql_info[field][0], where_val)
            
        return (agg_val, where) 
          
    
    def refine_queries(self, agg_result):
        """
        Takes in 'agg_result' which is the result from the aggregator
        for this BOQ.
        Selects which queries should be recorded in the results database. 
        To do this it creates a new list of associated selected queries
        and pairs them with their results. 
        """
        #selecting queries that match.
        queries = []
        assert len(self.queries) == len(agg_result[qs.QRY_SUBRESULTS])
        for q, r  in zip(self.queries, agg_result[qs.QRY_SUBRESULTS]):
            assert q
            assert r
            assert q[qs.QRY_QID] >= r[qs.QRY_QID]
            potential_queries = []
            for (value, value_result) in r[qs.QRY_FISHING_MATCHES_FOUND].iteritems():
                count = len(value_result)
                if qbs.get_rss_lower(q[qs.QRY_ENUM]) <= count and\
                   qbs.get_rss_upper(q[qs.QRY_ENUM]) >= count:
                    (value, where) = self.format_value_and_where(
                        sv.sql_name_to_enum(q[qs.QRY_FIELD]), value)
                    q[qs.QRY_VALUE] = value
                    q[qs.QRY_WHERECLAUSE] = where 
                    r[rdb.DBF_MATCHINGRECORDIDS] = value_result 
                    potential_queries.append((q, r))
            if potential_queries:
                chosen_q = random.sample(potential_queries,1)[0]
                chosen_q[0][qs.QRY_QID] = \
                    qids.full_where_has_been_seen(chosen_q[0][qs.QRY_QID], 
                                                  chosen_q[0][qs.QRY_WHERECLAUSE])
                queries.append(chosen_q)
        #capping at choose-num number of queries
        self.refined_queries_results = queries 
    
class EqualityQueryBatch(AtomicQueryBatch):
    pass             
    
class RangeQueryBatch(AtomicQueryBatch):
    pass
      
class FooRangeQueryBatch(AtomicQueryBatch):
         
    
    def refine_queries(self, agg_result):
        """
        Takes in 'agg_result' which is the result from the aggregator
        for this BOQ.
        
        Selects which queries should be recorded in the results database. 
        To discard a query it simply drops it and the associated result.
        """ 
        range_seen = set()
    
        #selecting queries that match.
        queries = []
        assert len(self.queries) == len(agg_result[qs.QRY_SUBRESULTS])
        for q, r  in zip(self.queries, agg_result[qs.QRY_SUBRESULTS]):
            assert q
            assert r
            assert q[qs.QRY_QID] >= r[qs.QRY_QID]
            count = len(r[rdb.DBF_MATCHINGRECORDIDS])
            #Weed out incorrect counts and previously seen range values
            if all([qbs.get_rss_lower(q[qs.QRY_ENUM]) <= count, 
                    qbs.get_rss_upper(q[qs.QRY_ENUM]) >= count,
                  q[qs.QRY_RANGEEXP] not in range_seen,
                  r[qs.QRY_VALID]]):
                queries.append((q, r))
                range_seen.add(q[qs.QRY_RANGEEXP])

  
        #capping at choose-num number of queries
        self.refined_queries_results = queries 
             
    
    
        
class KeywordQueryBatch(AtomicQueryBatch):
      pass
           
class WildcardQueryBatch(AtomicQueryBatch):
      pass
  
class XmlQueryBatch(AtomicQueryBatch):
      pass 

class AlarmQueryBatch(AtomicQueryBatch):
    
    def refine_queries(self, agg_result):
        '''
        Selects the queries that work given the chosen result set size, 
        and once those are selected it correctly orders the results with
        those rows who the words are closer towards the front of the 
        id list
        '''
        queries = []
        assert len(self.queries) == len(agg_result[qs.QRY_SUBRESULTS])
        for q, r  in zip(self.queries, agg_result[qs.QRY_SUBRESULTS]):
            assert q
            assert r
            assert q[qs.QRY_QID] >= r[qs.QRY_QID]
            row_dist = r[qs.QRY_MATCHINGROWIDANDDISTANCES]
            count = len(row_dist)
            if all([qbs.get_rss_lower(q[qs.QRY_ENUM]) <= count, 
                    qbs.get_rss_upper(q[qs.QRY_ENUM]) >= count,
                   r[qs.QRY_VALID]]):
                dist_dict = {}
                for (row_id, dist) in row_dist:
                    try:
                        dist_dict[dist].append(row_id)
                    except KeyError:
                        dist_dict[dist] = [row_id]
                ids = []
                counts = []
                for (dist, row_ids) in sorted(dist_dict.iteritems(), reverse=False):
                    ids += row_ids
                    counts.append(len(row_ids))
                r[rdb.DBF_MATCHINGRECORDIDS] = ids
                r[qs.QRY_MATCHINGRECORDCOUNTS] = '|'.join(map(str, 
                                                sorted(counts, reverse=False)))
                queries.append((q, r))

  
        #capping at choose-num number of queries
        self.refined_queries_results = queries 

