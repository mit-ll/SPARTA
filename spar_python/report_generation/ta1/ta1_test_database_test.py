# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests ta1_main_methods.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  16 Aug 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.report_generation.ta1.ta1_test_database as t1td

class TA1TestDatabaseTest(unittest.TestCase):

    def test_get_db_num_records_str(self):
        sdns = {}
        testdb = t1td.TestDatabase(
            short_database_names=sdns, db_num_records=100, db_record_size=None)
        self.assertEqual(testdb.get_db_num_records_str(), "$10^{2}$")
        testdb = t1td.TestDatabase(
            short_database_names=sdns, db_num_records=8, db_record_size=None)
        self.assertEqual(testdb.get_db_num_records_str(), "8")

    def test_get_db_record_size_str(self):
        sdns = {}
        testdb = t1td.TestDatabase(
            short_database_names=sdns, db_num_records=None, db_record_size=100)
        self.assertEqual(testdb.get_db_record_size_str(), "$10^{2}$B")
        testdb = t1td.TestDatabase(
            short_database_names=sdns, db_num_records=None, db_record_size=8)
        self.assertEqual(testdb.get_db_record_size_str(), "8B")
        
    def test_get_database_name(self):
        sdns = {}
        testdb = t1td.TestDatabase(
            short_database_names=sdns, db_num_records=10, db_record_size=2)
        self.assertEqual(testdb.get_database_name(),
                         "Database with $10^{1}$ Rows, Each of Size 2B")
        self.assertEqual(testdb.get_database_name(lower=True),
                         "database with $10^{1}$ rows, each of size 2B")

    def test_get_short_database_name(self):
        sdns = {(100, 10): "MainDB"}
        testdb = t1td.TestDatabase(
            short_database_names=sdns, db_num_records=100, db_record_size=10)
        self.assertEqual(testdb.get_short_database_name(), "MainDB")
        self.assertEqual(testdb.get_short_database_name(lower=True), "maindb")

