# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        correctness getter object classes test
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Jul 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest

# spar imports:
import spar_python.report_generation.ta1.ta1_analysis_correctness as correctness
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_database as t1d

class StubResultsDatabase(object):
    """This is a stub database class intended only for use with these unit
    tests."""
    def __init__(self, values):
        """Initializes the stub database with the specified values."""
        self._values = values
    def get_query_values(self,
                         simple_fields,
                         atomic_fields_and_functions=[],
                         full_fields_and_functions=[],
                         constraint_list=[],
                         non_standard_constraint_list=[]):
        return self._values

class TestCorrectnessGetters(unittest.TestCase):

    def test_query_bad_list_length(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"]]
        returned_record_ids = matching_record_ids
        returned_record_hashes = matching_record_hashes
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        self.assertRaises(AssertionError, correctness.QueryCorrectnessGetter,
                          results_db, constraint_list)

    def test_no_queries_found(self):
        constraint_list = None
        performer_query_ids = []
        full_query_ids = []
        query_cats = []
        is_corrects = []
        selection_cols = []
        matching_record_ids = []
        matching_record_hashes = []
        returned_record_ids = matching_record_ids
        returned_record_hashes = matching_record_hashes
        p9_matching_record_counts = []
        policies = []
        statuses = []
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 0
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 0
        expected_num_correct = 0
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_query_perfect_correctness(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "id"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = matching_record_ids
        returned_record_hashes = matching_record_hashes[:-1] + [[]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 0
        expected_num_correct = 3
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_query_failed(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = matching_record_ids[:-1] + [[]]
        returned_record_hashes = matching_record_hashes[:-1] + [[]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, "failed cuz life sucks"]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 2
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 0
        expected_num_correct = 2
        expected_num_failed = 1
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_query_perfect_query_correctness_out_of_order(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = [["3", "1", "2"], ["4"], ["5"]]
        returned_record_hashes = [["hash3", "hash1", "hash2"], ["hash4"],
                                  ["hash5"]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 0
        expected_num_correct = 3
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_p9_good_ordering(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["P9", "P9", "P9"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = [["1", "3", "2"], ["4"], ["5"]]
        returned_record_hashes = [["hash1", "hash3", "hash2"], ["hash4"],
                                  ["hash5"]]
        p9_matching_record_counts = [[1, 2], [1], [1]]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 0
        expected_num_correct = 3
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_p9_bad_ordering(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["P9", "P9", "P9"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4", "6"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"],
                                  ["hash4", "hash6"], ["hash5"]]
        returned_record_ids = [["3", "1", "2"], ["6", "4"], ["5"]]
        returned_record_hashes = [["hash3", "hash1", "hash2"],
                                  ["hash6", "hash4"], ["hash5"]]
        p9_matching_record_counts = [[1, 2], [1, 1], [1]]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 2
        expected_num_correct = 1
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertFalse(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())
        
    def test_query_imperfect_precision(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = [["1", "2", "3"], ["4", "6"], ["5"]]
        returned_record_hashes = [["hash1", "hash2", "hash3"],
                                  ["hash4", "hash6"], ["hash5"]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = round(5.0 / 6.0, 3)
        expected_recall = 1.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 0
        expected_num_correct = 2
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertFalse(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())
        
    def test_query_imperfect_recall(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = [["1", "3"], ["4"], ["5"]]
        returned_record_hashes = [["hash1", "hash3"], ["hash4"], ["hash5"]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 4.0 / 5.0
        expected_badhash_fraction = 0.0
        expected_num_bad_rankings = 0
        expected_num_correct = 2
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertFalse(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_query_bad_hashes(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        returned_record_hashes = [["hash1", "hash2", "badhash3"],
                                  ["hash4"], ["hash5"]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.2
        expected_num_bad_rankings = 0
        expected_num_correct = 2
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertFalse(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_query_select_id(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["id", "id", "id"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        returned_record_hashes = [["hash1", "hash2", "badhash3"],
                                  ["hash4"], ["hash5"]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0
        expected_num_bad_rankings = 0
        expected_num_correct = 3
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_query_bad_hashes_out_of_order(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "EQ"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        returned_record_ids = [["3", "2", "1"], ["4"], ["5"]]
        returned_record_hashes = [["badhash3", "hash2", "hash1"],
                                  ["hash4"], ["hash5"]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        results_db = StubResultsDatabase([performer_query_ids,
                                          full_query_ids,
                                          query_cats,
                                          is_corrects,
                                          selection_cols,
                                          matching_record_ids,
                                          matching_record_hashes,
                                          returned_record_ids,
                                          returned_record_hashes,
                                          p9_matching_record_counts,
                                          policies,
                                          statuses])
        cg = correctness.QueryCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.2
        expected_num_bad_rankings = 0
        expected_num_correct = 2
        expected_num_failed = 0
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertEqual(expected_badhash_fraction, cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings, cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, cg.get_num_failed())
        self.assertFalse(cg.is_perfect())

    def test_query_addition(self):
        constraint_list = None
        performer_query_ids = [1, 2, 3]
        full_query_ids = [23, 24, 25]
        query_cats = ["EQ", "EQ", "P2"]
        is_corrects = ["TRUE", "", ""]
        selection_cols = ["*", "*", "*"]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        matching_record_hashes = [["hash1", "hash2", "hash3"], ["hash4"],
                                  ["hash5"]]
        a_returned_record_ids = [["3", "2", "1"], ["4"], ["5"]]
        a_returned_record_hashes = [["badhash3", "hash2", "hash1"],
                                    ["hash4"], ["hash5"]]
        b_returned_record_ids = [["3", "2", "1"], ["4"], ["5"]]
        b_returned_record_hashes = [["hash3", "hash2", "hash1"],
                                    ["hash4"], ["hash5"]]
        p9_matching_record_counts = [None, None, None]
        policies = [[], [], []]
        statuses = [None, None, None]
        a_results_db = StubResultsDatabase([performer_query_ids,
                                            full_query_ids,
                                            query_cats,
                                            is_corrects,
                                            selection_cols,
                                            matching_record_ids,
                                            matching_record_hashes,
                                            a_returned_record_ids,
                                            a_returned_record_hashes,
                                            p9_matching_record_counts,
                                            policies,
                                            statuses])
        b_results_db = StubResultsDatabase([performer_query_ids,
                                            full_query_ids,
                                            query_cats,
                                            is_corrects,
                                            selection_cols,
                                            matching_record_ids,
                                            matching_record_hashes,
                                            b_returned_record_ids,
                                            b_returned_record_hashes,
                                            p9_matching_record_counts,
                                            policies,
                                            statuses])
        a_cg = correctness.QueryCorrectnessGetter(a_results_db, constraint_list)
        b_cg = correctness.QueryCorrectnessGetter(b_results_db, constraint_list)
        sum_cg = a_cg + b_cg
        expected_count = 6
        expected_precision = 1.0
        expected_recall = 1.0
        expected_badhash_fraction = 0.1
        expected_num_bad_rankings = 0
        expected_num_correct = 5
        expected_num_failed = 0
        self.assertEqual(expected_count, sum_cg.get_count())
        self.assertEqual(expected_precision, sum_cg.get_precision())
        self.assertEqual(expected_recall, sum_cg.get_recall())
        self.assertEqual(expected_badhash_fraction,
                         sum_cg.get_badhash_fraction())
        self.assertEqual(expected_num_bad_rankings,
                         sum_cg.get_num_bad_rankings())
        self.assertEqual(expected_num_failed, sum_cg.get_num_failed())
        self.assertFalse(sum_cg.is_perfect())

    def test_integration_with_db(self):
        results_db = t1d.Ta1ResultsDB(":memory:")
        set_up_static_db(results_db)
        self.assertEqual(results_db.get_query_values(
            [(t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT)])[0], ["", ""])
        cg = correctness.QueryCorrectnessGetter(results_db, update_db=True)
        self.assertEqual(results_db.get_query_values(
            [(t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT)])[0], [True, False])
        results_db.close()

    def test_policy_perfect_correctness(self):
        constraint_list = None
        rejecting_policies = [["policy1"], [], ["policy1", "policy2"]]
        current_policies = [["policy1"], ["policy1"], ["policy1"]]
        returned_record_ids = [[], ["4"], []]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        results_db = StubResultsDatabase([rejecting_policies,
                                          current_policies,
                                          matching_record_ids,
                                          returned_record_ids])
        cg = correctness.PolicyCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0
        expected_num_correct = 3
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertTrue(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_policy_imperfect_precision(self):
        constraint_list = None
        rejecting_policies = [["policy1"], [], ["policy1", "policy2"]]
        current_policies = [["policy1"], ["policy1"], ["policy1"]]
        returned_record_ids = [[], [], []]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        results_db = StubResultsDatabase([rejecting_policies,
                                          current_policies,
                                          matching_record_ids,
                                          returned_record_ids])
        cg = correctness.PolicyCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = round(2.0 / 3.0, 3)
        expected_recall = 1.0
        expected_num_correct = 2
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertFalse(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())

    def test_policy_imperfect_recall(self):
        constraint_list = None
        rejecting_policies = [["policy1"], [], ["policy1", "policy2"]]
        current_policies = [["policy1"], ["policy1"], ["policy1"]]
        returned_record_ids = [[], ["4"], ["5"]]
        matching_record_ids = [["1", "2", "3"], ["4"], ["5"]]
        results_db = StubResultsDatabase([rejecting_policies,
                                          current_policies,
                                          matching_record_ids,
                                          returned_record_ids])
        cg = correctness.PolicyCorrectnessGetter(results_db, constraint_list)
        expected_count = 3
        expected_precision = 1.0
        expected_recall = 1.0 / 2.0
        expected_num_correct = 2
        self.assertEqual(expected_count, cg.get_count())
        self.assertEqual(expected_precision, cg.get_precision())
        self.assertEqual(expected_recall, cg.get_recall())
        self.assertFalse(cg.is_perfect())
        self.assertEqual(expected_num_correct, cg.get_num_correct())
        
def set_up_static_db(this_database):
    """
    Clears the database, and enters some hard-coded query values into it.
    """
    this_database.clear()
    # add queries:
    this_database.add_row(t1s.DBF_TABLENAME,
                          {t1s.DBF_FQID: 1,
                           t1s.DBF_CAT: "Eq",
                           t1s.DBF_NUMRECORDS: 1000,
                           t1s.DBF_RECORDSIZE: 100,
                           t1s.DBF_WHERECLAUSE: 'fname="Alice"',
                           t1s.DBF_MATCHINGRECORDIDS: [1, 2, 3],
                           t1s.DBF_MATCHINGRECORDHASHES: ["hash1", "hash2",
                                                          "hash3"]})
    this_database.add_row(t1s.DBP_TABLENAME,
                          {t1s.DBP_PERFORMERNAME: "white knight",
                           t1s.DBP_TESTCASEID: "TC001",
                           t1s.DBP_FQID: 1,
                           t1s.DBP_SELECTIONCOLS: "*",
                           t1s.DBP_RETURNEDRECORDIDS: [1, 2, 3],
                           t1s.DBP_RETURNEDRECORDHASHES: ["hash1", "hash2",
                                                          "hash3"],
                           t1s.DBP_QUERYLATENCY: 1000.00,
                           t1s.DBP_ISMODIFICATIONQUERY: False,
                           t1s.DBP_ISTHROUGHPUTQUERY: False})
    this_database.add_row(t1s.DBP_TABLENAME,
                          {t1s.DBP_PERFORMERNAME: "white knight",
                           t1s.DBP_TESTCASEID: "TC001",
                           t1s.DBP_FQID: 1,
                           t1s.DBP_SELECTIONCOLS: "*",
                           t1s.DBP_RETURNEDRECORDIDS: [1, 2],
                           t1s.DBP_RETURNEDRECORDHASHES: ["hash1", "hash2"],
                           t1s.DBP_QUERYLATENCY: 1000.00,
                           t1s.DBP_ISMODIFICATIONQUERY: False,
                           t1s.DBP_ISTHROUGHPUTQUERY: False})
