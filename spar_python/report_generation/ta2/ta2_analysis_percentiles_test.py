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

# SPAR imports:
import spar_python.report_generation.ta2.ta2_analysis_percentiles as percentiles
import spar_python.report_generation.ta2.ta2_schema as t2s

PERFORMERNAME = "white knight"
BASELINENAME = "eight-year-old on donkey"
PERFORMER_CONSTRAINT_LIST = [
    (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_PERFORMERNAME, PERFORMERNAME)]
BASELINE_CONSTRAINT_LIST = [
    (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_PERFORMERNAME, BASELINENAME)]

class StubResultsDatabase(object):
    """This is a stub database class intended only for use with these unit
    tests."""
    def __init__(self, performer_values, baseline_values):
        """Initializes the stub database with the specified values."""
        self._baseline_values = baseline_values
        self._performer_values = performer_values
    def get_values(self, fields, constraint_list=[]):
        if constraint_list == BASELINE_CONSTRAINT_LIST:
            return self._baseline_values
        elif constraint_list == PERFORMER_CONSTRAINT_LIST:
            return self._performer_values
        else:
            assert False

class TestPercentileGetter(unittest.TestCase):

    def test_nonidentical_query_ids(self):
        # make sure that percentiles are only computed on queries for which both
        # the baseline and the performer have timing information:
        performer_iids = range(200)
        performer_encryption_latencies = [
            3.0 for idx in xrange(100)] + [6.0 for idx in xrange(100)]
        performer_decryption_latencies = performer_encryption_latencies[:]
        performer_evaluation_latencies = [
            4.0 for idx in xrange(100)] + [8.0 for idx in xrange(100)]
        baseline_iids = range(100, 300)
        baseline_encryption_latencies = [
            9.0 for idx in xrange(100)] + [6.0 for idx in xrange(100)]
        baseline_decryption_latencies = baseline_encryption_latencies[:]
        baseline_evaluation_latencies = [
            12.0 for idx in xrange(100)] + [8.0 for idx in xrange(100)]
        results_db = StubResultsDatabase([performer_iids,
                                          performer_encryption_latencies,
                                          performer_evaluation_latencies,
                                          performer_decryption_latencies],
                                         [baseline_iids,
                                          baseline_encryption_latencies,
                                          baseline_evaluation_latencies,
                                          baseline_decryption_latencies])
        percentile_getter = percentiles.Ta2PercentileGetter(
            results_db, PERFORMER_CONSTRAINT_LIST, BASELINE_CONSTRAINT_LIST)
        expected_performer_percentiles = [20.0 for idx in xrange(100)]
        expected_baseline_percentiles = [30.0 for idx in xrange(100)]
        performer_percentiles = percentile_getter.get_performer_percentiles()
        baseline_percentiles = percentile_getter.get_baseline_percentiles()
        self.assertEqual(expected_performer_percentiles, performer_percentiles)
        self.assertEqual(expected_baseline_percentiles, baseline_percentiles)

    def test_get_all_met(self):
        performer_iids = range(2000)
        performer_encryption_latencies = [500.0 + float(idx)/float(4)
                                          for idx in xrange(2000)]
        performer_evaluation_latencies = [1000.0 + float(idx)/float(2)
                                          for idx in xrange(2000)]
        performer_decryption_latencies = performer_encryption_latencies[:]
        baseline_iids = performer_iids[:]
        baseline_encryption_latencies = [0 for idx in xrange(2000)]
        baseline_evaluation_latencies = [idx*2 for idx in xrange(2000)]
        baseline_decryption_latencies = baseline_encryption_latencies[:]
        results_db = StubResultsDatabase([performer_iids,
                                          performer_encryption_latencies,
                                          performer_evaluation_latencies,
                                          performer_decryption_latencies],
                                         [baseline_iids,
                                          baseline_encryption_latencies,
                                          baseline_evaluation_latencies,
                                          baseline_decryption_latencies])
        percentile_getter = percentiles.Ta2PercentileGetter(
            results_db, PERFORMER_CONSTRAINT_LIST, BASELINE_CONSTRAINT_LIST)
        # for b = 1 and a = 1000, performer >= a + b*baseline for
        # the second half of the percentiles.
        expected_all_met = range(51, 101)
        all_met = percentile_getter.get_all_met(1000, 1)
        self.assertEqual(expected_all_met, all_met)
