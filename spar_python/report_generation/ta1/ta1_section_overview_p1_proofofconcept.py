# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Section class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  19 Sep 2013   SY             Original version
# *****************************************************************

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta1.ta1_section_overview_common as t1soc
import spar_python.report_generation.ta1.ta1_schema as t1s

# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta1OverviewP1POCSection(t1soc.Ta1OverviewCommonSection):
    """The Equality-Or overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator, subcat):
        """Initializes the section with a jinja template and a report generator.
        """
        cat = t1s.CATEGORIES.P1
        super(Ta1OverviewP1POCSection, self).__init__(
            jinja_template, report_generator, cat, subcat)

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        # establish whether queries on the given subcategory were run:
        this_tested_constraint_list = (
            self._config.get_constraint_list(
                require_correct=False, usebaseline=True) +
            self._inp.get_constraint_list())
        tested_values = self._config.results_db.get_query_values(
            simple_fields=[(t1s.DBP_TABLENAME, "ROWID")],
            constraint_list=this_tested_constraint_list)
        if tested_values:
            self._outp["tested"] = True
        else:
            self._outp["tested"] = False
        # establish whether thos queries were correct:
        this_passed_constraint_list = (
            self._config.get_constraint_list(
                require_correct=True, usebaseline=False) +
            self._inp.get_constraint_list())
        passed_values = self._config.results_db.get_query_values(
            simple_fields=[(t1s.DBP_TABLENAME, "ROWID")],
            constraint_list=this_passed_constraint_list)
        if passed_values:
            self._outp["passed"] = True
        else:
            self._outp["passed"] = False
