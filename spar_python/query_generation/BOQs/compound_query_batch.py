# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH 
#  Description:        Represents an and query batch
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 September 2013  ATLH            Original file
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
import itertools
import logging
import spar_python.query_generation.BOQs.atomic_query_batches as aqb
import spar_python.common.spar_random as random
import spar_python.query_generation.query_bounds as qbs

logger = logging.getLogger(__name__)
    
class CompoundQueryBatch(query_batch.QueryBatch):
    
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
        self.result_to_agg_map = {}
        for q in self.queries:
            try:
                qbs.set_result_set_size_range_lower(q[qs.QRY_ENUM], q[qs.QRY_LRSS])
                qbs.set_result_set_size_range_upper(q[qs.QRY_ENUM], q[qs.QRY_URSS])
                qbs.set_tm_result_set_size_range_lower(q[qs.QRY_ENUM], q[qs.QRY_FTMLOWER])
                qbs.set_tm_result_set_size_range_upper(q[qs.QRY_ENUM], q[qs.QRY_FTMUPPER])
            except KeyError:
                pass 
        
    def make_aggregator(self):
        """
        Returns a gen_choose aggregator which wraps the associated 
        aggregators for the queries contained in the query batch
        """
        clause_queries = []
        for comp_q in self.queries:
            for bob in comp_q[qs.QRY_SUBBOBS]:
                clause_queries.extend(bob.produce_queries())
        
        wheres = []
        dedup_clause_queries = []
        for clause in clause_queries:
            try:
                index = wheres.index(clause[qs.QRY_WHERECLAUSE])
            except ValueError:
                index = len(wheres)
                wheres.append(clause[qs.QRY_WHERECLAUSE])
                dedup_clause_queries.append(clause)
            self.result_to_agg_map[clause[qs.QRY_WHERECLAUSE]] = index
      
        for q in dedup_clause_queries:
            q['top_level'] = False
            
        aggregators = [aqb.CAT_TO_CLASSES[q[qs.QRY_ENUM]].aggregator(q) for q in dedup_clause_queries]
        return qa.GenChooseAggregator(aggregators)
    
    def refine_queries(self, agg_result):
        pass
       
    def produce_queries(self):
        """
        Returns the query dicts that the bob is based around, used primarily
        for debugging purposes and nested refinement. Returns a list of query 
        dictionaries. 
        """
        if self.refined_queries_results:
            return self.refined_queries_results
        else:
            queries = []
            for q in self.queries:
                q['sub_queries'] = [b.produce_queries() for b in q[qs.QRY_SUBBOBS]]
                queries.append(q)
            return queries
            
    
                                                           
class AndQueryBatch(CompoundQueryBatch):

    ## THIS CODE IS DUPLICATED ACROSS ALL COMPOUND BOBS FOR PERFORMANCE REASONS,
    ## IF SOMETHING CHANGES HERE IT NEEDS TO CHANGE **EVERYWHERE** 
    ## ALSO IT IS FORMATTED LIKE THIS FOR PERFORMANCE REASONS 
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
        if refined_queries:
            self.refined_queries_results = refined_queries
            for (comp_q, comp_q_results) in self.refined_queries_results:
                qr.QueryResultBase.write_to_full_to_atomic_table(comp_q,comp_q_results, db_object)
                qr.QueryResultBase.write_to_full_table(comp_q, comp_q_results, db_object)
                comp_q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                 zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]))
                        #print out the query
                self._print_query(comp_q, query_file_handle) 
        else:
            refined_total = 0    
            refined_queries = []
            for x in xrange(len(self.queries)):
                comp_q = self.queries[x]
                sub_results = agg_results[qs.QRY_SUBRESULTS]
                try: 
                    num_clauses = comp_q[qs.QRY_NUMCLAUSES]
                except KeyError:
                    num_clauses = comp_q[qs.QRY_N]
                sub_bobs = comp_q[qs.QRY_SUBBOBS]
                clause_q_b = []
                working_clauses = None
                #create the list of possible queries that can make up the clauses 
                #(they are also paired with the bobs that create them)
                for b in sub_bobs:
                    clause_q = b.produce_queries()
                    clause_q_b += [(q, b) for q in clause_q]
                clause_r = []
                #create list of results that go with those queries
                
                for (q,_) in clause_q_b:
                    clause_r.append(sub_results[self.result_to_agg_map[q[qs.QRY_WHERECLAUSE]]])
                comp_q_results = {qs.QRY_SUBRESULTS : clause_r}  
                #create a list of queries, their bobs, and their results         
                clause_q_r = zip(clause_q_b, clause_r)

                clause_q_r = sorted(clause_q_r, key=lambda ((q,b),r): len(r[rdb.DBF_MATCHINGRECORDIDS]))
                #try all possible cominbations of the queries to test if any
                #have the correct combinations to match the required ftm and ress  
                seen_where_group = []
                working_clauses = []
                q_refined = False
                for clause in clause_q_r:
                    #don't need to check permuations if ftm doesn't match
                    if q_refined == True: 
                        continue
                    ftm_match = len(clause[1][rdb.DBF_MATCHINGRECORDIDS])
                    if not all([ftm_match >= qbs.get_tm_rss_lower(comp_q[qs.QRY_ENUM]),
                                ftm_match <= qbs.get_tm_rss_upper(comp_q[qs.QRY_ENUM])]):
                        continue 
                    #alright ftm matches, let's check the rest of the clauses
                    for clause_set in itertools.combinations(
                                            clause_q_r, num_clauses-1):
                        #query has already been refined
                        if q_refined == True:
                            continue
                        clause_list = [clause] + list(clause_set) 
                        #check to see if any of the clauses or their fields are the same
                        #if so we know the intersection is one we are not interested in
                        values = [q[qs.QRY_WHERECLAUSE] for ((q,_),_) in clause_list]
                        fields = [q[qs.QRY_FIELD] for ((q,_),_) in clause_list]
                        #there are duplicate values or this where has already been seen
                        if len(values)!=len(set(values)) or\
                           len(fields)!=len(set(fields)) or\
                            values in seen_where_group:
                            continue
                        seen_where_group.append(values)
                        
                        #check conditions
                        matching_ids_set = reduce(set.intersection, 
                                      [set(r[rdb.DBF_MATCHINGRECORDIDS]) for (_,r)
                                                                         in clause_list])
                        count = len(matching_ids_set)
     
                        if not all([count >= qbs.get_rss_lower(comp_q[qs.QRY_ENUM]),
                                count <= qbs.get_rss_upper(comp_q[qs.QRY_ENUM]),
                                ftm_match >= qbs.get_tm_rss_lower(comp_q[qs.QRY_ENUM]),
                                ftm_match <= qbs.get_tm_rss_upper(comp_q[qs.QRY_ENUM])]):
                            continue
                        
                        #this combination worked, so don't need to refine further for this
                        #particular query
                        q_refined = True
                        refined_total += 1
                        #reorder clauses
                        working_clauses = clause_list 
                        reordered_clauses = working_clauses[:1]
                        working_clauses.remove(reordered_clauses[0])
                        cumulative_set = set(reordered_clauses[0][1][rdb.DBF_MATCHINGRECORDIDS])
                        while len(working_clauses) > 0:
                            next_clause = working_clauses[0]
                            current_set = cumulative_set.intersection(working_clauses[0][1][rdb.DBF_MATCHINGRECORDIDS])
                            for clauses in working_clauses:
                                potential_set = cumulative_set.intersection(clauses[1][rdb.DBF_MATCHINGRECORDIDS])
                                if len(potential_set) < len(current_set):
                                    next_clause = clauses
                                    current_set = potential_set     
                            working_clauses.remove(next_clause)
                            reordered_clauses.append(next_clause)
                            cumulative_set = current_set
            
                        working_clauses = reordered_clauses
            
                        #update query with chosen clauses
                        whereclauses = [q[qs.QRY_WHERECLAUSE] for ((q, _), _) in working_clauses]
                        comp_q[qs.QRY_WHERECLAUSE] = " AND ".join(whereclauses) 
                        comp_q['sub_queries'] = [q for ((q,_),_) in working_clauses]
                        comp_q[qs.QRY_SUBBOBS] = [b for ((_,b), _) in working_clauses]
            
                        ftm_match = len(working_clauses[0][1][rdb.DBF_MATCHINGRECORDIDS])
                        matching_ids_set = reduce(set.intersection, 
                                      [set(r[rdb.DBF_MATCHINGRECORDIDS]) for (_,r)
                                                                         in working_clauses])
                        comp_q_results[qs.QRY_SUBRESULTS] = [r for (_,r) in working_clauses]
                        comp_q_results[rdb.DBF_MATCHINGRECORDIDS] = matching_ids_set
                        comp_q_results[qs.QRY_NUMRECORDSMATCHINGFIRSTTERM] = ftm_match
                        
                        #get the id's lined up
                        comp_q[qs.QRY_QID] = qids.full_where_has_been_seen(comp_q[qs.QRY_QID], 
                                                              comp_q[qs.QRY_WHERECLAUSE])
                        comp_q_results[qs.QRY_QID] = comp_q[qs.QRY_QID]
                        for (sub_q, sub_r) in zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]):
                            sub_q[qs.QRY_QID] = qids.atomic_where_has_been_seen(sub_q[qs.QRY_QID], 
                                                                        sub_q[qs.QRY_WHERECLAUSE])
                            sub_r[qs.QRY_QID] = sub_q[qs.QRY_QID]
                            
                        #write the results to the results database
                        qr.QueryResultBase.write_to_full_to_atomic_table(comp_q,comp_q_results, db_object)
                        qr.QueryResultBase.write_to_full_table(comp_q, comp_q_results, db_object)
                        comp_q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                 zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]))
                        #print out the query
                        self._print_query(comp_q, query_file_handle)  
                        refined_queries.append((comp_q, comp_q_results))
                        
                                                           
                logger.info("FINISHED QUERY %d of %d, TOTAL THAT WORK %d" % (x, len(self.queries), refined_total))
                if q_refined == True:
                    logger.info("WORKING QUERY INFORMATION qid = %d, where_clause = %s, ftm = %d, rss = %d" % (comp_q[qs.QRY_QID],comp_q[qs.QRY_WHERECLAUSE],
                                                                                                 ftm_match, count))

            #capping at choose-num number of queries 
            self.refined_queries_results = refined_queries

   
                
                      
    
class AndTA2QueryBatch(AndQueryBatch):

    ## THIS CODE IS DUPLICATED ACROSS ALL COMPOUND BOBS FOR PERFORMANCE REASONS,
    ## IF SOMETHING CHANGES HERE IT NEEDS TO CHANGE **EVERYWHERE** 
    ## ALSO IT IS FORMATTED LIKE THIS FOR PERFORMANCE REASONS 
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
        if refined_queries:
            self.refined_queries_results = refined_queries
        else:    
            refined_queries = []
            refined_total=0
            for x in xrange(len(self.queries)):
                comp_q = self.queries[x]
                sub_results = agg_results[qs.QRY_SUBRESULTS]
                try: 
                    num_clauses = comp_q[qs.QRY_NUMCLAUSES]
                except KeyError:
                    num_clauses = comp_q[qs.QRY_N]
                sub_bobs = comp_q[qs.QRY_SUBBOBS]
                clause_q_b = []
                working_clauses = None
                #create the list of possible queries that can make up the clauses 
                #(they are also paired with the bobs that create them)
                for b in sub_bobs:
                    clause_q = b.produce_queries()
                    clause_q_b += [(q, b) for q in clause_q]
                clause_r = []
                #create list of results that go with those queries
                for (q,_) in clause_q_b:
                    clause_r.append(sub_results[self.result_to_agg_map[q[qs.QRY_WHERECLAUSE]]])
                comp_q_results = {qs.QRY_SUBRESULTS : clause_r}  
                #create a list of queries, their bobs, and their results         
                clause_q_r = zip(clause_q_b, clause_r)
                clause_q_r = [((q,b),r) for ((q,b),r) in clause_q_r if r[qs.QRY_VALID]]
                #try all possible cominbations of the queries to test if any
                #have the correct combinations to match the required ftm and ress  
                seen_where_group = []
                working_clauses = []
                q_refined = False
                for clause in clause_q_r:
                    for clause_set in itertools.combinations(
                                            clause_q_r, num_clauses-1):
                        if q_refined == True:
                            continue
                        clause_list = [clause] + list(clause_set) 
                        values = [q[qs.QRY_WHERECLAUSE] for ((q,_),_) in clause_list]
                        if len(values)!=len(set(values)) or values in seen_where_group:
                            continue
                        seen_where_group.append(values)
                        matching_ids_set = reduce(set.intersection, 
                                      [set(r[rdb.DBF_MATCHINGRECORDIDS]) for (_,r)
                                                                         in clause_list])
                        count = len(matching_ids_set)
                        P2_cats = [q for ((q,_),_) in clause_list if q[qs.QRY_CAT] == 'P2']
                        if not all([count >= qbs.get_rss_lower(comp_q[qs.QRY_ENUM]),
                                count <= qbs.get_rss_upper(comp_q[qs.QRY_ENUM]),
                                len(P2_cats) <= 1]):
                            continue
                    
                        #this combination worked, so don't need to refine further for this
                        #particular query
                        q_refined = True
                        refined_total += 1
                        working_clauses = clause_list
                        #reorder clauses
                        re_ordered_clauses = []
                        last_clause = None
                        for ((q,b),r) in working_clauses:
                            if q[qs.QRY_CAT] == 'P2':
                                last_clause = ((q,b),r)
                            else:
                                re_ordered_clauses.append(((q,b),r))
                        if last_clause:
                            re_ordered_clauses.append(last_clause)
            
                        working_clauses = re_ordered_clauses
            
                        #update query with chosen clauses
                        whereclauses = [q[qs.QRY_WHERECLAUSE] for ((q, _), _) in working_clauses]
                        comp_q[qs.QRY_WHERECLAUSE] = " AND ".join(whereclauses) 
                        comp_q['sub_queries'] = [q for ((q,_),_) in working_clauses]
                        comp_q[qs.QRY_SUBBOBS] = [b for ((_,b), _) in working_clauses]
                        ftm_match = len(working_clauses[0][1][rdb.DBF_MATCHINGRECORDIDS])
                        matching_ids_set = reduce(set.intersection, 
                                      [set(r[rdb.DBF_MATCHINGRECORDIDS]) for (_,r)
                                                                         in working_clauses])
                        comp_q_results[qs.QRY_SUBRESULTS] = [r for (_,r) in working_clauses]
                        comp_q_results[rdb.DBF_MATCHINGRECORDIDS] = matching_ids_set
                        comp_q_results[qs.QRY_NUMRECORDSMATCHINGFIRSTTERM] = ftm_match
    
                        refined_queries.append((comp_q, comp_q_results))

                        
                
                #make where clause, update and with chosen queries and the aggregator results
                #with the chosen results                                              
                logger.info("FINISHED QUERY %d of %d, TOTAL THAT WORK %d" % (x, len(self.queries), refined_total))
                if q_refined == True:
                    logger.info("WORKING QUERY INFORMATION where_clause = %s, ftm = %d, rss = %d" % (comp_q[qs.QRY_WHERECLAUSE],
                                                                                                 ftm_match, count))

            for (q,r) in refined_queries:
                q[qs.QRY_QID] = qids.full_where_has_been_seen(q[qs.QRY_QID], 
                                                              q[qs.QRY_WHERECLAUSE])
                r[qs.QRY_QID] = q[qs.QRY_QID]
                for (sub_q, sub_r) in zip(q['sub_queries'], r[qs.QRY_SUBRESULTS]):
                    sub_q[qs.QRY_QID] = qids.atomic_where_has_been_seen(sub_q[qs.QRY_QID], 
                                                                        sub_q[qs.QRY_WHERECLAUSE])
                    sub_r[qs.QRY_QID] = sub_q[qs.QRY_QID]
                    
            
            #capping at choose-num number of queries 
            self.refined_queries_results = refined_queries
            #create result objects and write to ground truth database
        for (q, r) in self.refined_queries_results:
            qr.QueryResultBase.write_to_full_to_atomic_table(q,r, db_object)
            qr.QueryResultBase.write_to_full_table(q, r, db_object)
            q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                 zip(q['sub_queries'], r[qs.QRY_SUBRESULTS]))
        #writing queries in sql format to file        
        for (q, _) in self.refined_queries_results:
            if q != None:
                self._print_query(q, query_file_handle)      
    
                 
class OrQueryBatch(CompoundQueryBatch):
    ## THIS CODE IS DUPLICATED ACROSS ALL COMPOUND BOBS FOR PERFORMANCE REASONS,
    ## IF SOMETHING CHANGES HERE IT NEEDS TO CHANGE **EVERYWHERE** 
    ## ALSO IT IS FORMATTED LIKE THIS FOR PERFORMANCE REASONS 
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
        if refined_queries:
            self.refined_queries_results = refined_queries
            for (comp_q, comp_q_results) in self.refined_queries_results:
                qr.QueryResultBase.write_to_full_to_atomic_table(comp_q,comp_q_results, db_object)
                qr.QueryResultBase.write_to_full_table(comp_q, comp_q_results, db_object)
                comp_q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                 zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]))
                        #print out the query
                self._print_query(comp_q, query_file_handle) 
        else: 
            refined_total = 0   
            refined_queries = []
            for x in xrange(len(self.queries)):
                comp_q = self.queries[x]
                sub_results = agg_results[qs.QRY_SUBRESULTS]

                num_clauses = comp_q[qs.QRY_NUMCLAUSES]
   
                sub_bobs = comp_q[qs.QRY_SUBBOBS]
                clause_q_b = []
                working_clauses = None
                #create the list of possible queries that can make up the clauses 
                #(they are also paired with the bobs that create them)
                for b in sub_bobs:
                    clause_q = b.produce_queries()
                    clause_q_b += [(q, b) for q in clause_q]
                clause_r = []
                #create list of results that go with those queries
                
                for (q,_) in clause_q_b:
                    clause_r.append(sub_results[self.result_to_agg_map[q[qs.QRY_WHERECLAUSE]]])
                comp_q_results = {qs.QRY_SUBRESULTS : clause_r}  
                #create a list of queries, their bobs, and their results         
                clause_q_r = zip(clause_q_b, clause_r)
                clause_q_r = [((q,b),r) for ((q,b),r) in clause_q_r 
                              if len(r[rdb.DBF_MATCHINGRECORDIDS]) <= qbs.get_tm_rss_upper(comp_q[qs.QRY_ENUM])]
                if len(clause_q_r) < num_clauses:
                    continue
                #try all possible cominbations of the queries to test if any
                #have the correct combinations to match the required ftm and ress  
                seen_where_group = []
                working_clauses = []
                q_refined = False
                for clause_set in itertools.combinations(
                                        clause_q_r, num_clauses):
                    #query has already been refined
                    if q_refined == True:
                        continue
                    clause_list = list(clause_set) 
                    values = [q[qs.QRY_WHERECLAUSE] for ((q,_),_) in clause_list]
                    #there are duplicate values or this where has already been seen
                    if len(values)!=len(set(values)) or\
                        values in seen_where_group:
                        continue
                    seen_where_group.append(values)
                    
                    #check conditions
                    matching_ids_set = reduce(set.union, 
                              [set(r[rdb.DBF_MATCHINGRECORDIDS]) for (_,r)
                                                                 in clause_list])
                    count = len(matching_ids_set)
                    all_match = sum(map(len, [r[rdb.DBF_MATCHINGRECORDIDS] for (_, r) in clause_list]))
                    if not all([count >= qbs.get_rss_lower(comp_q[qs.QRY_ENUM]),
                                count <= qbs.get_rss_upper(comp_q[qs.QRY_ENUM]),
                                all_match >= qbs.get_tm_rss_lower(comp_q[qs.QRY_ENUM]),
                                all_match <= qbs.get_tm_rss_upper(comp_q[qs.QRY_ENUM])]):
                        continue
                    #this combination worked, so don't need to refine further for this
                    #particular query
                    q_refined = True
                    refined_total += 1
                    working_clauses = clause_list
                    #update query with chosen clauses
                    whereclauses = [q[qs.QRY_WHERECLAUSE] for ((q, _), _) in working_clauses]
                    comp_q[qs.QRY_WHERECLAUSE] = " OR ".join(whereclauses) 
                    comp_q['sub_queries'] = [q for ((q,_),_) in working_clauses]
                    comp_q[qs.QRY_SUBBOBS] = [b for ((_,b), _) in working_clauses]
        
                    ftm_match = len(working_clauses[0][1][rdb.DBF_MATCHINGRECORDIDS])

                    comp_q_results[qs.QRY_SUBRESULTS] = [r for (_,r) in working_clauses]
                    comp_q_results[rdb.DBF_MATCHINGRECORDIDS] = matching_ids_set
                    comp_q_results[qs.QRY_SUMRECORDSMATCHINGEACHTERM] = all_match
                    comp_q_results[qs.QRY_NUMRECORDSMATCHINGFIRSTTERM] = ftm_match

                    #make sure duplicate queries (and their atomic sub_components) have the same qids 
                    comp_q[qs.QRY_QID] = qids.full_where_has_been_seen(comp_q[qs.QRY_QID], 
                                                              comp_q[qs.QRY_WHERECLAUSE])
                    comp_q_results[qs.QRY_QID] = q[qs.QRY_QID]
                    for (sub_q, sub_r) in zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]):
                        sub_q[qs.QRY_QID] = qids.atomic_where_has_been_seen(sub_q[qs.QRY_QID], 
                                                                        sub_q[qs.QRY_WHERECLAUSE])
                        sub_r[qs.QRY_QID] = sub_q[qs.QRY_QID]
                        
                    #create result objects and write to ground truth database   
                    qr.QueryResultBase.write_to_full_to_atomic_table(comp_q,comp_q_results, db_object)
                    qr.QueryResultBase.write_to_full_table(comp_q, comp_q_results, db_object)
                    comp_q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                 zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]))   
                    refined_queries.append((comp_q, comp_q_results))
                     
                    #print query
                    self._print_query(comp_q, query_file_handle)   
                
                #make where clause, update and with chosen queries and the aggregator results
                #with the chosen results                                              
                logger.info("FINISHED QUERY %d of %d, TOTAL THAT WORK %d" % (x, len(self.queries), refined_total))
                if q_refined == True:
                    logger.info("WORKING QUERY INFORMATION where_clause = %s, sftm = %d, rss = %d" % (comp_q[qs.QRY_WHERECLAUSE],
                                                                                                 all_match, count))
            
            self.refined_queries_results = refined_queries

      
class ThresholdQueryBatch(CompoundQueryBatch):
      
    ## THIS CODE IS DUPLICATED ACROSS ALL COMPOUND BOBS FOR PERFORMANCE REASONS,
    ## IF SOMETHING CHANGES HERE IT NEEDS TO CHANGE **EVERYWHERE** 
    ## ALSO HAS BEEN OPTIMIZED - SO BEWARE CHANGING IT 
    ## 
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
        if refined_queries != None:
            self.refined_queries_results = refined_queries 
            for (q, r) in self.refined_queries_results:
                qr.QueryResultBase.write_to_full_to_atomic_table(q,r, db_object)
                qr.QueryResultBase.write_to_full_table(q, r, db_object)
                q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                     zip(q['sub_queries'], r[qs.QRY_SUBRESULTS]))
                self._print_query(q, query_file_handle)
             
                try:
                    q[qs.QRY_PERF].remove('IBM1')
                except ValueError:
                    pass
                
                q[qs.QRY_WHERECLAUSE] = q[qs.QRY_WHERECLAUSE] + " ORDER BY " +\
                                        q[qs.QRY_WHERECLAUSE] + " DESC"
                q[qs.QRY_ENUM] = qs.CAT.P9_EQ
                q[qs.QRY_CAT] = 'P9'
                q[qs.QRY_QID] = qids.full_where_has_been_seen(qids.query_id(), 
                                                              q[qs.QRY_WHERECLAUSE])
                r[qs.QRY_QID] = q[qs.QRY_QID]
                qr.QueryResultBase.write_to_full_to_atomic_table(q,r, db_object)
                qr.QueryResultBase.write_to_full_table(q, r, db_object)
                self._print_query(q, query_file_handle)
                q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                     zip(q['sub_queries'], r[qs.QRY_SUBRESULTS])) 
        else:
            refined_total = 0
            refined_queries = []
            for x in xrange(len(self.queries)):
                comp_q = self.queries[x]
                sub_results = agg_results[qs.QRY_SUBRESULTS]
                num_clauses = comp_q[qs.QRY_N]
                sub_bobs = comp_q[qs.QRY_SUBBOBS]
                clause_q_b = []
                #create the list of possible queries that can make up the clauses 
                #(they are also paired with the bobs that create them)
                for b in sub_bobs:
                    clause_q = b.produce_queries()
                    clause_q_b += [(q, b) for q in clause_q]
                clause_r = []
                #create list of results that go with those queries
                
                for (q,_) in clause_q_b:
                    clause_r.append(sub_results[self.result_to_agg_map[q[qs.QRY_WHERECLAUSE]]])
                comp_q_results = {qs.QRY_SUBRESULTS : clause_r}  
                #create a list of queries, their bobs, and their results         
                clause_q_r = zip(clause_q_b, clause_r)
                clause_q_r = sorted(clause_q_r, key=lambda ((q,b),r): len(r[rdb.DBF_MATCHINGRECORDIDS]))
                #try all possible cominbations of the queries to test if any
                #have the correct combinations to match the required ftm and ress  
                seen_where_group = []
                comp_q_refined = False
                for clause_set in itertools.combinations(
                                       clause_q_r, num_clauses):
                   if comp_q_refined == True:
                       continue
                   clause_list = list(clause_set) 
                   values = [q[qs.QRY_WHERECLAUSE] for ((q,_),_) in clause_list]
                   if len(values)!=len(set(values)) or values in seen_where_group:
                       continue
                   seen_where_group.append(values)
                   
                   #check to see if it is working
                   #if stfm doesn't match, don't bother continuing
                   stfm = 0
                   for offset in xrange(comp_q[qs.QRY_N]-comp_q[qs.QRY_M]+1):
                       (_,r) = clause_list[offset]   
                       stfm += len(r[rdb.DBF_MATCHINGRECORDIDS])
                   if not all([stfm >= qbs.get_tm_rss_lower(comp_q[qs.QRY_ENUM]),
                               stfm <= qbs.get_tm_rss_upper(comp_q[qs.QRY_ENUM])]):
                       continue
                   #if stfm does match, calculate the set intersection
                   matching_ids_set = set()
                   for m_set in itertools.combinations(clause_list, comp_q[qs.QRY_M]):
                       matching_ids_set.update(reduce(set.intersection, 
                                 [set(r[rdb.DBF_MATCHINGRECORDIDS]) for (_,r)
                                                                    in m_set]))
                   count = len(matching_ids_set)
                   
                   #check overall compliance     
                   if not all([count >= qbs.get_rss_lower(comp_q[qs.QRY_ENUM]),
                               count <= qbs.get_rss_upper(comp_q[qs.QRY_ENUM])]):
                       continue 
                   
                   comp_q_refined = True
                   refined_total += 1
                   ##PROCESSING THE WORKING CLAUSE_LIST
                   working_clauses = clause_list
                   whereclauses = [q[qs.QRY_WHERECLAUSE] for ((q, _), _) in working_clauses]
                   where =  ", ".join(whereclauses)
                   where =  'M_OF_N(%d, %d, %s)' % (comp_q[qs.QRY_M], comp_q[qs.QRY_N], where)
                   #update query with chosen clauses
                   comp_q[qs.QRY_WHERECLAUSE] = where
                   comp_q['sub_queries'] = [q for ((q,_),_) in working_clauses]
                   comp_q[qs.QRY_SUBBOBS] = [b for ((_,b), _) in working_clauses]
               
                   #have to create a list of counts of how many that match N terms, n-1 terms...
                   #until m. Such of the form 34 | 384 | 1094
                   records_matching_count = dict(zip(range(comp_q[qs.QRY_M],
                                               comp_q[qs.QRY_N]+1),
                                         [0]*comp_q[qs.QRY_N]))
                   for id in matching_ids_set:
                       matching_terms = [1 if id in clause[1][rdb.DBF_MATCHINGRECORDIDS] else 0
                                   for clause in working_clauses]
                       term_matches = sum(matching_terms)
                       records_matching_count[term_matches] +=1
                   matching_records_counts = sorted(records_matching_count.values(), 
                                                        reverse=True)
                   #update the results dictionary with the new calculated values
                   comp_q_results[qs.QRY_SUBRESULTS] = [r for (_,r) in working_clauses]
                   comp_q_results[rdb.DBF_MATCHINGRECORDIDS] = matching_ids_set
                   comp_q_results[qs.QRY_MATCHINGRECORDCOUNTS] = matching_records_counts
     
       
                   #make sure duplicate queries (and their atomic sub_components) have the same qids 
                   comp_q[qs.QRY_QID] = qids.full_where_has_been_seen(comp_q[qs.QRY_QID], 
                                                              comp_q[qs.QRY_WHERECLAUSE])
                   comp_q_results[qs.QRY_QID] = comp_q[qs.QRY_QID]
                   for (sub_q, sub_r) in zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]):
                        sub_q[qs.QRY_QID] = qids.atomic_where_has_been_seen(sub_q[qs.QRY_QID], 
                                                                        sub_q[qs.QRY_WHERECLAUSE])
                        sub_r[qs.QRY_QID] = sub_q[qs.QRY_QID]
                   
                   #write queries to the results database
                   qr.QueryResultBase.write_to_full_to_atomic_table(comp_q,comp_q_results, db_object)
                   qr.QueryResultBase.write_to_full_table(comp_q, comp_q_results, db_object)
                   comp_q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                     zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS]))
                   self._print_query(comp_q, query_file_handle)
             
                   try:
                      comp_q[qs.QRY_PERF].remove('IBM1')
                   except ValueError:
                      pass
                        
                   comp_q[qs.QRY_WHERECLAUSE] = comp_q[qs.QRY_WHERECLAUSE] + " ORDER BY " +\
                                                comp_q[qs.QRY_WHERECLAUSE] + " DESC"
                   comp_q[qs.QRY_ENUM] = qs.CAT.P9_EQ
                   comp_q[qs.QRY_CAT] = 'P9'
                   comp_q[qs.QRY_QID] = qids.full_where_has_been_seen(qids.query_id(), 
                                                                      comp_q[qs.QRY_WHERECLAUSE])
                   comp_q_results[qs.QRY_QID] = comp_q[qs.QRY_QID]
                   qr.QueryResultBase.write_to_full_to_atomic_table(comp_q,comp_q_results, db_object)
                   qr.QueryResultBase.write_to_full_table(comp_q, comp_q_results, db_object)
                   comp_q[qs.QRY_SUBBOBS][0].process_results(None, db_object, query_file_handle,
                                                             zip(comp_q['sub_queries'], comp_q_results[qs.QRY_SUBRESULTS])) 
                   self._print_query(comp_q, query_file_handle)
                   refined_queries.append((comp_q, comp_q_results))
                logger.info("FINISHED QUERY %d of %d, TOTAL THAT WORK %d" % (x, len(self.queries), refined_total))
                if comp_q_refined == True:
                    logger.info("WORKING QUERY INFORMATION where_clause = %s, sftm = %d, rss = %d" % (comp_q[qs.QRY_WHERECLAUSE],
                                                                                                 stfm, count))                   
        self.refined_queries_results = refined_queries   
    

            


    
    

            
        
        
                   
        
