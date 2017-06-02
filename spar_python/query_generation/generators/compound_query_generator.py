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
import spar_python.query_generation.generators.equality_query_generator as eqg
import spar_python.query_generation.query_ids as qids
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import spar_python.query_generation.BOQs.atomic_query_batches as aqb
import spar_python.query_generation.BOQs.compound_query_batch as cqb
import logging
import collections as c  
import bisect
import spar_python.common.spar_random as random
import operator
import itertools
import copy
from math import factorial

def choose(n, r):
    return factorial(n) / factorial(r) / factorial(n-r)


logger = logging.getLogger(__name__)

#Dummy value for row width
QUERY_OVER_GENERATION_RATIO = 2 #Over generation for the number of queries generated
CLAUSE_OVER_GENERATION_RATIO = 3 #Over generation ratio for values for that clause




class CombinationQueryGenerator(query_object.QueryGenerator):
  
    
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
         *other_fields: ['no_queries','r_lower','r_upper','num_clauses','tm_lower','tm_upper']
         *other_cols: [[10,1,10,2,10,100],[10,1,10,2,10,100],...
        '''  
        self._cat = cat  
        self._perf = perf
        self._sub_cat = sub_cat
        self._fields = fields
        self._dists = dict(zip(fields, dists))
        self._db_size = db_size
        self._row_width = row_width
        self._queries = [dict(zip(other_fields,x)) for x in other_cols]
        self._total = sum([x[0] for x in other_cols]) *\
                       QUERY_OVER_GENERATION_RATIO
                       
    def works_for_performer(self, fields):
        '''
        makes sure that the chosen fields work for the specific performer set
        '''
        for perf in self._perf:
           if not all([f in sv.performer_allowed_fields[perf] for f in fields]):
               return False
        
        if self._row_width < 100000 and \
           any([f in sv.fields_not_in_skinny for f in fields]):
            return False
        
        return True 
            
    def choose_fields(self, clauses, q): 
        '''
        chooses values to use for the clauses based on what the first term
        must match and how much that value must be reduced to meet the 
        values for the total result set size
        '''
        (tm_ratio, reduce_ratio) = self.calculate_ratios(q, self._db_size)
        fields = sv.pdf_to_fields[0.00001]
        for key in sorted(sv.pdf_to_fields.keys()):
            if key > tm_ratio and tm_ratio > 0.00001:
                fields = sv.pdf_to_fields[key]
            elif key <= tm_ratio:
                break 
        random.shuffle(fields)
        dependency_lists = copy.deepcopy(sv.field_dependencies_cycles)
        random.shuffle(dependency_lists)
        for f in fields:
            for temp_dependency_list in dependency_lists:
                
                dependency_list = copy.deepcopy(temp_dependency_list)
                if f in dependency_list and len(dependency_list) >= clauses:
                    dependency_list.remove(f)      
                    
                    for clause_set in itertools.combinations(
                                      dependency_list, clauses-1):
                        check_list = list(clause_set)
                        check_list.append(f)
                        if not self.works_for_performer(check_list):
                            continue
                        
                        min_pdfs = map(sv.field_to_min_pdf, clause_set)
                        max_pdfs = map(sv.field_to_max_pdf, clause_set)
                        proposed_funnel_min_ratio = reduce(self.combination_operator(), min_pdfs)
                        proposed_funnel_max_ratio = reduce(self.combination_operator(), max_pdfs)
                       
                        if proposed_funnel_min_ratio <= (reduce_ratio*1.01) and\
                           proposed_funnel_max_ratio >= (reduce_ratio/1.01):
                             return (f, list(clause_set))
        return (None, None)     
                                       
    def generation_order(self, ft, fields):
        '''
        determines the generation order of things 
        '''
        dependencies = set(fields)
        dependencies.add(ft)
        for f in fields:
            map(dependencies.add, sv.field_dependencies[f])
        order = []
        for f in sv.VAR_GENERATION_ORDER:
            if f in dependencies:
                 order.append(f)
        return order
    
    def make_equality_queries(self, field, value):
        '''
        creates equality query dictionaries
        '''
        (value, where) = aqb.EqualityFishingQueryBatch.format_value_and_where(field, value)
        qid = qids.query_id()
        return  {qs.QRY_ENUM : qs.CAT.EQ, 
                 qs.QRY_QID : qids.full_where_has_been_seen(qid,where),
                 qs.QRY_DBNUMRECORDS : self._db_size,
                 qs.QRY_DBRECORDSIZE : self._row_width, 
                 qs.QRY_CAT : 'EQ',
                 qs.QRY_SUBCAT : '', 
                 qs.QRY_WHERECLAUSE : where,
                 qs.QRY_FIELD : sv.sql_info[field][0],
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : sv.sql_info[field][1],
                 qs.QRY_VALUE : value}   
          
    def _generate_clause_values(self, q, ft, fields):
        '''
        generates the values for the clauses 
        '''
        #determine generation order for the values, this will add fields that
        #are not part of the query if fields in the query are dependent on them
        order_fields = self.generation_order(ft, fields)
                
        generated_values = {}
        for x in xrange(CLAUSE_OVER_GENERATION_RATIO):
            #simulated 'row' of values
            row = {}
            for f in order_fields:
                dist = self._dists[f]
                value = self.calculate_value(f, q, dist, row, order_fields, 
                                             ft, self._db_size)
                row[f] = value
                #store the generated values according to field
                try:
                    generated_values[f].append(value)
                except KeyError:
                    generated_values[f] = [value]
        #create the list of bobs, one for all of the clauses
        eq_queries = []
        for (f, values) in generated_values.iteritems():
            if f in fields or f == ft:
                eq_queries += [self.make_equality_queries(f, value)
                          for value in values] 
        return [aqb.EqualityQueryBatch(eq_queries,None, None,False)]   
    
           
    def produce_query_batches(self):
        '''
        loops through query templates, finds appropriate fields, calculates pdf values
        for that, and then over generates values for those fields by a factor of 
        CLAUSE_OVER_GENERATION_RATIO, it then creates and query batches for each
        template 
        '''
        comp_bobs = []
        count = 0
        comp_queries = []
        for q in self._queries:
            #loop through the number of queries that are to be generated based on that
            #template
            
            for x in xrange(q['no_queries']*QUERY_OVER_GENERATION_RATIO):
                #choose appropriate first term (ft) and other fields for the
                #clauses
                try:
                        clause = q['num_clauses']
                except KeyError:
                        clause = q['n']
                (ft,fields)=self.choose_fields(clause, q)
                if ft == None:
                    logger.info('Query Template tm_lower: %d, tm_upper: %d, r_lower: %d r_upper: %d with'\
                            ' %d clauses cannot be supported over this size database' % (q['tm_lower'],
                                                        q['tm_upper'], q['r_lower'], q['r_upper'],clause))
                    break
                count +=1
                #Generate the values for the clauses and make a bob for them 
                bob = self._generate_clause_values(q, ft, fields)
                #create a dictionary for the and query, containing the list of bobs
                #for each query
                comp_queries.append(self.make_query_template(q, bob)) 
            #create_and_dict and append to and list of dicts
        if comp_queries:       
            comp_bobs.append(self.query_batch()(comp_queries,q['no_queries']*\
                                                    QUERY_OVER_GENERATION_RATIO, 
                                              q['no_queries'],
                                              True))
        logger.info("P1-eq-and/or: Generated %d out of %d queries" % (count, self._total))        
        return comp_bobs
    
    def make_query_template(self, q, bob):
        return {    qs.QRY_ENUM : self.enum(), 
                    qs.QRY_QID : qids.query_id(),
                    qs.QRY_DBNUMRECORDS : self._db_size,
                    qs.QRY_DBRECORDSIZE : self._row_width, 
                    qs.QRY_PERF : self._perf,
                    qs.QRY_CAT : self._cat,
                    qs.QRY_SUBCAT : self._sub_cat, 
                    qs.QRY_WHERECLAUSE : '',
                    qs.QRY_NEGATE : False,
                    qs.QRY_LRSS : q['r_lower'],
                    qs.QRY_URSS : q['r_upper'],
                    qs.QRY_FTMLOWER : q['tm_lower'],
                    qs.QRY_FTMUPPER : q['tm_upper'],
                    qs.QRY_NUMCLAUSES : q['num_clauses'], 
                    qs.QRY_NUMTERMSPERCLAUSE : 1,  
                    qs.QRY_SUBBOBS : bob}
         
class AndQueryGenerator(CombinationQueryGenerator):              
               
     def calculate_ratios(self, q, db_size):
         return ((q['tm_upper']*1.0)/db_size, (q['r_upper']*1.0)/q['tm_upper'])
     
     def combination_operator(self):
         return operator.mul
     
     def calculate_value(self, f, q, dist, row, order_fields, ft, db_size): 
         #this is the pdf value based on how much the resulting set size needs to
         #be funnelled or trimmed from the first term matching number
         u_funnel_ratio = (q['r_upper']*1.0)/q['tm_upper']
         l_funnel_ratio = (q['r_lower']*1.0)/q['tm_upper']
         l_pdf = pow(l_funnel_ratio, 1.0/max((len(order_fields)-1),1))
         u_pdf = pow(u_funnel_ratio, 1.0/max((len(order_fields)-1),1))
         if f == ft:
            ft_pdf_upper = (q['tm_upper']*1.0)/db_size
            ft_pdf_lower = (q['tm_lower']*1.0)/db_size
            value = dist.generate_conditional_pdf(ft_pdf_lower,
                                                  ft_pdf_upper,
                                                  row)
         #generate every other clause
         else:
            value = dist.generate_conditional_pdf(u_pdf,u_pdf,row) #change to l_pdf
         return value
     
     def query_batch(self):
         return cqb.AndQueryBatch
     
     def enum(self):
         return qs.CAT.P1_EQ_AND
     
class AndTA2QueryGenerator(AndQueryGenerator):
    
     def query_batch(self):
         return cqb.AndTA2QueryBatch
       
class OrQueryGenerator(CombinationQueryGenerator):              
               
     def calculate_ratios(self, q, db_size):
         return ((q['tm_upper']*1.0)/db_size, (q['r_upper']*1.0)/q['tm_upper'])
     
     def combination_operator(self):
         return operator.add
     
     def calculate_value(self, f, q, dist, row, order_fields, ft, db_size): 
         #breaking up the values 
         total_pdf_upper = (q['tm_upper']*1.0)/db_size
         total_pdf_lower = (q['tm_lower']*1.0)/db_size 
         pdf_upper = total_pdf_upper/q['num_clauses']
         pdf_lower = total_pdf_lower/q['num_clauses']
         value = dist.generate_conditional_pdf(pdf_lower,pdf_upper,row)
         return value
     
     def query_batch(self): 
         return cqb.OrQueryBatch 
     
     def enum(self):
         return qs.CAT.P1_EQ_OR
     
class ThresholdQueryGenerator(CombinationQueryGenerator):
       
     def calculate_ratios(self, q, db_size):
         return ((q['tm_upper']*1.0/(q['n']-q['m']+1))/db_size, 
                 (q['r_upper']*1.0/(choose(q['n'],q['m'])))/db_size)
     
     def combination_operator(self):
         return operator.mul
     
     def calculate_value(self, f, q, dist, row, order_fields, ft, db_size): 
         #breaking up the values 
         total_pdf_upper = (q['tm_upper']*1.0)/db_size
         total_pdf_lower = (q['tm_lower']*1.0)/db_size 
         pdf_upper = total_pdf_upper/q['m']
         pdf_lower = total_pdf_lower/q['m']
         value = dist.generate_conditional_pdf(pdf_lower,pdf_upper,row)
         return value
     
     def query_batch(self):
         return cqb.ThresholdQueryBatch
     
     def enum(self): 
         return qs.CAT.P8_EQ
     
     def make_query_template(self, q, bob):
        return {    qs.QRY_ENUM : self.enum(), 
                    qs.QRY_QID : qids.query_id(),
                    qs.QRY_DBNUMRECORDS : self._db_size,
                    qs.QRY_DBRECORDSIZE : self._row_width, 
                    qs.QRY_PERF : self._perf,
                    qs.QRY_CAT : self._cat,
                    qs.QRY_SUBCAT : 'eq', 
                    qs.QRY_WHERECLAUSE : '',
                    qs.QRY_NEGATE : False,
                    qs.QRY_LRSS : q['r_lower'],
                    qs.QRY_URSS : q['r_upper'],
                    qs.QRY_FTMLOWER : q['tm_lower'],
                    qs.QRY_FTMUPPER : q['tm_upper'],
                    qs.QRY_N : q['n'],
                    qs.QRY_M : q['m'],
                    qs.QRY_SUBBOBS : bob}
                 
                
