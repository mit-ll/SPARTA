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
import spar_python.report_generation.common.regression as regression

# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta1OverviewP1EqDnfSection(t1soc.Ta1OverviewCommonSection):
    """The Equality-DNF overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator):
        """Initializes the section with a jinja template and a report generator.
        """
        cat = t1s.CATEGORIES.P1
        subcat = t1s.SUBCATEGORIES[cat].eqdnf
        super(Ta1OverviewP1EqDnfSection, self).__init__(
            jinja_template, report_generator, cat, subcat)

    def _get_parameters(self, selection_cols):
        """Returns parameters for the 3d graph."""
        parameters = {}
        parameters["z_label"] = (
            self._config.var_sumfirstmatches
            + " = sum # first term matches")
        # find the data:
        this_constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list() + [
                (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols)])
        parameters["values"] =  self._config.results_db.get_query_values(
            simple_fields=[
                (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS),
                (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
            full_fields_and_functions=[
                (t1s.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM, sum)],
            constraint_list=this_constraint_list)
        parameters["ftr"] = self._config.ql_p1dnf_ftr
        return parameters

    def _store_complex_function(self, selection_cols):
        """Stores the higher-order best-fit curve for the dnf."""
        # because python cannot handle attribute names containing "*", we must
        # map * to something else:
        selection_cols_attr_string = selection_cols
        if selection_cols == "*":
            selection_cols_attr_string = "star"
        this_constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list() + [
                (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols)])
        [x_values, y_values, c_values, t_values,
         z_values] = self._config.results_db.get_query_values(
            simple_fields=[
                (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS),
                (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
                (t1s.DBF_TABLENAME, t1s.DBF_P1NUMCLAUSES),
                (t1s.DBF_TABLENAME, t1s.DBF_P1NUMTERMSPERCLAUSE)],
            full_fields_and_functions=[
                (t1s.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM, sum)],
            constraint_list=this_constraint_list)
        ftr = self._config.ql_p1dnfcomplex_ftr
        inputs = [x_values, c_values, t_values, z_values]
        outputs = y_values
        try:
            function = regression.regress(
                function_to_regress=ftr, outputs=outputs, inputs=inputs)
            functionstr = function.string
            rsquared = function.get_rsquared(inputs=inputs, outputs=outputs)
        except regression.BadRegressionInputError:
            functionstr = None
            rsquared = None
        for (suffix, value) in [("higher_order_functionstr", functionstr),
                                ("higher_order_rsquared", rsquared)]:
            self._outp[selection_cols_attr_string + "_" + suffix] = value

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
            self._store_complex_function(selection_cols)
            self._store_3d_latency_graph(selection_cols)
