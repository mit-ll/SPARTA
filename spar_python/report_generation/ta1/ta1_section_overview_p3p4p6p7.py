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

class Ta1OverviewP3P4P6P7Section(t1soc.Ta1OverviewCommonSection):
    """The equality overview section of the TA1 report."""

    def _store_latency_by_keywordlen_graph(self):
        """Stores the latency as a function of keywordlen graph."""
        # find all of the naming and reference strings:
        caption = "Type %s Queries (%s)" % (
            self._inp[t1s.DBF_CAT],
            self._inp.test_db.get_short_database_name())
        tag = self.get_tag(inp=self._inp)
        graph_path = self.get_img_path(inp=self._inp, aux="bykeyword")
        # find the data and create the graphs, etc:
        keywordlen_numrecords_max = self._config.keywordlen_numrecords_max[
            self._inp["cat_number"]]
        keywordlen_numrecords_min = self._config.keywordlen_numrecords_min[
            self._inp["cat_number"]]
        self._outp["keywordlen_numrecords_max"] = keywordlen_numrecords_max
        self._outp["keywordlen_numrecords_min"] = keywordlen_numrecords_min
        this_constraint_list = (
            self._config.get_constraint_list()
            + self._inp.get_constraint_list())
        this_non_standard_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS,
             "%s.%s<" + str(keywordlen_numrecords_max)),
            (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS,
             "%s.%s>" + str(keywordlen_numrecords_min))]
        these_atomic_fields_and_functions = [
            (t1s.DBA_KEYWORDLEN,
             t1s.Ta1ResultsSchema().get_complex_function(
                 t1s.DBA_TABLENAME, t1s.DBA_KEYWORDLEN))]
        categories = self._config.results_db.get_unique_query_values(
             [(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
             atomic_fields_and_functions=these_atomic_fields_and_functions,
             constraint_list=this_constraint_list,
             non_standard_constraint_list=this_non_standard_constraint_list)
        y_label = (
            self._config.var_ql + " = query latency (s)")
        inputs = []
        for (selection_cols, keyword_len) in categories:
            data = self._config.results_db.get_query_values(
                [(t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
                constraint_list=this_constraint_list + [
                    (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS, selection_cols),
                    (t1s.DBA_TABLENAME, t1s.DBA_KEYWORDLEN, keyword_len)],
                non_standard_constraint_list=this_non_standard_constraint_list)
            label = "SELECT %s, keyword legnth %s" % (
                selection_cols, str(keyword_len))
            inputs.append((label, data))
        if inputs:
            graph = graphing.box_plot("", inputs)
            self.write(graph_path, graph)
            graphimage = latex_classes.LatexImage(caption, tag, graph_path)
            self._outp["latency_by_keywordlen_graph"] = graphimage.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        super(Ta1OverviewP3P4P6P7Section, self)._populate_output()
        self._store_latency_by_keywordlen_graph()
