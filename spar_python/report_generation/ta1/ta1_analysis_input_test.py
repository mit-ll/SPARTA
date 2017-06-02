# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests the Ta1AnalysisInput class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  13 Sep 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest
import sys
import os

# SPAR imports:
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_config as config
import spar_python.report_generation.ta1.ta1_test_database as t1tdb
import spar_python.common.spar_random as sr
import spar_python.data_generation.spar_variables as sv

class Ta1AnalysisInputTest(unittest.TestCase):

    def test_get_constraint_list(self):
        inp = t1ai.Input()
        inp[t1s.DBF_NUMRECORDS] = 800
        cat = t1s.CATEGORIES.to_string(t1s.CATEGORIES.EQ)
        inp[t1s.DBF_CAT] = cat
        expected_constraint_list = [
            (t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS, 800),
            (t1s.DBF_TABLENAME, t1s.DBF_CAT, cat)]
        actual_constraint_list = inp.get_constraint_list()
        self.assertEquals(expected_constraint_list, actual_constraint_list)
        
    def test_get_complete_constraint_list(self):
        db_num_records = 800
        db_record_size = 10
        cat = t1s.CATEGORIES.to_string(t1s.CATEGORIES.P1)
        subcat = t1s.SUBCATEGORIES[
            t1s.CATEGORIES.P1].to_string(
                t1s.SUBCATEGORIES[t1s.CATEGORIES.P1].eqcnf)
        subsubcat = sr.choice(t1s.SUBSUBCATEGORIES[
            (t1s.CATEGORIES.P1, t1s.SUBCATEGORIES[
                t1s.CATEGORIES.P1].eqcnf)])
        selection_cols = sr.choice(t1s.SELECTION_COLS)
        field = sr.choice(sv.VARS.numbers_list())
        inp = t1ai.Input()
        inp[t1s.DBF_NUMRECORDS] = db_num_records
        inp[t1s.DBF_RECORDSIZE] = db_record_size
        inp[t1s.DBF_CAT] = cat
        inp[t1s.DBF_SUBCAT] = subcat
        inp[t1s.DBF_SUBSUBCAT] = subsubcat
        inp[t1s.DBP_SELECTIONCOLS] = selection_cols
        inp[t1s.DBA_FIELD] = field
        expected_constraint_list = [
            (t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS, db_num_records),
            (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE, db_record_size),
            (t1s.DBF_TABLENAME, t1s.DBF_CAT, cat),
            (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT, subcat),
            (t1s.DBF_TABLENAME, t1s.DBF_SUBSUBCAT, subsubcat),
            (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols),
            (t1s.DBA_TABLENAME, t1s.DBA_FIELD, field)]
        actual_constraint_list = inp.get_constraint_list()
        self.assertEquals(expected_constraint_list, actual_constraint_list)

    def test_get_test_database(self):
        db_num_records = 800
        db_record_size = 10
        inp = t1ai.Input()
        inp[t1s.DBF_NUMRECORDS] = db_num_records
        inp[t1s.DBF_RECORDSIZE] = db_record_size
        self.assertEquals(inp.test_db, t1tdb.TestDatabase(
            short_database_names=config.SHORT_DATABASE_NAMES,
            db_num_records=db_num_records, db_record_size=db_record_size))
