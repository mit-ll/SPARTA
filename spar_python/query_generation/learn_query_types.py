# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        handles converstion to query_objects
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  2 August 2013  ATLH            Original file
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import cPickle
import csv
import spar_python.data_generation.spar_variables as sv
import spar_python.query_generation.generators.equality_query_generator as eqg
import spar_python.query_generation.generators.foo_range_query_generator as frqg
import spar_python.query_generation.generators.keyword_query_generator as kqg
import spar_python.query_generation.generators.wildcard_query_generator as wqg
import spar_python.query_generation.generators.compound_query_generator as aqg
import spar_python.query_generation.generators.xml_query_generator as xqg
import spar_python.query_generation.generators.range_query_generator as rqg
import spar_python.query_generation.generators.ta2_query_generator as tqg
import spar_python.query_generation.generators.alarm_query_generator as alqg


#Safely evaluate an expression node or a string containing a Python expression. 
#The string or node provided may only consist of the following Python literal 
#structures: strings, numbers, tuples, lists, dicts, booleans, and None.
from ast import literal_eval

QUERY_SUBCAT = {"eq": eqg.EqualityQueryGenerator,
                "foo-range": frqg.FooRangeQueryGenerator,
                "foo-greater": frqg.FooRangeQueryGenerator,
                'range' : rqg.RangeQueryGenerator,
                "word": kqg.KeywordQueryGenerator,
                "stem" : kqg.KeywordQueryGenerator,
                "wildcard" : wqg.WildcardQueryGenerator,
                "eq-and" : aqg.AndQueryGenerator,
                "eq-or" : aqg.OrQueryGenerator,
                'threshold' : aqg.ThresholdQueryGenerator,
                'xml' : xqg.XmlQueryGenerator,
                'ta2' : tqg.AndTA2QueryGenerator,
                'alarm' : alqg.AlarmQueryGenerator }



class Learner(object):
    """
     Takes in a schema and distributions, pairs the schema line with a query_type and 
     a distribution object with a field and creates the associated instance of the 
     query object, which it then adds to the list, when it is done processing the 
     schema file it returns the list as an object
     
     An example of a line in csv file would be:
     cat, sub_cat, performer,          field,                "['no_queries','result_set_size']"
     EQ,  eq,      "['IBM1','IBM2', 'COL']","['fname','lname']", "[100,(1,10)]", "[20,(11,100)]", "[10,(101,1000...
     ...
     """
    def __init__(self, dist_holder, schema_handle, db_size, row_width):
        
        self.__query_objects = []
        #unpickling distributions
        self.__dist_holder = dist_holder
        
        #process and and pair csv file
        reader = csv.reader(schema_handle)
        row_num = 0
        for row in reader:
            #strip of trailing empty columns
            row = [x for x in row if x != '']
            #store the other column headers
            if row[0] == '*':
                row_num = -1
            elif row_num == 0:
                other_fields = literal_eval(row[4])
            else:
                col_num = 0
                other_cols = []
                for col in row:
                    if col_num == 0:
                        cat = col
                    elif col_num == 1:
                        sub_cat = col
                    elif col_num == 2:
                        perf = literal_eval(col)
                    elif col_num == 3:
                        fields = literal_eval(col)
                    else:
                        other_cols.append(literal_eval(col))
                    col_num +=1
                obj = self.__create_query_object(cat, sub_cat, perf, fields, other_fields, 
                                                other_cols, db_size, row_width)
                self.__query_objects.append(obj)
            row_num +=1

                
    def __create_query_object(self, cat, sub_cat, perf, fields, other_fields, other_cols, db_size,
                              row_width):
        """
        Args:
             *sub_cat: the catagory of the query, all are keys within QUERY_TYPES
             *fields: the fields that this query relies on
             *other_fields: list of headers such as the number of queries to generate and 
              the size of a range, this varies for different query types, and this class
              doesn't really care what they are
             *other_cols: a list of values for other columns, corresponds the the headers
              see above for example
             *db_size: size of the db that is being run against. 
        Returns:
             Query object
        """
        type_class = QUERY_SUBCAT[sub_cat]
        if fields[0] == "ALL":
            fields = self.__dist_holder.dist_dict.keys()
            dists = self.__dist_holder.dist_dict.values()
        else:
            fields = map(sv.sql_name_to_enum, fields)
            dists = [self.__dist_holder.dist_dict[field] for field in fields]
        return type_class(cat,sub_cat, perf, dists, fields, db_size, row_width,
                                               other_fields, other_cols)


    def generate_query_objects(self):
        """
        Returns:
             The list of processed query objects
        """
        return self.__query_objects

