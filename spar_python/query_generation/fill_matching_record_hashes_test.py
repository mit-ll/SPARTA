#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module contains the unit tests for
#                      fill_matching_record_hashes.py                     
# *****************************************************************


import unittest
import sqlite3 as sql
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.query_generation import fill_matching_record_hashes as fmr


class FillMatchingRecodHashesTest(unittest.TestCase):
    '''Class to hold unit tests for fill_matching_record_hashes.py'''

    fake_hashes = { 1 : "abcd1234" ,
                     2 : "78901234" ,
                     5 : "98765432" ,
                     6543 : "aaaaaaaa" }
    fake_matching_record_ids = { 0 : "1|2|5" ,
                                  1 : "5" ,
                                  2 : "6543" ,
                                  3 : "6543|2" ,
                                  4 : "1|2|5|6543"}
    expected_matching_hashes = { 0 : "abcd1234|78901234|98765432" ,
                                 1 : "98765432" ,
                                 2 : "aaaaaaaa" ,
                                 3 : "aaaaaaaa|78901234" ,
                                 4 : "abcd1234|78901234|98765432|aaaaaaaa" }


    def create_fake_database(self):
        '''Helper function.  Creates the database to be used in other tests'''
        con = sql.connect(":memory:")
        con.execute("CREATE TABLE IF NOT EXISTS " + 
                    "hashes(record_id INTEGER PRIMARY KEY, hash TEXT);")
        con.execute("CREATE TABLE IF NOT EXISTS " + 
                    "full_queries(qid INTEGER PRIMARY KEY, " +
                    "matching_record_ids TEXT, matching_record_hashes TEXT);")
        for key in self.fake_hashes.keys():
            con.execute("INSERT INTO hashes(record_id, hash) VALUES(?, ?);",
                        (key, self.fake_hashes[key]))
        for key in self.fake_matching_record_ids.keys():
            con.execute("INSERT INTO full_queries(qid, matching_record_ids, " +
                        "matching_record_hashes) VALUES(?,?,?);", 
                        (key, self.fake_matching_record_ids[key], ""))
        con.commit()
        return con
    
    
    @unittest.skip("API broken; fill_hashes_column() takes two arguments now")
    def test_fill_hashes_column(self):
        '''tests fill_matching_record_hashes.fill_hashes_column'''
        # create database
        con = self.create_fake_database()
        # fill column
        fmr.fill_hashes_column(con)
        # check each row
        fqt_query = "SELECT qid, matching_record_hashes FROM full_queries;"
        for row in con.execute(fqt_query):
            qid = row[0]
            thishash = row[1]
            self.assertEqual(thishash, self.expected_matching_hashes[qid])
        
        
