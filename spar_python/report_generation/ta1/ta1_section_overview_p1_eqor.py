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

class Ta1OverviewP1EqOrSection(t1soc.Ta1OverviewCommonSection):
    """The Equality-Or overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator):
        """Initializes the section with a jinja template and a report generator.
        """
        cat = t1s.CATEGORIES.P1
        subcat = t1s.SUBCATEGORIES[cat].eqor
        super(Ta1OverviewP1EqOrSection, self).__init__(
            jinja_template, report_generator, cat, subcat)

    def _get_parameters(self, selection_cols):
        """Returns parameters for the 3d graph."""
        parameters = {}
        parameters["z_label"] = (
            self._config.var_summatches
            + " = sum # recs each term")
        # find the data:
        this_constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list() + [
                (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols)])
        parameters["values"] =  self._config.results_db.get_query_values(
            simple_fields=[
                (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS),
                (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
            atomic_fields_and_functions=[(t1s.DBA_NUMMATCHINGRECORDS, sum)],
            constraint_list=this_constraint_list)
        parameters["ftr"] = self._config.ql_p1or_ftr
        return parameters

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        this_constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list())
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
            constraint_list=this_constraint_list)
        for selection_cols in categories:
            self._store_3d_latency_graph(selection_cols)
