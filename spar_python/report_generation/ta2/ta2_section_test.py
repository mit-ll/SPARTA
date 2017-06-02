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
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.ta2.ta2_config as ta2_config
import spar_python.report_generation.ta2.ta2_report_generator as t2rg
import spar_python.report_generation.ta2.ta2_section as ta2_section

class SectionTest(unittest.TestCase):

    def test_get_tag(self):
        this_config = ta2_config.Ta2Config()
        this_config.performername = "white knight"
        this_config.results_db_path = ":memory:"
        this_report_generator = t2rg.Ta2ReportGenerator(jinja_env=None,
                                                        config=this_config)
        this_section = ta2_section.Ta2Section(
            jinja_template=None, report_generator=this_report_generator)
        self.assertEqual(
            this_section.get_tag(aux="silly section tagging"),
            "Ta2Section_sillysectiontagging")
