# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests the results database.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  16 Oct 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.report_generation.common.results_database as results_database
import spar_python.report_generation.ta1.ta1_schema as t1s
from spar_python.report_generation.ta1.ta1_database_test import set_up_static_db

BASELINE_NAME = "baseline"
PERFORMER_NAME = "white knight"
TESTCASEID1 = "TC001"
TESTCASEID2 = "TC002"

class ResultsDatabaseTest(unittest.TestCase):

    def setUp(self):
        self.database = results_database.ResultsDB(
            db_path=":memory:", schema=t1s.Ta1ResultsSchema())
        set_up_static_db(self.database)

    def tearDown(self):
        self.database.close()

    def test_to_values_list(self):
        list_of_tuples = [(1, "nose", 6.2), (2, "ears", 7.4)]
        values_list = [[1, 2], ["nose", "ears"], [6.2, 7.4]]
        self.assertEqual(self.database.to_values_list(list_of_tuples),
                         values_list)

    def test_build_constraint(self):
        static_constraint = "%s.%s=10 AND %s.%s='age=24'" % (
            t1s.DBA_TABLENAME, t1s.DBA_AQID, t1s.DBA_TABLENAME,
            t1s.DBA_WHERECLAUSE)
        generated_constraint = self.database.build_constraint(
            [(t1s.DBA_TABLENAME, t1s.DBA_AQID, 10),
             (t1s.DBA_TABLENAME, t1s.DBA_WHERECLAUSE, "age=24")])
        self.assertEqual(generated_constraint, static_constraint)

    def test_build_query_cmd(self):
        fields = [(t1s.DBA_TABLENAME, t1s.DBA_WHERECLAUSE),
                  (t1s.DBA_TABLENAME, t1s.DBA_AQID)]
        constraint_list = [(t1s.DBA_TABLENAME, t1s.DBA_AQID, 1)]
        static_cmd = ("SELECT " + t1s.DBA_TABLENAME + "." + t1s.DBA_WHERECLAUSE
                      + ", " + t1s.DBA_TABLENAME + "." + t1s.DBA_AQID +
                      " FROM " + t1s.DBA_TABLENAME + 
                      " WHERE " + t1s.DBA_TABLENAME + "." + t1s.DBA_AQID + "=1")
        generated_cmd = self.database.build_query_cmd(fields, constraint_list)
        self.assertEqual(generated_cmd, static_cmd)

    def test_add(self):
        fqid1 = 100
        frow1 = {t1s.DBF_FQID: fqid1,
                 t1s.DBF_CAT: "Eq",
                 t1s.DBF_NUMRECORDS: 1000,
                 t1s.DBF_RECORDSIZE: 100,
                 t1s.DBF_WHERECLAUSE: 'fname="Grettle"'}
        prow1 = {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                 t1s.DBP_TESTCASEID: TESTCASEID1,
                 t1s.DBP_FQID: fqid1,
                 t1s.DBP_SELECTIONCOLS: "id",
                 t1s.DBP_SENDTIME: 123.00,
                 t1s.DBP_RESULTSTIME: 128.00,
                 t1s.DBP_QUERYLATENCY: 5.00,
                 t1s.DBP_ISMODIFICATIONQUERY: False,
                 t1s.DBP_ISTHROUGHPUTQUERY: False}
        fqid2 = 200
        frow2 = {t1s.DBF_FQID: fqid2,
                 t1s.DBF_CAT: "Eq",
                 t1s.DBF_NUMRECORDS: 1000,
                 t1s.DBF_RECORDSIZE: 100,
                 t1s.DBF_WHERECLAUSE: 'fname="Hansel"'}
        prow2 = {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                 t1s.DBP_TESTCASEID: TESTCASEID1,
                 t1s.DBP_FQID: fqid2,
                 t1s.DBP_SELECTIONCOLS: "id",
                 t1s.DBP_SENDTIME: 128.00,
                 t1s.DBP_RESULTSTIME: 130.00,
                 t1s.DBP_QUERYLATENCY: 5.00,
                 t1s.DBP_ISMODIFICATIONQUERY: False,
                 t1s.DBP_ISTHROUGHPUTQUERY: False}
        self.database.add_row(t1s.DBF_TABLENAME, frow1)
        self.database.add_row(t1s.DBF_TABLENAME, frow2)
        self.database.add_row(t1s.DBP_TABLENAME, prow1)
        self.database.add_row(t1s.DBP_TABLENAME, prow2)
        all_fqids = self.database.get_unique_values(
            fields=[(t1s.DBP_TABLENAME, t1s.DBP_FQID)])
        self.assertTrue(fqid1 in all_fqids)
        self.assertTrue(fqid2 in all_fqids)
        
    def test_add_two_rows(self):
        fqid1 = 100
        frow1 = {t1s.DBF_FQID: fqid1,
                 t1s.DBF_CAT: "Eq",
                 t1s.DBF_NUMRECORDS: 1000,
                 t1s.DBF_RECORDSIZE: 100,
                 t1s.DBF_WHERECLAUSE: 'fname="Grettle"'}
        prow1 = {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                 t1s.DBP_TESTCASEID: TESTCASEID1,
                 t1s.DBP_FQID: fqid1,
                 t1s.DBP_SELECTIONCOLS: "id",
                 t1s.DBP_SENDTIME: 123.00,
                 t1s.DBP_RESULTSTIME: 128.00,
                 t1s.DBP_QUERYLATENCY: 5.00,
                 t1s.DBP_ISMODIFICATIONQUERY: False,
                 t1s.DBP_ISTHROUGHPUTQUERY: False}
        fqid2 = 200
        frow2 = {t1s.DBF_FQID: fqid2,
                 t1s.DBF_CAT: "Eq",
                 t1s.DBF_NUMRECORDS: 1000,
                 t1s.DBF_RECORDSIZE: 100,
                 t1s.DBF_WHERECLAUSE: 'fname="Hansel"'}
        prow2 = {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                 t1s.DBP_TESTCASEID: TESTCASEID1,
                 t1s.DBP_FQID: fqid2,
                 t1s.DBP_SELECTIONCOLS: "id",
                 t1s.DBP_SENDTIME: 128.00,
                 t1s.DBP_RESULTSTIME: 130.00,
                 t1s.DBP_QUERYLATENCY: 5.00,
                 t1s.DBP_ISMODIFICATIONQUERY: False,
                 t1s.DBP_ISTHROUGHPUTQUERY: False}
        self.database.add_rows(t1s.DBF_TABLENAME, [frow1, frow2])
        self.database.add_rows(t1s.DBP_TABLENAME, [prow1, prow2])
        all_fqids = self.database.get_unique_values(
            fields=[(t1s.DBP_TABLENAME, t1s.DBP_FQID)])
        self.assertTrue(fqid1 in all_fqids)
        self.assertTrue(fqid2 in all_fqids)

    def test_is_populated(self):
        self.assertTrue(self.database.is_populated(
            t1s.DBP_TABLENAME, t1s.DBP_FQID))
        self.assertFalse(self.database.is_populated(
            t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT))
