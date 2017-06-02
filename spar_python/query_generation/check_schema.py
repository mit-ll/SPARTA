# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Checks query_schema format
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  27 August 2013  ATLH            Original file
# *****************************************************************

"""
Takes in a file and parses it, checking to see that all associated 
requirements for the query schema are met
"""

from __future__ import division 
import os
import sys
import csv
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.query_generation.query_ids as qids
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
from ast import literal_eval
import logging

logger = logging.getLogger(__name__)


PERF = ["LL","COL","IBM1","IBM2"]    
CATS = ['EQ','P1','P2','P3','P4','P6','P7','P8','P9','P11']
OTHER_COLS = { ('EQ','eq') : [['no_queries','r_lower','r_upper']],
               ('EQ','ta2') :  [['no_queries','r_lower','r_upper','range']],
               ('P1','eq-and') : [['no_queries','r_lower','r_upper','num_clauses','tm_lower','tm_upper']],
               ('P1','ta2') :  [['no_queries','r_lower','r_upper','range']],
               ('P1','eq-or') : [['no_queries','r_lower','r_upper','num_clauses','tm_lower','tm_upper']],
               ('P2','foo-range') : [['no_queries','r_lower','r_upper','r_exp_lower','r_exp_upper','type']],
               ('P2','foo-greater') : [['no_queries','r_lower','r_upper','r_exp_lower','r_exp_upper','type']],
               ('P2','range') : [['no_queries','r_lower','r_upper','type']],
               ('P2','ta2') :  [['no_queries','r_lower','r_upper','range']],
               ('P3','word') : [['no_queries','rss','keyword_len','type'],
                                ['no_queries','r_lower','r_upper','keyword_len','type']],
               ('P4','stem') : [['no_queries','rss','keyword_len','type'],
                                ['no_queries','r_lower','r_upper','keyword_len','type']],
               ('P6','wildcard') : [['no_queries','rss','keyword_len','type'],
                                ['no_queries','r_lower','r_upper','keyword_len','type']],
               ('P7','wildcard') : [['no_queries','rss','keyword_len','type'],
                                ['no_queries','r_lower','r_upper','keyword_len','type']],
               ('P8','threshold') : [['no_queries','r_lower','r_upper','m','n','tm_lower','tm_upper']],
               ('P9','alarm') : [['no_queries','r_lower','r_upper','distance']],
               ('P11','xml') :  [['no_queries', 'r_lower', 'r_upper', 'path_type']]}
VALID_FIELDS = {'EQ' : ['fname','lname','ssn','address','city',
                        'zip','dob','income','foo','last_updated','language'],
                'P1' : ['ALL','fname','lname','income','dob','hours_worked_per_week',
                        'weeks_worked_last_year','citizenship','race','state','zip',
                        'last_updated','foo'],
                'P2' : ['foo','fname','lname','ssn','dob',
                        'address','city','zip','income','last_updated',
                        'hours_worked_per_week','weeks_worked_last_year'],
                'P3' : ['notes1','notes2','notes3','notes4'],
                'P4' : ['notes1','notes2','notes3','notes4'],
                'P6' : ['fname','city','lname','address'],
                'P7' : ['fname','city','lname','address',
                        'notes1','notes2','notes3','notes4'],
                'P8' : ['ALL'],
                'P9' : ['notes1','notes2','notes3'],
                'P11' : ['xml'] }

def check_other_fields_format(row, cat, sub_cat, template, total_row, db_size):
    
    #check r_lower, r_upper, rss
    try:
      r_lower = template['r_lower']
      r_upper = template['r_upper']
    except KeyError:
      r_lower = template['rss']
      r_upper = template['rss']
    
    if r_upper < r_lower or r_upper > db_size:
        logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
        logger.warning("ILL-FORMED QUERY SCHEMA: Row %d r_upper (%d) and r_lower (%d) will not work" % (total_row, 
                                                                                                        r_upper,
                                                                                                        r_lower))
        exit()
    if sub_cat == 'ta2':
        if (cat,template['range']) not in [('P1','range'),('P2','range'),('P1','greater'),('P2','greater'),
                                           ('P1','less'),('P2','less'),('EQ','none'),('P1','none')]:
            logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
            logger.warning("ILL-FORMED QUERY SCHEMA: Row %d range of type %s is not correct for cat %s" % (total_row, 
                                                                                                template['range']),
                                                                                                cat)
            exit()
    elif cat in ['P1','P8']:
        if r_upper > template['tm_upper'] or template['tm_upper'] > db_size:
            logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
            logger.warning("ILL-FORMED QUERY SCHEMA: Row %d r_upper (%d) and tm_upper (%d) will not work" % (total_row, 
                                                                                                        r_upper,
                                                                                                template['tm_upper']))
            exit()
            
        elif (cat == 'P1' and template['num_clauses'] > 6) or (cat == "P8" and template['m'] > 6):
            logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
            logger.warning("ILL-FORMED QUERY SCHEMA: Row %d clause number or m must be less than 6" % (total_row))
            exit()
            
        if cat == 'P8' and template['m'] > template['n']:
            logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
            logger.warning("ILL-FORMED QUERY SCHEMA: Row %d m must be less than n" % (total_row))
            exit()
            
    elif cat in ['P2','P3','P4','P6','P7']:
        if template['type'] not in ['range','greater','less','word','stem','initial-one','final-one','middle-one',
                                    'both','initial','final']:
            logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
            logger.warning("ILL-FORMED QUERY SCHEMA: Row %d type %s is not supported" % (total_row, template['type']))
            exit()
    elif cat == 'P9': 
        if template['distance'] < 0: 
            logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
            logger.warning("ILL-FORMED QUERY SCHEMA: Row %d distance %d is not appropriate" % (total_row, template['type']))
            exit()
    elif cat == 'P11':
        if template['path_type'] not in ['full','short']:
            logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
            logger.warning("ILL-FORMED QUERY SCHEMA: Row %d type %s is not supported" % (total_row, template['path_type']))
            exit()


def check_format(schema_handle, db_size):
    #process and and pair csv file
    reader = csv.reader(schema_handle)
    row_num = 0
    total_row = 1
    for row in reader:
        #strip of empty columns
        row = [x for x in row if x != '']
        #store the other column headers
        if row[0] == '*':
            row_num = -1
        elif row_num == 0:
           other_fields = literal_eval(row[4]);
        else:
           #store content into columns
           col_num = 0
           other_cols = []
           for col in row:
               if col_num == 0:
                   cat = col
               elif col_num == 1:
                   sub_cat = col
               elif col_num == 2:
                   try:
                       perf = literal_eval(col)
                   except SyntaxError as e:
                       logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
                       logger.warning("ILL-FORMED QUERY SCHEMA: Row %d Performer syntax is not valid %s" % (total_row, e))  
                       exit()
               elif col_num == 3:
                   fields = literal_eval(col)
               else:
                   other_cols.append(literal_eval(col))
               col_num +=1
           #check to see that the category is appropriate
           if not cat in CATS:
               logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
               logger.warning("ILL-FORMED QUERY SCHEMA: Row %d Category is not correct: %s" %(total_row, cat))
               exit()
           #check to see that the performer is supported
           for p in perf:
               if not p in PERF:
                   logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
                   logger.warning("ILL-FORMED QUERY SCHEMA: Row %d Performer is not valid %s" % (total_row, p))
                   exit()
           #check to see the other fields work for the combination of category and sub_category
           if not other_fields in OTHER_COLS[(cat,sub_cat)]:
               logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
               logger.warning("ILL-FORMED QUERY SCHEMA: Row %d Other_columns is not valid %s" % (total_row, other_fields))
               exit()
           #check to see that the field is currently supported for the category
           for field in fields:
               if not field in VALID_FIELDS[cat]:
                   logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
                   logger.warning("ILL-FORMED QUERY SCHEMA: Row %d Field %s is not valid" % (total_row, field))
                   exit()
           #check the other columns
           for cols in other_cols:
               try:
                  dicts = dict(zip(other_fields, cols))
               except SyntaxError as e:
                  logger.warning("ILL_FORMED QUERY SCHEMA: Row %d is %s" %(total_row, row))
                  logger.warning("ILL-FORMED QUERY SCHEMA: Row %d Other_cols is not valid %s" % (total_row, e))
                  exit()        
               check_other_fields_format(row, cat, sub_cat, dicts, total_row, db_size)
        total_row +=1   
        row_num +=1
            

    