#!/usr/bin/env python
# *****************************************************************
#  Copyright 2014 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module creates the alarm words index
#                      after the data has already been generated
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import argparse
from spar_python.baseline.default_alarm_words import default_alarm_word_list as default_alarms


def get_alarm_insert_statement(id, column, note, alarm_word_list=default_alarms, table_name="alarms"):
    '''Takes a notes field entry, and list of alarm words, and generates
    values for insertion into the alarms join table
    
    Arguments:
    id: the rows id corresponding to the note
    column: the name of the corresponding column ("notes1")
    note: a string containing the contents of a notes field
        ("Twas brillig, and the slithy toves...")
    alarm_word_list: a list of alarm words, (default: default_alarm_words)
    table_name: the name of the index table, (default="alarms")
    
    Returns: an tuple appropriate for MySQLdb.execute() if there are 
    2 alarm words, or None if there are none'''
    
    # alarms are to be case-insensitive -- convert note to lower case
    lower_note = note.lower()
    
    # Get matching entries
    matching_words = [w for w in alarm_word_list if w.lower() in lower_note]
    
    # if there are less than 2 matches, nothing to insert
    if len(matching_words) < 2:
        return None

    # ensure that the matches are full word matches, and not sub-string matches
    # (ie, we don't match 'own' in the word 'brown')
    final_matches = [w for w in alarm_word_list if ''.join([' ', w.lower(), ' ']) in lower_note]
    if (len(final_matches) != 2):
        return None
    
    # Distance is the number of bytes between the end of then
    # First word and the beginning of the last word
    # First, take the absolute value of the difference in their locations
    location0 = lower_note.find(final_matches[0].lower())
    location1 = lower_note.find(final_matches[1].lower())
    distance = abs(location0 - location1)
    # Then, subtract the length of the first word
    if (location0 < location1): 
        distance -= len(final_matches[0])
    else:
        distance -= len(final_matches[1])
    
    # INSERT statement will be of the form:
    # INSERT INTO alarms(id, word1, word2, field, distance) VALUES(...) 
    return (id, final_matches[0], final_matches[1], column, distance)



def fill_alarms_join_table(con, row, word_list=default_alarms, table_name="alarms"):
    '''Fill alarms index table
    
    Inputs: 
    con: a database connection
    row: a row from the notes table (id, notes1, notes2, notes3, notes4)
    word_list: list of alarm words (default: default_alarm_words)
    table_name: name of the index table (default: alarms)
    '''
    id = row[0]
    notes1 = row[1]
    notes2 = row[2]
    notes3 = row[3]
    notes4 = row[4]
        
    list1 = get_alarm_insert_statement(id, "notes1", notes1, word_list, table_name)
    list2 = get_alarm_insert_statement(id, "notes2", notes2, word_list, table_name)
    list3 = get_alarm_insert_statement(id, "notes3", notes3, word_list, table_name)
    list4 = get_alarm_insert_statement(id, "notes4", notes4, word_list, table_name)

    for l in [list1, list2, list3, list4]:
        if (l):
            do_alarm_join_insert(con, l)




def do_alarm_join_insert(con, values, table_name="alarms"):
    '''Does the alarm table insertion
    
    Inputs:
    con: database connection
    value: tuple of values (id, word1, word2, column, distance)
    table_name: name of index table (default: alarms)
    
    returns: nothing
    '''
    insert_statement = "INSERT INTO " + table_name + \
        "(id, word1, word2, field, distance) VALUES(%s, %s, %s, %s, %s)"
    con.cursor().execute(insert_statement, values)

def create_alarm_join_table(con, table_name="alarms"):
    '''Creates the alarms index table.
    
    inputs:
    con: database connection
    table_name: name of the input table (default="alarms")
    
    returns:
    nothing
    '''
    
    create_command = "CREATE TABLE IF NOT EXISTS " + table_name + \
        "(id BIGINT UNSIGNED NOT NULL, word1 CHAR(30) NOT NULL, " + \
        "word2 CHAR(30) NOT NULL, field CHAR(30) NOT NULL, " + \
        "distance INT NOT NULL) " + \
        "ENGINE = MyISAM PARTITION BY KEY(id) PARTITIONS 10;"
    index_command = "CREATE INDEX alarms ON %s(id, word1, word2, field, distance)" % table_name

    cur = con.cursor()        
    cur.execute(create_command)    
    #cur.execute(index_command)


