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
import spar_python.report_generation.common.section as section
import spar_python.report_generation.ta1.ta1_section_overview_common as t1soc
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.common.graphing as graphing
import spar_python.report_generation.common.latex_classes as latex_classes

# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta1OverviewP2Section(t1soc.Ta1OverviewCommonSection):
    """The equality overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator):
        """Initializes the section with a jinja template and a report generator.
        """
        cat = t1s.CATEGORIES.P2
        super(Ta1OverviewP2Section, self).__init__(
            jinja_template, report_generator, cat)

    def _get_parameters(self, selection_cols):
        """Returns parameters for the 3d graph."""
        parameters = {}
        parameters["z_label"] = (
            self._config.var_rangesize + " = range size")
        # find the data:
        this_constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list() + [
                (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols)])
        these_atomic_fields_and_functions = [
            (t1s.DBA_RANGE,
             t1s.Ta1ResultsSchema().get_complex_function(t1s.DBA_TABLENAME,
                                                         t1s.DBA_RANGE))]
        parameters["values"] = self._config.results_db.get_query_values(
            [(t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS),
             (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
            constraint_list=this_constraint_list,
            atomic_fields_and_functions=these_atomic_fields_and_functions)
        parameters["ftr"] = self._config.ql_p2_ftr
        return parameters

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        super(Ta1OverviewP2Section, self)._populate_output()
        this_constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list())
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
            constraint_list=this_constraint_list)
        for selection_cols in categories:
            self._store_3d_latency_graph(selection_cols)
