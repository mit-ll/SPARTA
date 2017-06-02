# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            MZ
#  Description:        Creates a test database for testing the regression tool.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  29 July 2013   MZ             Original Version
# *****************************************************************

# general imports:
import unittest
import sqlite3

# SPAR imports:
import spar_python.report_generation.ta1.ta1_database as t1d
import spar_python.report_generation.ta1.ta1_schema as t1s

BASELINE_NAME = "baseline"
PERFORMER_NAME = "white knight"
TESTCASEID1 = "TC001"
TESTCASEID2 = "TC002"

class Ta1DatabaseTest(unittest.TestCase):

    def setUp(self):
        self.database = t1d.Ta1ResultsDB(":memory:")
        set_up_static_db(self.database)

    def tearDown(self):
        self.database.close()

    def test_sort(self):
        tuples = [("P11", 3), ("P6", 101), ("P6", 99)]
        list_of_fields = [(t1s.DBF_TABLENAME, t1s.DBF_CAT),
                          (t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS)]
        self.assertEqual([("P6", 99), ("P6", 101), ("P11", 3)],
                         self.database.sort(tuples, list_of_fields))

    def test_build_simple_query_cmd(self):
        fields = [(t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME),
                  (t1s.DBF_TABLENAME, t1s.DBF_WHERECLAUSE)]
        constraint_list = [(t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
                            PERFORMER_NAME)]
        constraint = self.database.build_constraint(constraint_list)
        static_cmd = ("SELECT %s.%s, %s.%s FROM %s "
                      "INNER JOIN %s ON %s.%s=%s.%s "
                      "WHERE %s"% (
                          t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
                          t1s.DBF_TABLENAME, t1s.DBF_WHERECLAUSE,
                          t1s.DBP_TABLENAME,
                          t1s.DBF_TABLENAME,
                          t1s.DBP_TABLENAME, t1s.DBP_FQID,
                          t1s.DBF_TABLENAME, t1s.DBF_FQID,
                          constraint))
        generated_cmd = self.database.build_pquery_query_cmd(
            fields=fields, constraint_list=constraint_list)
        self.assertEqual(generated_cmd, static_cmd)

    def test_build_atomic_query_cmd(self):
        atomic_fields = [t1s.DBA_NUMMATCHINGRECORDS]
        simple_fields = []
        static_cmd = (
            "SELECT full_to_atomic_junction.ROWID, performer_queries.ROWID, "
            "performer_queries.qid, atomic_queries.num_matching_records FROM "
            "performer_queries INNER JOIN full_queries ON "
            "performer_queries.qid=full_queries.qid INNER JOIN atomic_queries "
            "ON full_to_atomic_junction.atomic_row_id=atomic_queries.aqid "
            "INNER JOIN full_to_atomic_junction ON "
            "full_queries.qid=full_to_atomic_junction.full_row_id")
        generated_cmd = self.database.build_pquery_query_cmd(
            fields=simple_fields, atomic_fields=atomic_fields)
        self.assertEqual(generated_cmd, static_cmd)

    def test_build_full_to_full_query_cmd(self):
        full_fields = [t1s.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM]
        simple_fields = []
        static_cmd = (
            "SELECT full_to_full_junction.ROWID, performer_queries.ROWID, "
            "performer_queries.qid, dbf2.p1_and_num_records_matching_first_term "
            "FROM performer_queries INNER JOIN full_queries ON "
            "performer_queries.qid=full_queries.qid INNER JOIN full_queries AS "
            "dbf2 ON full_to_full_junction.base_full_query=dbf2.qid INNER JOIN "
            "full_to_full_junction ON "
            "full_queries.qid=full_to_full_junction.composite_full_query")
        generated_cmd = self.database.build_pquery_query_cmd(
            fields=simple_fields, full_fields=full_fields)
        self.assertEqual(generated_cmd, static_cmd)

    def test_add_two_identical_performer_query_rows(self):
        row = {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
               t1s.DBP_TESTCASEID: TESTCASEID1,
               t1s.DBP_FQID: 100,
               t1s.DBP_SELECTIONCOLS: "id",
               t1s.DBP_SENDTIME: 123.00,
               t1s.DBP_RESULTSTIME: 128.00,
               t1s.DBP_QUERYLATENCY: 5.00,
               t1s.DBP_ISMODIFICATIONQUERY: False,
               t1s.DBP_ISTHROUGHPUTQUERY: False}
        self.database.add_row(t1s.DBP_TABLENAME, row)
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t1s.DBP_TABLENAME, row)

    def test_add_two_identical_atomic_query_rows(self):
        row = {t1s.DBA_AQID: 100,
               t1s.DBA_CAT: "Eq",
               t1s.DBA_NUMRECORDS: 1000,
               t1s.DBA_RECORDSIZE: 100,
               t1s.DBA_WHERECLAUSE: 'fname="Gretta"',
               t1s.DBA_NUMMATCHINGRECORDS: 12,
               t1s.DBA_FIELD: 'fname',
               t1s.DBA_FIELDTYPE: 'string'}
        self.database.add_row(t1s.DBA_TABLENAME, row)
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t1s.DBA_TABLENAME, row)
        
    def test_get_unique_query_values_empty(self):
        expected_unique_values = []
        unique_values = self.database.get_unique_query_values(
            simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
            constraint_list=[(t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
                              "fictional performer")])
        self.assertEqual(unique_values, expected_unique_values)

    def test_get_query_values_empty(self):
        expected_values = [[]]
        values = self.database.get_query_values(
            simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
            constraint_list=[(t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
                              "fictional performer")])
        self.assertEqual(values, expected_values)

    def test_get_unique_simple_query_values_without_constraint_one(self):
        expected_unique_selectioncols_values = set(["*", "id"])
        unique_selectioncols_values = set(
            self.database.get_unique_query_values(
                simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)]))
        self.assertEqual(unique_selectioncols_values,
                         expected_unique_selectioncols_values)

    def test_get_unique_simple_query_values_without_constraint_many(self):
        expected_unique_values = set([(PERFORMER_NAME, "*"),
                                      (PERFORMER_NAME, "id")])
        unique_values = set(
            self.database.get_unique_query_values(
                [(t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME),
                 (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)]))
        self.assertEqual(unique_values, expected_unique_values)

    def test_get_unique_simple_query_values_with_constraint_one(self):
        this_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_TESTCASEID, TESTCASEID1)]
        expected_unique_selectioncols_values = set(["*"])
        unique_selectioncols_values = set(
            self.database.get_unique_query_values(
                [(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
                constraint_list=this_constraint_list))
        self.assertEqual(unique_selectioncols_values,
                         expected_unique_selectioncols_values)

    def test_get_unique_simple_query_values_with_constraint_many(self):
        this_constraint_list = [(t1s.DBP_TABLENAME, t1s.DBP_TESTCASEID, TESTCASEID1)]
        expected_unique_values = set([(PERFORMER_NAME, "*")])
        unique_values = set(
            self.database.get_unique_query_values(
                [(t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME),
                 (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
                constraint_list=this_constraint_list))
        self.assertEqual(unique_values, expected_unique_values)

    def test_get_unique_atomic_query_values_without_constraint(self):
        # atomic unique values will appear in a tuple, because there
        # is always the chance that multiple atomic values are associated with
        # a single performer query id.
        schema = t1s.Ta1ResultsSchema()
        expected_unique_fieldtype_values = set([tuple(["string"]),
                                                tuple(["integer"]),
                                                tuple(["integer", "string"]),
                                                tuple(["string", "integer"])])
        unique_fieldtype_values = set(
            self.database.get_unique_query_values(
                [], atomic_fields_and_functions=[
                    (t1s.DBA_FIELDTYPE,
                     schema.get_complex_function(
                         t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE, is_list=True))]))
        self.assertEqual(unique_fieldtype_values,
                         expected_unique_fieldtype_values)

    def test_get_unique_atomic_query_values_with_simple_constraint(self):
        this_constraint_list = [(t1s.DBF_TABLENAME, t1s.DBF_CAT, "Eq")]
        # atomic unique values will not appear in a tuple this time, because
        # the function passed in specifies that only one value is expected.
        schema = t1s.Ta1ResultsSchema()
        expected_unique_fieldtype_values = set(["string", "integer"])
        unique_fieldtype_values = set(
            self.database.get_unique_query_values(
                [], constraint_list=this_constraint_list,
                atomic_fields_and_functions=[
                    (t1s.DBA_FIELDTYPE,
                     schema.get_complex_function(
                         t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE))]))
        self.assertEqual(unique_fieldtype_values,
                         expected_unique_fieldtype_values)

    def test_get_unique_atomic_query_values_with_atomic_constraint(self):
        schema = t1s.Ta1ResultsSchema()
        this_constraint_list = [
            (t1s.DBF_TABLENAME, t1s.DBF_CAT, "Eq"),
            (t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE, "string")]
        # atomic unique values will not appear in a tuple this time, because
        # the function passed in specifies that only one value is expected.
        expected_unique_fieldtype_values = set(["string"])
        unique_fieldtype_values = set(
            self.database.get_unique_query_values(
                [], constraint_list=this_constraint_list,
                atomic_fields_and_functions=[
                    (t1s.DBA_FIELDTYPE,
                     schema.get_complex_function(
                         t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE))]))
        self.assertEqual(unique_fieldtype_values,
                         expected_unique_fieldtype_values)
        
    def test_get_simple_query_values_without_constraint(self):
        expected_latency_values = [1000.00, 5000.00, 10000.00, 5.0, 5.0]
        expected_performer_values = [
            PERFORMER_NAME, PERFORMER_NAME, PERFORMER_NAME, PERFORMER_NAME,
            PERFORMER_NAME]
        [latency_values, performer_values] = self.database.get_query_values(
            [(t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
             (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME)])
        self.assertEqual(latency_values, expected_latency_values)
        self.assertEqual(performer_values, expected_performer_values)

    def test_get_simple_query_values_with_constraint(self):
        this_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, "id")]
        expected_latency_values = [5000.00, 10000.00, 5.0, 5.0]
        expected_performer_values = [
            PERFORMER_NAME, PERFORMER_NAME, PERFORMER_NAME, PERFORMER_NAME]
        [latency_values, performer_values] = self.database.get_query_values(
            [(t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
             (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME)],
            constraint_list=this_constraint_list)
        self.assertEqual(latency_values, expected_latency_values)
        self.assertEqual(performer_values, expected_performer_values)

    def test_get_simple_query_values_with_nonstandard_constraint(self):
        this_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, "id")]
        this_non_standard_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_FQID, "%s.%s<6")]
        expected_latency_values = [5000.00, 10000.00]
        expected_performer_values = [PERFORMER_NAME, PERFORMER_NAME]
        [latency_values, performer_values] = self.database.get_query_values(
            [(t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
             (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME)],
            constraint_list=this_constraint_list,
            non_standard_constraint_list=this_non_standard_constraint_list)
        self.assertEqual(latency_values, expected_latency_values)
        self.assertEqual(performer_values, expected_performer_values)

    def test_get_simple_query_values_with_atomic_constraint(self):
        this_constraint_list = [
            (t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE, "string"),
            (t1s.DBF_TABLENAME, t1s.DBF_CAT, "Eq")]
        expected_latency_values = [5.0]
        expected_performer_values = [PERFORMER_NAME]
        [latency_values, performer_values] = self.database.get_query_values(
            [(t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
             (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME)],
            constraint_list=this_constraint_list)
        self.assertEqual(latency_values, expected_latency_values)
        self.assertEqual(performer_values, expected_performer_values)

    def test_get_atomic_query_values_without_constraint(self):
        # Note that though there are 5 performer queries, only 4 of them
        # return values here, because one of them does not have associated
        # atomic queries (it is a dnf, which only have associated sub-full
        # queries).
        fields = [(t1s.DBF_TABLENAME, t1s.DBF_CAT),
                  (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT),
                  (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
                  (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)]
        def first(values): return values[0]
        these_atomic_fields_and_functions = [
            (t1s.DBA_NUMMATCHINGRECORDS, first),
            (t1s.DBA_NUMMATCHINGRECORDS, max)]
        expected_cat_values = ["P1", "P1", "Eq", "Eq"]
        expected_subcat_values = ["eq-or", "eq-or", "", ""]
        expected_querylatency_values = [1000.0, 5000.0, 5.0, 5.0]
        expected_selectioncols_values = ["*", "id", "id", "id"]
        expected_atomic_values_first = [63, 5, 63, 5]
        expected_atomic_values_max = [63, 12, 63, 5]
        [cat_values,
         subcat_values,
         querylatency_values,
         selectioncols_values,
         atomic_values_first,
         atomic_values_max] = self.database.get_query_values(fields,
            atomic_fields_and_functions=these_atomic_fields_and_functions)
        self.assertEqual(cat_values, expected_cat_values)
        self.assertEqual(subcat_values, expected_subcat_values)
        self.assertEqual(querylatency_values, expected_querylatency_values)
        self.assertEqual(selectioncols_values, expected_selectioncols_values)
        self.assertEqual(atomic_values_first, expected_atomic_values_first)
        self.assertEqual(atomic_values_max, expected_atomic_values_max)

    def test_get_atomic_query_values_with_constraint(self):
        this_constraint_list = [(t1s.DBF_TABLENAME, t1s.DBF_CAT, "P1")]
        fields = [(t1s.DBF_TABLENAME, t1s.DBF_CAT),
                  (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT),
                  (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
                  (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)]
        def first(values): return values[0]
        these_atomic_fields_and_functions = [
            (t1s.DBA_NUMMATCHINGRECORDS, first),
            (t1s.DBA_NUMMATCHINGRECORDS, max)]
        expected_cat_values = ["P1", "P1"]
        expected_subcat_values = ["eq-or", "eq-or"]
        expected_querylatency_values = [1000.0, 5000.0]
        expected_selectioncols_values = ["*", "id"]
        expected_atomic_values_first = [63, 5]
        expected_atomic_values_max = [63, 12]
        [cat_values, subcat_values, querylatency_values, selectioncols_values,
         atomic_values_first,
         atomic_values_max] = self.database.get_query_values(fields,
            atomic_fields_and_functions=these_atomic_fields_and_functions,
            constraint_list = this_constraint_list)
        self.assertEqual(cat_values, expected_cat_values)
        self.assertEqual(subcat_values, expected_subcat_values)
        self.assertEqual(querylatency_values, expected_querylatency_values)
        self.assertEqual(selectioncols_values, expected_selectioncols_values)
        self.assertEqual(atomic_values_first, expected_atomic_values_first)
        self.assertEqual(atomic_values_max, expected_atomic_values_max)

    def test_get_full_query_values_without_constraint(self):
        fields = [(t1s.DBF_TABLENAME, t1s.DBF_CAT),
                  (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT),
                  (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
                  (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)]
        these_full_fields_and_functions = [
            (t1s.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM, sum)]
        expected_cat_values = ["P1"]
        expected_subcat_values = ["eq-dnf"]
        expected_querylatency_values = [10000.0]
        expected_selectioncols_values = ["id"]
        expected_full_values_sum = [68]
        [cat_values,
         subcat_values,
         querylatency_values,
         selectioncols_values,
         full_values_sum] = self.database.get_query_values(fields,
            full_fields_and_functions=these_full_fields_and_functions)
        self.assertEqual(cat_values, expected_cat_values)
        self.assertEqual(subcat_values, expected_subcat_values)
        self.assertEqual(querylatency_values, expected_querylatency_values)
        self.assertEqual(selectioncols_values, expected_selectioncols_values)
        self.assertEqual(full_values_sum, expected_full_values_sum)

def set_up_static_db(this_database):
    """
    Clears the database, and enters some hard-coded query values into it.
    """
    this_database.clear()
    # add atomic queries:
    this_database.add_row(t1s.DBA_TABLENAME,
                          {t1s.DBA_AQID: 1,
                           t1s.DBA_CAT: "Eq",
                           t1s.DBA_NUMRECORDS: 1000,
                           t1s.DBA_RECORDSIZE: 100,
                           t1s.DBA_WHERECLAUSE: "fname='Alice'",
                           t1s.DBA_NUMMATCHINGRECORDS: 12,
                           t1s.DBA_FIELD: 'fname',
                           t1s.DBA_FIELDTYPE: 'string'})
    this_database.add_row(t1s.DBA_TABLENAME,
                          {t1s.DBA_AQID: 2,
                           t1s.DBA_CAT: "Eq",
                           t1s.DBA_NUMRECORDS: 1000,
                           t1s.DBA_RECORDSIZE: 100,
                           t1s.DBA_WHERECLAUSE: "lname='Smith'",
                           t1s.DBA_NUMMATCHINGRECORDS: 63,
                           t1s.DBA_FIELD: 'lname',
                           t1s.DBA_FIELDTYPE: 'string'})
    this_database.add_row(t1s.DBA_TABLENAME,
                          {t1s.DBA_AQID: 5,
                           t1s.DBA_CAT: "Eq",
                           t1s.DBA_NUMRECORDS: 1000,
                           t1s.DBA_RECORDSIZE: 100,
                           t1s.DBA_WHERECLAUSE: 'age=32',
                           t1s.DBA_NUMMATCHINGRECORDS: 5,
                           t1s.DBA_FIELD: 'age',
                           t1s.DBA_FIELDTYPE: 'integer'})
    # add full queries:
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 6,
                           t1s.DBF_CAT: "Eq",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE: "lname='Smith'"})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 6,
                           t1s.F2A_AQID: 2})
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 7,
                           t1s.DBF_CAT: "Eq",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE: 'age=32'})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 7,
                           t1s.F2A_AQID: 5})
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 1,
                           t1s.DBF_CAT: "P1",
                           t1s.DBF_SUBCAT: "eq-or",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE:
                           "lname='Smith' OR age=32"})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 1,
                           t1s.F2A_AQID: 2})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 1,
                           t1s.F2A_AQID: 5})
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 2,
                           t1s.DBF_CAT: "P1",
                           t1s.DBF_SUBCAT: "eq-or",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE:
                           "age=32 OR fname='Alice'"})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 2,
                           t1s.F2A_AQID: 5})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 2,
                           t1s.F2A_AQID: 1})
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 3,
                           t1s.DBF_CAT: "P1",
                           t1s.DBF_SUBCAT: "eq-and",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE:
                           "lname='Smith' AND age=32",
                           t1s.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM: 63})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 3,
                           t1s.F2A_AQID: 2})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 3,
                           t1s.F2A_AQID: 5})
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 4,
                           t1s.DBF_CAT: "P1",
                           t1s.DBF_SUBCAT: "eq-and",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE:
                           "age=32 AND fname='Alice'",
                           t1s.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM: 5})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 4,
                           t1s.F2A_AQID: 5})
    this_database.add_row(t1s.F2A_TABLENAME,
                          {t1s.F2A_FQID: 4,
                           t1s.F2A_AQID: 1})
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 5,
                           t1s.DBF_CAT: "P1",
                           t1s.DBF_SUBCAT: "eq-dnf",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE:
            "(age=32 AND fname='Alice') OR (lname='Smith' AND age=32)"})
    this_database.add_row(t1s.F2F_TABLENAME,
                          {t1s.F2F_COMPOSITEQID: 5,
                           t1s.F2F_BASEQID: 3})
    this_database.add_row(t1s.F2F_TABLENAME,
                          {t1s.F2F_COMPOSITEQID: 5,
                           t1s.F2F_BASEQID: 4})
    # add performer queries:
    this_database.add_row(t1s.DBP_TABLENAME,
                          {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                           t1s.DBP_TESTCASEID: TESTCASEID1,
                           t1s.DBP_FQID: 1,
                           t1s.DBP_SELECTIONCOLS: "*",
                           t1s.DBP_QUERYLATENCY: 1000.00,
                           t1s.DBP_ISMODIFICATIONQUERY: False,
                           t1s.DBP_ISTHROUGHPUTQUERY: False})
    this_database.add_row(t1s.DBP_TABLENAME,
                          {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                           t1s.DBP_TESTCASEID: TESTCASEID2,
                           t1s.DBP_FQID: 2,
                           t1s.DBP_SELECTIONCOLS: "id",
                           t1s.DBP_QUERYLATENCY: 5000.00,
                           t1s.DBP_ISMODIFICATIONQUERY: False,
                           t1s.DBP_ISTHROUGHPUTQUERY: False})
    this_database.add_row(t1s.DBP_TABLENAME,
                          {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                           t1s.DBP_TESTCASEID: TESTCASEID2,
                           t1s.DBP_FQID: 5,
                           t1s.DBP_SELECTIONCOLS: "id",
                           t1s.DBP_QUERYLATENCY: 10000.00,
                           t1s.DBP_ISMODIFICATIONQUERY: False,
                           t1s.DBP_ISTHROUGHPUTQUERY: False})
    this_database.add_row(t1s.DBP_TABLENAME,
                          {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                           t1s.DBP_TESTCASEID: TESTCASEID2,
                           t1s.DBP_FQID: 6,
                           t1s.DBP_SELECTIONCOLS: "id",
                           t1s.DBP_QUERYLATENCY: 5.00,
                           t1s.DBP_ISMODIFICATIONQUERY: False,
                           t1s.DBP_ISTHROUGHPUTQUERY: False})
    this_database.add_row(t1s.DBP_TABLENAME,
                          {t1s.DBP_PERFORMERNAME: PERFORMER_NAME,
                           t1s.DBP_TESTCASEID: TESTCASEID2,
                           t1s.DBP_FQID: 7,
                           t1s.DBP_SELECTIONCOLS: "id",
                           t1s.DBP_QUERYLATENCY: 5.00,
                           t1s.DBP_ISMODIFICATIONQUERY: False,
                           t1s.DBP_ISTHROUGHPUTQUERY: False})
    # populate one correctness value:
    this_database.update(t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT, "TRUE",
                         constraint_list=[(t1s.DBP_TABLENAME, "ROWID", 5)])
