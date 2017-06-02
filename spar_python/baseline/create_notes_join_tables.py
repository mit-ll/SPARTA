#!/usr/bin/env python
# *****************************************************************
#  Copyright 2014 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module creates the notes join tables
#                      (alarms, keywords, stems)
#                      after the data has already been generated
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.baseline.create_alarms_join as alarms
import spar_python.baseline.create_keywords_stems_join as ks
from spar_python.external.porterstemmer.stemmer import PorterStemmer as PorterStemmer 

import argparse
import datetime
import MySQLdb


def create_join_tables(con):
    '''Creates the join tables
    
    Inputs:
    con: database connection

    returns: nothing
    '''
    alarms.create_alarm_join_table(con)
    ks.create_keywords_stems_join_table(con)
    
def fill_join_tables(con, limit, offset):
    '''Fills the join tables (alarms, keywords, stems)
    
    Inputs:
    con: database connection
    limit: number of entries to handle in this call
    offset: offset within database to start at
    
    Returns: nothing
    '''
    
    # make a stemmer
    stemmer = PorterStemmer()
    stems_dict = {}
    # get cursor
    cur = con.cursor()
    # retrieve notes fields
    print "Calling select:  ", datetime.datetime.now()
    cur.execute("SELECT id, notes1, notes2, notes3, notes4 FROM notes " + \
                "ORDER BY id LIMIT " + limit + " OFFSET " + offset)
    print "Select returned: ", datetime.datetime.now()

    #ks_statements = []
    for row in cur:
        alarms.fill_alarms_join_table(con, row)
        #ks_statements += ks.fill_keywords_stems_join_table(con, row, stemmer, stems_dict)
        ks.fill_keywords_stems_join_table(con, row, stemmer, stems_dict)
    #print "finished inserting rows: ", datetime.datetime.now()
    #print "Have keyword/stem statements, about to insert: ", datetime.datetime.now()
    #for statement in ks_statements:
    #    cur.execute(statement)
    print "finished: ", datetime.datetime.now()

def main():   
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', dest = 'user',
          type = str, required = True,
          help = 'db username')
    parser.add_argument('-p', '--pass', dest = 'passwd',
          type = str, required = True,
          help = 'db password')
    parser.add_argument('-s', '--server', dest = 'host',
          type = str, required = True,
          help = 'server where the database lives ("localhost")')
    parser.add_argument('-d', '--db', dest = 'db',
          type = str, required = True,
          help = 'name of the db')
    parser.add_argument('-l', '--limit', dest = 'limit',
          type = str, required = True,
          help = 'number of entries to handle in this run')
    parser.add_argument('-o', '--offset', dest = 'offset',
          type = str, required = True,
          help = 'where in the database to start in this run')
    
    options = parser.parse_args()
    
    con = MySQLdb.connect(user=options.user, passwd=options.passwd, host=options.host, db=options.db)
    create_join_tables(con)
    fill_join_tables(con, options.limit, options.offset)    

if __name__ == "__main__":
    main()
