# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests the Section class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Sep 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_config as ta1_config
import spar_python.report_generation.ta1.ta1_report_generator as t1rg
import spar_python.report_generation.ta1.ta1_section as ta1_section

class SectionTest(unittest.TestCase):

    def test_get_tag(self):
        this_config = ta1_config.Ta1Config()
        this_config.performername = "white knight"
        this_config.results_db_path = ":memory:"
        this_report_generator = t1rg.Ta1ReportGenerator(jinja_env=None,
                                                        config=this_config)
        this_section = ta1_section.Ta1Section(
            jinja_template=None, report_generator=this_report_generator)
        this_db_num_records = 101
        this_query_subcat = "eq-and"
        this_selection_cols = "*"
        this_inp = t1ai.Input()
        this_inp[t1s.DBF_NUMRECORDS] = this_db_num_records
        this_inp[t1s.DBF_SUBCAT] = this_query_subcat
        this_inp[t1s.DBP_SELECTIONCOLS] = this_selection_cols       
        self.assertEqual(
            this_section.get_tag(inp=this_inp),
            "Ta1Section_whiteknight_101_eq-and_*")
