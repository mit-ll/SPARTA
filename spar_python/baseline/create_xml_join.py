#!/usr/bin/env python
# *****************************************************************
#  Copyright 2014 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module creates the xml join tables
#                      to make xml searches faster (post-generation)
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)


import argparse
import datetime
import MySQLdb
from lxml import etree


def create_xml_join_table(con):
    '''Creates the join tables
    
    Inputs:
    con: database connection

    returns: nothing
    '''
    create_command = "CREATE TABLE IF NOT EXISTS xml_join" + \
    "(id BIGINT UNSIGNED NOT NULL, field CHAR(30) NOT NULL, " + \
    "path CHAR(255) NOT NULL, value CHAR(255) NOT NULL) " + \
    "ENGINE = MyISAM PARTITION BY KEY(id) PARTITIONS 10;"
    index_command = "CREATE INDEX xml_join ON xml_join(id, field, path, value)"

    cur = con.cursor()
    cur.execute(create_command)
    #cur.execute(index_command)
    
    
def fill_xml_join_table(con, limit, offset):
    '''Fills the join tables (alarms, keywords, stems)
    
    Inputs:
    con: database connection
    
    Returns: nothing
    '''
    
    # get cursor
    cur = con.cursor()
    # retrieve xml field
    print "Calling SELECT: ", datetime.datetime.now()
    cur.execute("SELECT id, xml FROM base" + \
                " ORDER BY id LIMIT " + limit + " OFFSET " + offset)
    print "SELECT retuned: ", datetime.datetime.now()

    for row in cur:        
        id = row[0]
        tag_values = get_xml_tag_value_pairs(row[1])
        do_xml_join_insert(con, id, tag_values)
        

def do_xml_join_insert(con, id, tag_values):
    '''Does the actual join table insertion

    Inputs: con: database connection
    id: row id (as a string)
    tag_values: a list (xml_tag, xml_value) tuples

    Returns: nothing'''

    cur = con.cursor()
    #insert_statement = "INSERT DELAYED INTO xml_join"  \
    #    "(id, field, path, value) VALUES(%s, %s, %s, %s)"

    # MyIASM doesn't support transactions, so for speed
    # build a large insert statement
    # on sparllan04 going from (10K * 125) single inserts
    # to (10K) (125-value inserts) cut running time from
    # 140 seconds to 15 seconds
    values = "INSERT INTO xml_join(id, field, path, value) VALUES"
    for (t, v) in tag_values:
        values += '(%d,"%s","%s","%s"),' % (id, "xml", t, v)
        #cur.execute(insert_statement, (id, "xml", t, v))
    # "values: has a trailing comma, so remove that comma
    cur.execute(values[:-1])


def get_xml_tag_value_pairs(data):
    '''Takes in an xml document as a string and returns
    a list of (tag, value) tuples.  The tags will be 
    full-path tags, the values will be non-empty

    Inputs: data: an xml document as a string
    Returns: a list of (tag, value) tuples
    '''

    result = []
    root = etree.XML(data)
    parse_xml(root, "", result)
    return result
    

def parse_xml(elem, elem_path, result):
    for child in elem:
        if child.text:
            #  node with text => print
            result.append(("%s/%s" % (elem_path, child.tag), child.text))
        if child.getchildren():
            # node with child elements => recurse
            parse_xml(child, "%s/%s" % (elem_path, child.tag), result)



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
    create_xml_join_table(con)
    fill_xml_join_table(con, options.limit, options.offset)    
    print "Finished: ", datetime.datetime.now()

if __name__ == "__main__":
    main()