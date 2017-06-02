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
import spar_python.report_generation.ta1.ta1_config as t1c
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_database as t1d

class ConfigTest(unittest.TestCase):

    def test_get_perf_incorrect_constraint_list(self):
        conf = t1c.Ta1Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        expected_perf_incorrect_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME, conf.performername),
            (t1s.DBP_TABLENAME, t1s.DBP_ISTHROUGHPUTQUERY, False),
            (t1s.DBP_TABLENAME, t1s.DBP_ISMODIFICATIONQUERY, False)]
        actual_perf_incorrect_constraint_list = conf.get_constraint_list(
            require_correct=False, usebaseline=False)
        self.assertEquals(expected_perf_incorrect_constraint_list,
                          actual_perf_incorrect_constraint_list)

    def test_get_perf_correct_constraint_list(self):
        conf = t1c.Ta1Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        expected_perf_correct_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT, True),
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME, conf.performername),
            (t1s.DBP_TABLENAME, t1s.DBP_ISTHROUGHPUTQUERY, False),
            (t1s.DBP_TABLENAME, t1s.DBP_ISMODIFICATIONQUERY, False)]
        actual_perf_correct_constraint_list = conf.get_constraint_list(
            require_correct=True, usebaseline=False)
        self.assertEquals(expected_perf_correct_constraint_list,
                          actual_perf_correct_constraint_list)

    def test_get_base_incorrect_constraint_list(self):
        conf = t1c.Ta1Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        expected_base_incorrect_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME, conf.baselinename),
            (t1s.DBP_TABLENAME, t1s.DBP_ISTHROUGHPUTQUERY, False),
            (t1s.DBP_TABLENAME, t1s.DBP_ISMODIFICATIONQUERY, False)]
        actual_base_incorrect_constraint_list = conf.get_constraint_list(
            require_correct=False, usebaseline=True)
        self.assertEquals(expected_base_incorrect_constraint_list,
                          actual_base_incorrect_constraint_list)

    def test_get_base_correct_constraint_list(self):
        conf = t1c.Ta1Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        expected_base_correct_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT, True),
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME, conf.baselinename),
            (t1s.DBP_TABLENAME, t1s.DBP_ISTHROUGHPUTQUERY, False),
            (t1s.DBP_TABLENAME, t1s.DBP_ISMODIFICATIONQUERY, False)]
        actual_base_correct_constraint_list = conf.get_constraint_list(
            require_correct=True, usebaseline=True)
        self.assertEquals(expected_base_correct_constraint_list,
                          actual_base_correct_constraint_list)

    def test_get_base_correct_constraint_list_for_mods_and_throughput(self):
        conf = t1c.Ta1Config()
        conf.performername = "PERF"
        conf.baselinename = "MIT"
        expected_base_correct_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT, True),
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME, conf.baselinename),
            (t1s.DBP_TABLENAME, t1s.DBP_ISTHROUGHPUTQUERY, True),
            (t1s.DBP_TABLENAME, t1s.DBP_ISMODIFICATIONQUERY, True)]
        actual_base_correct_constraint_list = conf.get_constraint_list(
            require_correct=True, usebaseline=True, mod=True, throughput=True)
        self.assertEquals(expected_base_correct_constraint_list,
                          actual_base_correct_constraint_list)

    def test_results_db(self):
        conf = t1c.Ta1Config()
        conf.results_db_path = ":memory:"
        self.assertEquals(type(conf.results_db), t1d.Ta1ResultsDB)
