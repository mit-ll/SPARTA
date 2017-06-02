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
import spar_python.report_generation.common.latex_classes as latex_classes

# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta1OverviewP8P9EqSection(t1soc.Ta1OverviewCommonSection):
    """The equality overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator, cat):
        """Initializes the section with a jinja template and a report generator.
        """
        subcat = t1s.SUBCATEGORIES[cat].eq
        super(Ta1OverviewP8P9EqSection, self).__init__(
            jinja_template, report_generator, cat, subcat)

    def _get_parameters(self, selection_cols):
        """Returns parameters for the 3d graph."""
        parameters = {}
        parameters["z_label"] = (
            self._config.var_sumfirstmatches + " = # first term matches")
        # find the data:
        this_constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list() + [
                (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols),
                (t1s.DBF_TABLENAME, t1s.DBF_P8M, self._config.fixed_m),
                (t1s.DBF_TABLENAME, t1s.DBF_P8N, self._config.fixed_n)])
        def this_func(num_records_returned_matching_each_term):
            return sum(num_records_returned_matching_each_term[
                :self._config.fixed_n - self._config.fixed_m])
        parameters["values"] =  self._config.results_db.get_query_values(
            simple_fields=[
                (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS),
                (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
            atomic_fields_and_functions=[
                (t1s.DBA_NUMMATCHINGRECORDS, this_func)],
            constraint_list=this_constraint_list)
        parameters["ftr"] = self._config.ql_p8eq_ftr
        return parameters

    def _store_chart(self, selection_cols):
        """Stores the theshold m and n -dependent latency chart"""
        assert selection_cols in ["id", "*"], (
            "invalid selection cols %s" % selection_cols)
        # because python cannot handle attribute names containing "*", we must
        # map * to something else:
        selection_cols_attr_string = selection_cols
        if selection_cols == "*":
            selection_cols_attr_string = "star"
        constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list() + [
                (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols)])
        this_non_standard_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS,
             "%s.%s < " + str(self._config.threshold_numrecords_max)),
            (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS,
             "%s.%s > " + str(self._config.threshold_numrecords_min))]
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBF_TABLENAME, t1s.DBF_P8N),
                           (t1s.DBF_TABLENAME, t1s.DBF_P8M)],
            constraint_list=constraint_list,
            non_standard_constraint_list=this_non_standard_constraint_list)
        n_values = list(set([n for (n, m) in categories]))
        n_values.sort()
        m_values = list(set([m for (n, m) in categories]))
        m_values.sort()
        chart = latex_classes.LatexChart(
            caption=(r"\texttt{select %s} Threshold Query Latnecy"
                     % selection_cols),
            tag=self.get_tag(aux=selection_cols_attr_string),
            top_header=["n=%s" % n for n in n_values],
            left_header=["m=%s" % m for m in m_values])
        for (n, m) in categories:
            this_constraint_list = constraint_list + [
                (t1s.DBF_TABLENAME, t1s.DBF_P8N, n),
                (t1s.DBF_TABLENAME, t1s.DBF_P8M, m)]
            latencies = self._config.results_db.get_query_values(
                simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
                constraint_list=this_constraint_list,
                non_standard_constraint_list=this_non_standard_constraint_list)
            latencies = latencies[0]
            if latencies:
                mean_latency = float(sum(latencies)) / float(len(latencies))
                chart.add_cell(top_elt="n=%s" % n, left_elt="m=%s" % m,
                               content=str(round(mean_latency, 3)))
        chartstr = chart.get_string()
        self._outp[selection_cols_attr_string + "_chart"] = chartstr
        
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
            self._store_chart(selection_cols)
