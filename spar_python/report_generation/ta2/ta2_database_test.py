# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests the TA2 results database.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  16 Oct 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest
import sqlite3

# SPAR imports:
import spar_python.report_generation.ta2.ta2_database as t2d
import spar_python.report_generation.ta2.ta2_schema as t2s

BASELINE_NAME = "baseline"
PERFORMER_NAME = "white knight"
TESTNAME = "testcase001"

class Ta2DatabaseTest(unittest.TestCase):

    def setUp(self):
        self.database = t2d.Ta2ResultsDB(":memory:")
        set_up_static_db(self.database)

    def tearDown(self):
        self.database.close()

    def test_get_next_parms_id(self):
        static_next_id = 2
        generated_next_id = self.database.get_next_params_id() 
        self.assertEqual(generated_next_id, static_next_id)

    def test_get_next_circuit_id(self):
        static_next_id = 2
        generated_next_id = self.database.get_next_circuit_id() 
        self.assertEqual(generated_next_id, static_next_id)

    def test_get_next_parms_id(self):
        static_next_id = 3
        generated_next_id = self.database.get_next_input_id() 
        self.assertEqual(generated_next_id, static_next_id)

    def test_build_keygen_query_cmd(self):
        fields = [(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY),
                  (t2s.PARAM_TABLENAME, t2s.PARAM_K)]
        static_cmd = ("SELECT %s.%s, %s.%s FROM %s "
                      "INNER JOIN %s ON %s.%s=%s.%s" % (
                          t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY,
                          t2s.PARAM_TABLENAME, t2s.PARAM_K,
                          t2s.PERKEYGEN_TABLENAME,
                          t2s.PARAM_TABLENAME, t2s.PERKEYGEN_TABLENAME,
                          t2s.PERKEYGEN_PID, t2s.PARAM_TABLENAME,
                          t2s.PARAM_PID))
        generated_cmd = self.database.build_query_cmd(fields)
        self.assertEqual(generated_cmd, static_cmd)

    def test_add_two_identical_param_rows(self):
        row = {t2s.PARAM_TESTNAME: TESTNAME,
               t2s.PARAM_PID: 1,
               t2s.PARAM_K: 80,
               t2s.PARAM_D: 10,
               t2s.PARAM_L: 20}
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t2s.PARAM_TABLENAME, row)

    def test_add_two_identical_circuit_rows(self):
        row = {t2s.CIRCUIT_TESTNAME: TESTNAME,
               t2s.CIRCUIT_CID: 1,
               t2s.CIRCUIT_W: 30,
               t2s.CIRCUIT_PID: 1,
               t2s.CIRCUIT_NUMADDS: 3,
               t2s.CIRCUIT_NUMADDCONSTS: 4,
               t2s.CIRCUIT_NUMMULS: 5,
               t2s.CIRCUIT_NUMMULCONSTS: 6,
               t2s.CIRCUIT_NUMROTATES: 7,
               t2s.CIRCUIT_NUMSELECTS: 8,
               t2s.CIRCUIT_NUMLEVELS: 9,
               t2s.CIRCUIT_NUMGATES: 42,
               t2s.CIRCUIT_OUTPUTGATETYPE: "LADD",
               t2s.CIRCUIT_TESTTYPE: "RANDOM"}
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t2s.CIRCUIT_TABLENAME, row)

    def test_add_two_identical_input_rows(self):
        row = {t2s.INPUT_TESTNAME: TESTNAME,
               t2s.INPUT_IID: 1,
               t2s.INPUT_CID: 1,
               t2s.INPUT_NUMZEROS: 299,
               t2s.INPUT_NUMONES: 301}
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t2s.INPUT_TABLENAME, row)

    def test_add_two_identical_perkeygen_rows(self):
        row = {t2s.PERKEYGEN_TESTNAME: TESTNAME,
               t2s.PERKEYGEN_TIMESTAMP: 1.0,
               t2s.PERKEYGEN_PERFORMERNAME: PERFORMER_NAME,
               t2s.PERKEYGEN_PID: 1,
               t2s.PERKEYGEN_TRANSMITLATENCY: .01,
               t2s.PERKEYGEN_LATENCY: 10.0,
               t2s.PERKEYGEN_KEYSIZE: 55.0}
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t2s.PERKEYGEN_TABLENAME, row)

    def test_add_two_identical_peringestion_rows(self):
        row = {t2s.PERINGESTION_TESTNAME: TESTNAME,
               t2s.PERINGESTION_TIMESTAMP: 2.0,
               t2s.PERINGESTION_PERFORMERNAME: PERFORMER_NAME,
               t2s.PERINGESTION_CID: 1,
               t2s.PERINGESTION_TRANSMITLATENCY: .01,
               t2s.PERINGESTION_LATENCY: 12.0}
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t2s.PERINGESTION_TABLENAME,
                          row)

    def test_add_two_identical_perevaluation_rows(self):
        row = {t2s.PEREVALUATION_TESTNAME: TESTNAME,
               t2s.PEREVALUATION_TIMESTAMP: 3.0,
               t2s.PEREVALUATION_PERFORMERNAME: PERFORMER_NAME,
               t2s.PEREVALUATION_IID: 1,
               t2s.PEREVALUATION_INPUTTRANSMITLATENCY: .01,
               t2s.PEREVALUATION_OUTPUTTRANSMITLATENCY: .01,
               t2s.PEREVALUATION_ENCRYPTIONLATENCY: 14.0,
               t2s.PEREVALUATION_EVALUATIONLATENCY: 16.0,
               t2s.PEREVALUATION_DECRYPTIONLATENCY: 18.0,
               t2s.PEREVALUATION_OUTPUT: "111",
               t2s.PEREVALUATION_OUTPUTSIZE: 200.0,
               t2s.PEREVALUATION_INPUTSIZE: 400.0}
        self.assertRaises(sqlite3.IntegrityError,
                          self.database.add_row, t2s.PEREVALUATION_TABLENAME,
                          row)

    def test_get_unique_values_empty(self):
        expected_unique_values = []
        unique_values = self.database.get_unique_values(
            fields=[(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY)],
            constraint_list=[(t2s.PERKEYGEN_TABLENAME,
                              t2s.PERKEYGEN_PERFORMERNAME,
                              "fictional performer")])
        self.assertEqual(unique_values, expected_unique_values)

    def test_get_values_empty(self):
        expected_values = [[]]
        values = self.database.get_values(
            fields=[(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY)],
            constraint_list=[(t2s.PERKEYGEN_TABLENAME,
                              t2s.PERKEYGEN_PERFORMERNAME,
                              "fictional performer")])
        self.assertEqual(values, expected_values)

    def test_get_unique_values_without_constraint_one(self):
        expected_unique_evaluation_outputs = set(["000", "111"])
        unique_evaluation_outputs = set(
            self.database.get_unique_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT)]))
        self.assertEqual(unique_evaluation_outputs,
                         expected_unique_evaluation_outputs)

    def test_get_unique_values_without_constraint_many(self):
        expected_unique_values = set([("111", 299), ("000", 298), ("111", 298)])
        unique_values = set(
            self.database.get_unique_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT),
                        (t2s.INPUT_TABLENAME, t2s.INPUT_NUMZEROS)]))
        self.assertEqual(unique_values, expected_unique_values)

    def test_get_unique_values_with_constraint_one(self):
        expected_unique_evaluation_outputs = set(["111"])
        unique_evaluation_outputs = set(
            self.database.get_unique_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT)],
                constraint_list=[(t2s.INPUT_TABLENAME, t2s.INPUT_IID, 1)]))
        self.assertEqual(unique_evaluation_outputs,
                         expected_unique_evaluation_outputs)

    def test_get_unique_values_with_constraint_many(self):
        expected_unique_values = set([("111", 299)])
        unique_values = set(
            self.database.get_unique_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT),
                        (t2s.INPUT_TABLENAME, t2s.INPUT_NUMZEROS)],
                constraint_list=[(t2s.INPUT_TABLENAME, t2s.INPUT_IID, 1)]))
        self.assertEqual(unique_values, expected_unique_values)

    def test_get_values_without_constraint_one(self):
        expected_evaluation_outputs = [["111", "000", "111"]]
        evaluation_outputs = self.database.get_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT)])
        self.assertEqual(evaluation_outputs, expected_evaluation_outputs)

    def test_get_values_without_constraint_many(self):
        expected_values = [["111", "000", "111"], [299, 298, 298]]
        values = self.database.get_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT),
                        (t2s.INPUT_TABLENAME, t2s.INPUT_NUMZEROS)])
        self.assertEqual(values, expected_values)

    def test_get_values_with_constraint_one(self):
        expected_evaluation_outputs = [["111"]]
        evaluation_outputs = self.database.get_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT)],
                constraint_list=[(t2s.INPUT_TABLENAME, t2s.INPUT_IID, 1)])
        self.assertEqual(evaluation_outputs, expected_evaluation_outputs)

    def test_get_values_with_constraint_many(self):
        expected_values = [["111"], [299]]
        values = self.database.get_values(
                fields=[(t2s.PEREVALUATION_TABLENAME,
                         t2s.PEREVALUATION_OUTPUT),
                        (t2s.INPUT_TABLENAME, t2s.INPUT_NUMZEROS)],
                constraint_list=[(t2s.INPUT_TABLENAME, t2s.INPUT_IID, 1)])
        self.assertEqual(values, expected_values)

    def test_get_values_without_primary_table(self):
        expected_values = [[299, 298]]
        values = self.database.get_values(
            fields=[(t2s.INPUT_TABLENAME, t2s.INPUT_NUMZEROS)])
        self.assertEqual(values, expected_values)

def set_up_static_db(this_database):
    """
    Clears the database, and enters some hard-coded values into it.
    """
    this_database.clear()
    # add parameters:
    this_database.add_row(t2s.PARAM_TABLENAME,
                          {t2s.PARAM_TESTNAME: TESTNAME,
                           t2s.PARAM_PID: 1,
                           t2s.PARAM_K: 80,
                           t2s.PARAM_D: 10,
                           t2s.PARAM_L: 20})
    # add circuits:
    this_database.add_row(t2s.CIRCUIT_TABLENAME,
                          {t2s.CIRCUIT_TESTNAME: TESTNAME,
                           t2s.CIRCUIT_CID: 1,
                           t2s.CIRCUIT_W: 30,
                           t2s.CIRCUIT_PID: 1,
                           t2s.CIRCUIT_NUMADDS: 3,
                           t2s.CIRCUIT_NUMADDCONSTS: 4,
                           t2s.CIRCUIT_NUMMULS: 5,
                           t2s.CIRCUIT_NUMMULCONSTS: 6,
                           t2s.CIRCUIT_NUMROTATES: 7,
                           t2s.CIRCUIT_NUMSELECTS: 8,
                           t2s.CIRCUIT_NUMLEVELS: 9,
                           t2s.CIRCUIT_NUMGATES: 42,
                           t2s.CIRCUIT_OUTPUTGATETYPE: "LADD",
                           t2s.CIRCUIT_TESTTYPE: "RANDOM"})

    # add inputs:
    this_database.add_row(t2s.INPUT_TABLENAME,
                          {t2s.INPUT_TESTNAME: TESTNAME,
                           t2s.INPUT_IID: 1,
                           t2s.INPUT_CID: 1,
                           t2s.INPUT_NUMZEROS: 299,
                           t2s.INPUT_NUMONES: 301})
    this_database.add_row(t2s.INPUT_TABLENAME,
                          {t2s.INPUT_TESTNAME: TESTNAME,
                           t2s.INPUT_IID: 2,
                           t2s.INPUT_CID: 1,
                           t2s.INPUT_NUMZEROS: 298,
                           t2s.INPUT_NUMONES: 302})

    # add performer key generation results:
    this_database.add_row(t2s.PERKEYGEN_TABLENAME,
                          {t2s.PERKEYGEN_TESTNAME: TESTNAME,
                           t2s.PERKEYGEN_TIMESTAMP: 1.0,
                           t2s.PERKEYGEN_PERFORMERNAME: PERFORMER_NAME,
                           t2s.PERKEYGEN_PID: 1,
                           t2s.PERKEYGEN_TRANSMITLATENCY: .01,
                           t2s.PERKEYGEN_LATENCY: 10.0,
                           t2s.PERKEYGEN_KEYSIZE: 55.0})

    # add performer circuit ingestion results:
    this_database.add_row(t2s.PERINGESTION_TABLENAME,
                          {t2s.PERINGESTION_TESTNAME: TESTNAME,
                           t2s.PERINGESTION_TIMESTAMP: 2.0,
                           t2s.PERINGESTION_PERFORMERNAME: PERFORMER_NAME,
                           t2s.PERINGESTION_CID: 1,
                           t2s.PERINGESTION_TRANSMITLATENCY: .01,
                           t2s.PERINGESTION_LATENCY: 12.0})

    # add performer evaluation results:
    this_database.add_row(t2s.PEREVALUATION_TABLENAME,
                          {t2s.PEREVALUATION_TESTNAME: TESTNAME,
                           t2s.PEREVALUATION_TIMESTAMP: 3.0,
                           t2s.PEREVALUATION_PERFORMERNAME: PERFORMER_NAME,
                           t2s.PEREVALUATION_IID: 1,
                           t2s.PEREVALUATION_INPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_OUTPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_ENCRYPTIONLATENCY: 14.0,
                           t2s.PEREVALUATION_EVALUATIONLATENCY: 16.0,
                           t2s.PEREVALUATION_DECRYPTIONLATENCY: 18.0,
                           t2s.PEREVALUATION_OUTPUT: "111",
                           t2s.PEREVALUATION_OUTPUTSIZE: 200.0,
                           t2s.PEREVALUATION_INPUTSIZE: 400.0})
    this_database.add_row(t2s.PEREVALUATION_TABLENAME,
                          {t2s.PEREVALUATION_TESTNAME: TESTNAME,
                           t2s.PEREVALUATION_TIMESTAMP: 4.0,
                           t2s.PEREVALUATION_PERFORMERNAME: PERFORMER_NAME,
                           t2s.PEREVALUATION_IID: 2,
                           t2s.PEREVALUATION_INPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_OUTPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_ENCRYPTIONLATENCY: 20.0,
                           t2s.PEREVALUATION_EVALUATIONLATENCY: 22.0,
                           t2s.PEREVALUATION_DECRYPTIONLATENCY: 24.0,
                           t2s.PEREVALUATION_OUTPUT: "000",
                           t2s.PEREVALUATION_OUTPUTSIZE: 200.0,
                           t2s.PEREVALUATION_INPUTSIZE: 400.0})
    this_database.add_row(t2s.PEREVALUATION_TABLENAME,
                          {t2s.PEREVALUATION_TESTNAME: TESTNAME,
                           t2s.PEREVALUATION_TIMESTAMP: 5.0,
                           t2s.PEREVALUATION_PERFORMERNAME: PERFORMER_NAME,
                           t2s.PEREVALUATION_IID: 2,
                           t2s.PEREVALUATION_INPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_OUTPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_ENCRYPTIONLATENCY: 26.0,
                           t2s.PEREVALUATION_EVALUATIONLATENCY: 28.0,
                           t2s.PEREVALUATION_DECRYPTIONLATENCY: 30.0,
                           t2s.PEREVALUATION_OUTPUT: "111",
                           t2s.PEREVALUATION_OUTPUTSIZE: 200.0,
                           t2s.PEREVALUATION_INPUTSIZE: 400.0})

