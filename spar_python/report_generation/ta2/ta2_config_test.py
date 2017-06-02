# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests the Config class
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
import spar_python.report_generation.ta2.ta2_config as t2c
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.ta2.ta2_database as t2d

class ConfigTest(unittest.TestCase):

    def test_get_perf_incorrect_constraint_list(self):
        conf = t2c.Ta2Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        fields = [(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY)]
        expected_perf_incorrect_constraint_list = [
            (t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_PERFORMERNAME,
             conf.performername)]
        actual_perf_incorrect_constraint_list = conf.get_constraint_list(
            fields=fields, require_correct=False, usebaseline=False)
        self.assertEquals(expected_perf_incorrect_constraint_list,
                          actual_perf_incorrect_constraint_list)

    def test_get_perf_correct_keygen_constraint_list(self):
        conf = t2c.Ta2Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        fields = [(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY)]
        expected_perf_correct_constraint_list = [
            (t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_PERFORMERNAME,
             conf.performername)]
        actual_perf_correct_constraint_list = conf.get_constraint_list(
            fields=fields, require_correct=True, usebaseline=False)
        self.assertEquals(expected_perf_correct_constraint_list,
                          actual_perf_correct_constraint_list)
        
    def test_get_perf_correct_eval_constraint_list(self):
        conf = t2c.Ta2Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        fields = [(t2s.PEREVALUATION_TABLENAME,
                   t2s.PEREVALUATION_EVALUATIONLATENCY)]
        expected_perf_correct_constraint_list = [
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_CORRECTNESS, True),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_PERFORMERNAME,
             conf.performername)]
        actual_perf_correct_constraint_list = conf.get_constraint_list(
            fields=fields, require_correct=True, usebaseline=False)
        self.assertEquals(expected_perf_correct_constraint_list,
                          actual_perf_correct_constraint_list)

    def test_get_base_incorrect_constraint_list(self):
        conf = t2c.Ta2Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        fields = [(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY)]
        expected_base_incorrect_constraint_list = [
            (t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_PERFORMERNAME,
             conf.baselinename)]
        actual_base_incorrect_constraint_list = conf.get_constraint_list(
            fields=fields, require_correct=False, usebaseline=True)
        self.assertEquals(expected_base_incorrect_constraint_list,
                          actual_base_incorrect_constraint_list)

    def test_get_base_correct_keygen_constraint_list(self):
        conf = t2c.Ta2Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        fields = [(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY)]
        expected_base_correct_constraint_list = [
            (t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_PERFORMERNAME,
             conf.baselinename)]
        actual_base_correct_constraint_list = conf.get_constraint_list(
            fields=fields, require_correct=True, usebaseline=True)
        self.assertEquals(expected_base_correct_constraint_list,
                          actual_base_correct_constraint_list)

    def test_results_db(self):
        conf = t2c.Ta2Config()
        conf.results_db_path = ":memory:"
        self.assertEquals(type(conf.results_db), t2d.Ta2ResultsDB)
