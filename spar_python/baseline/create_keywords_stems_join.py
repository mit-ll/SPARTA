#!/usr/bin/env python
# *****************************************************************
#  Copyright 2014 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module creates the keywords words index
#                      after the data has already been generated
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import argparse
from spar_python.baseline.default_stopwords import default_stopwords_list as default_stopwords

import re


def get_keywords_stems_insert_data(id, column, note, stemmer, stems_dict,
                stopwords=default_stopwords):
    '''Takes a notes field entry, list of stopwords, and a stemmer
    and generates a list of tuples for insertion into the keywords 
    and stems join tables
    
    Arguments:
    id: the rows id corresponding to the note
    column: the name of the corresponding column ("notes1")
    note: a string containing the contents of a notes field
        ("Twas brillig, and the slithy toves...")
    stemmer: an initalized PorterStemmer object
    stems_dict: a dict of (word, stem) pairs, to keep from having to
        re-stem when we already know the result
    stopwords: a list of stopwords (default: default_stopwords)
    
    Returns: (keyword) and (stem) tuples appropriate for MySQLdb.execute()
    '''
    
    # get a list of all words in the note
    regex = re.compile('[ .!?;,-]')
    all_words = regex.split(note)
    
    # keywords = all words without empty strings and stopwords
    keywords = set(word.lower() for word in all_words)
    #for word in all_words:
    #    if word == '':
    #        continue
    keywords.discard('')
    #    if word.lower() in stopwords:
    #        continue
    #    keywords.add(word.lower())
    # create list of tuples (id, col, word)
    for word in stopwords:
        keywords.discard(word.lower())
    keyword_tuples = [(id, column, word) for word in keywords]

    # create list of all stems
    # note that all only keywords are stemmed
    #all_stems = [stemmer.stem(word, 0, len(word)-1) for word in keywords]
    unique_stems = set()
    for word in keywords:
        try:
            unique_stems.add(stems_dict[word])
        except KeyError:
            st = stemmer.stem(word, 0, len(word)-1)
            unique_stems.add(st)
            stems_dict[word] = st
    
    stem_tuples = [(id, column, stem) for stem in unique_stems]

    return keyword_tuples, stem_tuples


def fill_keywords_stems_join_table(con, row, stemmer, stems_dict, stopwords=default_stopwords, 
                kw_table_name="keywords", st_table_name="stems"):
    '''Fill keywords and stems join tables
    
    Inputs: 
    con: a database connection
    row: a row from the notes table (id, notes1, notes2, notes3, notes4)
    stemmer: an instance of PorterStemmer
    stopwords: list of stopwords (default: default_stopwords)
    kw_table_name: name of the keywords join table (default: keywords)
    st_table_name: name of the stems join table (default: stems)
    '''
    id = row[0]
    notes1 = row[1]
    notes2 = row[2]
    notes3 = row[3]
    notes4 = row[4]
        
    (k1, s1) = get_keywords_stems_insert_data(id, "notes1", notes1, stemmer, stems_dict, stopwords)
    (k2, s2) = get_keywords_stems_insert_data(id, "notes2", notes2, stemmer, stems_dict, stopwords)
    (k3, s3) = get_keywords_stems_insert_data(id, "notes3", notes3, stemmer, stems_dict, stopwords)
    (k4, s4) = get_keywords_stems_insert_data(id, "notes4", notes4, stemmer, stems_dict, stopwords)

    for k in [k1, k2, k3, k4]:
        if (len(k)): #if there is anything to insert
            do_keywords_stems_join_insert(con, k, kw_table_name)
    for s in [s1, s2, s3, s4]:
        if (len(s)): #if there is anything to insert
            do_keywords_stems_join_insert(con, s, st_table_name)
 
def do_keywords_stems_join_insert(con, values, table_name):
    '''Does the keywords/stems table insertion
    
    Inputs:
    con: database connection
    value: list of tuples of values (id, col, word) 
    table_name: name of join table
    
    returns: nothing
    '''
    #insert_statement = "INSERT INTO " + table_name + \
    #    "(id, col, word) VALUES(%s, %s, %s)"

    # do a mult-insert for speed
    insert_statement = "INSERT INTO " + table_name + \
        "(id, col, word) VALUES"
    for v in values:
        insert_statement += '(%d,"%s","%s"),' % v
    #con.cursor().executemany(insert_statement, values)
    con.cursor().execute(insert_statement[:-1])
  

def create_keywords_stems_join_table(con, kw_table_name="keywords", 
                                     st_table_name="stems"):
    '''Creates the keywords and stems index tables.
    
    inputs:
    con: database connection
    kw_table_name: name of the keywords join table (default="keywords")
    st_table_name: name of the stems join table (default="stems")
    
    returns:
    nothing
    '''
    
    create_command = "CREATE TABLE IF NOT EXISTS %s" + \
        "(id BIGINT UNSIGNED NOT NULL, col CHAR(30) NOT NULL, " + \
        "word CHAR(30) NOT NULL) " + \
        "ENGINE = MyISAM PARTITION BY KEY(id) PARTITIONS 10;"
    index_command = "CREATE INDEX id ON %s(id)"

    cur = con.cursor()        
    cur.execute(create_command % kw_table_name)
    cur.execute(create_command % st_table_name)    
    # Save index creation for later, to time insertion
    #cur.execute(index_command % kw_table_name)
    #cur.execute(index_command % st_table_name)


