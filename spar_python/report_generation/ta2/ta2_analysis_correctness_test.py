# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA2 correctness getter object classes test
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Jul 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.report_generation.ta2.ta2_analysis_correctness as correctness
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.ta2.ta2_database as t2d

class StubResultsDatabase(object):
    """This is a stub database class intended only for use with these unit
    tests."""
    def __init__(self, values):
        """Initializes the stub database with the specified values."""
        self._values = values
    def get_values(self,
                         simple_fields,
                         constraint_list=[],
                         non_standard_constraint_list=[]):
        return self._values

class TestCorrectnessGetters(unittest.TestCase):

    def test_bad_list_length(self):
        constraint_list = None
        evaluationids = [1, 2, 3]
        evaluationoutputs = ["111", "101", "001"]
        evaluationgroundtruths = ["111", "101"]
        statuses = [None, None, None]
        correctnesses = [None, None, None]
        results_db = StubResultsDatabase([evaluationids,
                                          evaluationoutputs,
                                          evaluationgroundtruths,
                                          statuses,
                                          correctnesses])
        self.assertRaises(AssertionError,
                          correctness.CircuitCorrectnessGetter,
                          results_db, constraint_list)

    def test_no_queries_found(self):
        constraint_list = None
        evaluationids = []
        evaluationoutputs = []
        evaluationgroundtruths = []
        statuses = []
        correctnesses = []
        results_db = StubResultsDatabase([evaluationids,
                                          evaluationoutputs,
                                          evaluationgroundtruths,
                                          statuses,
                                          correctnesses])
        cg = correctness.CircuitCorrectnessGetter(results_db, constraint_list)
        expected_count = 0
        expected_num_correct = 0
        expected_num_failed = 0
        expected_evaluation_accuracy = 1.0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())
        self.assertEqual(expected_evaluation_accuracy,
                         cg.get_evaluation_accuracy())

    def test_imperfect_correctness(self):
        constraint_list = None
        evaluationids = [1, 2, 3, 4]
        evaluationoutputs = ["111", "101", "001", "100"]
        evaluationgroundtruths = ["111", "101", "001", "011"]
        statuses = [None, None, None, None]
        correctnesses = [None, None, None, None]
        results_db = StubResultsDatabase([evaluationids,
                                          evaluationoutputs,
                                          evaluationgroundtruths,
                                          statuses,
                                          correctnesses])
        cg = correctness.CircuitCorrectnessGetter(results_db, constraint_list)
        expected_count = 4
        expected_num_correct = 3
        expected_num_failed = 0
        expected_evaluation_accuracy = .75
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertFalse(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())    
        self.assertEqual(expected_evaluation_accuracy,
                         cg.get_evaluation_accuracy())

    def test_perfect_correctness(self):
        constraint_list = None
        evaluationids = [1, 2, 3]
        evaluationoutputs = ["111", "101", "001"]
        evaluationgroundtruths = ["111", "101", "001"]
        statuses = [None, None, None]
        correctnesses = [None, None, None]
        results_db = StubResultsDatabase([evaluationids,
                                          evaluationoutputs,
                                          evaluationgroundtruths,
                                          statuses,
                                          correctnesses])
        cg = correctness.CircuitCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_num_correct = 3
        expected_num_failed = 0
        expected_evaluation_accuracy = 1.0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())    
        self.assertEqual(expected_evaluation_accuracy,
                         cg.get_evaluation_accuracy())
        
    def test_failed(self):
        constraint_list = None
        evaluationids = [1, 2, 3]
        evaluationoutputs = ["111", "101", "001"]
        evaluationgroundtruths = ["111", "101", "001"]
        statuses = ["Failed... sadness", None, None]
        correctnesses = [None, None, None]
        results_db = StubResultsDatabase([evaluationids,
                                          evaluationoutputs,
                                          evaluationgroundtruths,
                                          statuses,
                                          correctnesses])
        cg = correctness.CircuitCorrectnessGetter(results_db, constraint_list)
        expected_count = 2
        expected_num_correct = 2
        expected_num_failed = 1
        expected_evaluation_accuracy = 1.0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())
        self.assertEqual(expected_evaluation_accuracy,
                         cg.get_evaluation_accuracy())
                
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
                           t2s.CIRCUIT_OUTPUTGATETYPE: "LADD"})

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
    # performer:
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
                           t2s.PEREVALUATION_OUTPUTSIZE: 200.0})
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
                           t2s.PEREVALUATION_OUTPUTSIZE: 200.0})
    # baseline:
    this_database.add_row(t2s.PEREVALUATION_TABLENAME,
                          {t2s.PEREVALUATION_TESTNAME: TESTNAME,
                           t2s.PEREVALUATION_TIMESTAMP: 5.0,
                           t2s.PEREVALUATION_PERFORMERNAME: BASELINE_NAME,
                           t2s.PEREVALUATION_IID: 1,
                           t2s.PEREVALUATION_INPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_OUTPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_ENCRYPTIONLATENCY: 0.0,
                           t2s.PEREVALUATION_EVALUATIONLATENCY: 2.0,
                           t2s.PEREVALUATION_DECRYPTIONLATENCY: 0.0,
                           t2s.PEREVALUATION_OUTPUT: "111",
                           t2s.PEREVALUATION_OUTPUTSIZE: 200.0})
    this_database.add_row(t2s.PEREVALUATION_TABLENAME,
                          {t2s.PEREVALUATION_TESTNAME: TESTNAME,
                           t2s.PEREVALUATION_TIMESTAMP: 6.0,
                           t2s.PEREVALUATION_PERFORMERNAME: BASELINE_NAME,
                           t2s.PEREVALUATION_IID: 2,
                           t2s.PEREVALUATION_INPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_OUTPUTTRANSMITLATENCY: .01,
                           t2s.PEREVALUATION_ENCRYPTIONLATENCY: 0.0,
                           t2s.PEREVALUATION_EVALUATIONLATENCY: 2.0,
                           t2s.PEREVALUATION_DECRYPTIONLATENCY: 0.0,
                           t2s.PEREVALUATION_OUTPUT: "111",
                           t2s.PEREVALUATION_OUTPUTSIZE: 200.0})

