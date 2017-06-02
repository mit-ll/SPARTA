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

class Ta1OverviewEqSection(t1soc.Ta1OverviewCommonSection):
    """The equality overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator):
        """Initializes the section with a jinja template and a report generator.
        """
        cat = t1s.CATEGORIES.EQ
        super(Ta1OverviewEqSection, self).__init__(
            jinja_template, report_generator, cat)

    def _store_latency_by_fieldtype_graph(self):
        """Stores the latency as a function of fieldtype graph."""
        # find all of the naming and reference strings:
        caption = "Type %s Queries (%s)" % (
            self._inp[t1s.DBF_CAT],
            self._inp.test_db.get_short_database_name())
        tag = self.get_tag(self._inp)
        graph_path = self.get_img_path(self._inp, "byfieldtype")
        # find the data and create the graph:
        constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list())
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
            constraint_list=constraint_list,
            atomic_fields_and_functions=[
                (t1s.DBA_FIELDTYPE,
                 t1s.Ta1ResultsSchema().get_complex_function(
                     t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE))])
        (x_label, y_label) = (
            self._config.var_nummatches + " = # new matching records",
            self._config.var_ql + " = query latency (s)")
        datasets = []
        for (selection_cols, field_type) in categories:
            this_constraint_list = constraint_list + [
                (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols),
                (t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE, field_type)]
            [x_values,
             y_values] = self._config.results_db.get_query_values(
                [(t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS),
                 (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
                constraint_list=this_constraint_list)
            try:
                inputs = [x_values]
                outputs = y_values
                function = regression.regress(
                    function_to_regress=self._config.ql_all_ftr,
                    outputs=outputs, inputs=inputs)
            except regression.BadRegressionInputError:
                function = None
            datasets.append(
                (x_values, y_values,
                 "SELECT %s on %ss" % (selection_cols, field_type), function))
        graph = graphing.graph2d(
            plot_name="", datasets=datasets, x_label=x_label, y_label=y_label)
        self.write(graph_path, graph)
        graph_image = latex_classes.LatexImage(caption, tag, graph_path)
        self._outp["latency_by_fieldtype_graph"] = graph_image.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        super(Ta1OverviewEqSection, self)._populate_output()
        self._store_latency_by_fieldtype_graph()
