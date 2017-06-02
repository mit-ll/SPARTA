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


# SPAR imports:
import spar_python.report_generation.ta1.ta1_section as section
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.common.latex_classes as latex_classes
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_analysis_percentiles as percentiles
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai
import spar_python.report_generation.common.graphing as graphing

class LatencyPercentiles(object):
    """Produces all the objects describing percentiles for a given
    configuration of database, query type and selection cols."""
    def __init__(self, section, config, inp):
        """Initializes the object with a section object, a configuration object
        and an input object."""
        self._section = section
        self._config = config
        self._inp = inp
        self.name = "SELECT %s %s Queries" % (self._inp[t1s.DBP_SELECTIONCOLS],
                                              self._inp[t1s.DBF_CAT])
        self._percentile_getter = None
        self._populate_charts()

    def has_values(self):
        """Returns True if the LatencyPercentiles object has values, and False
        otherwise."""
        return self._percentile_getter.has_values()

    def _make_chart(self, caption, tag):
        """Creates a chart"""
        return latex_classes.LatexChart(
            caption, tag,
            ["b=%s" % str(i) for i in xrange(1, self._config.b_max + 1)],
            ["a=%s" % str(i) for i in xrange(0, self._config.a_max + 1)])

    def _populate_charts(self):
        caption = "Type %s Query Percentiles (%s)" % (
            self._inp[t1s.DBF_CAT], self._inp.test_db.get_short_database_name())
        # generate the charts:
        query_percentiles_min_chart = self._make_chart(
            caption="Minimum Passing " + caption,
            tag=self._section.get_tag(inp=self._inp) + "_min")
        query_percentiles_max_chart = self._make_chart(
            caption="Maximum Passing " + caption,
            tag=self._section.get_tag(inp=self._inp) + "_max")
        query_percentiles_count_chart = self._make_chart(
            caption="Count of Passing " + caption,
            tag=self._section.get_tag(inp=self._inp) + "_count")
        performer_constraint_list = self._config.get_constraint_list(
            require_correct=True,
            usebaseline=False) +  self._inp.get_constraint_list()
        baseline_constraint_list = self._config.get_constraint_list(
            require_correct=True,
            usebaseline=True) +  self._inp.get_constraint_list()
        self._percentile_getter = percentiles.Ta1PercentileGetter(
            self._config.results_db, performer_constraint_list,
            baseline_constraint_list)
        if not self.has_values():
            return
        self.performer_percentiles = [
            round(perc, 3) for perc in
            self._percentile_getter.get_performer_percentiles()]
        self.baseline_percentiles = [
            round(perc, 3) for perc in
            self._percentile_getter.get_baseline_percentiles()]
        for a in xrange(0, self._config.a_max + 1):
            for b in xrange(1, self._config.b_max + 1):
                all_met = self._percentile_getter.get_all_met(a, b)
                (min_met, max_met, count_met) = (None, None, 0)
                (min_color, max_color, count_color) = ("red", "red", "red")
                if all_met:
                    (min_met, max_met, count_met) = (
                        min(all_met), max(all_met), len(all_met))
                    if min_met == 1: min_color = "green"
                    else: min_color = "yellow"
                    if max_met == 100: max_color = "green"
                    else: max_color = "yellow"
                    if count_met == 100: count_color = "green"
                    else: count_color = "yellow"
                query_percentiles_min_chart.add_cell("b=%s" % str(b),
                                                     "a=%s" % str(a),
                                                     min_met, min_color)
                query_percentiles_max_chart.add_cell("b=%s" % str(b),
                                                     "a=%s" % str(a),
                                                     max_met, max_color)
                query_percentiles_count_chart.add_cell("b=%s" % str(b),
                                                       "a=%s" % str(a),
                                                       count_met, count_color)
        self.percentiles_min_chart = query_percentiles_min_chart.get_string()
        self.percentiles_max_chart = query_percentiles_max_chart.get_string()
        self.percentiles_cnt_chart = query_percentiles_count_chart.get_string()
        graph = graphing.comparison_percentile_graph(
            self._percentile_getter, "query latency (s)")
        graph_path = self._section.get_img_path(inp=self._inp)
        graphimage = latex_classes.LatexImage(
            caption=caption,
            tag=self._section.get_tag(inp=self._inp) + "_graph",
            image_path=graph_path)
        self._section.write(graph_path, graph)
        self.percentiles_graph = graphimage.get_string()


class Ta1PercentilesAuxSection(section.Ta1Section):
    """The percentiles section of the TA1 report"""

    def _store_percentiles(self):
        """Stores the LaTeX string representing the query percentiles table
        on the output object."""
        db_constraint_list = self._config.get_constraint_list(
            require_correct=True)
        db_categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS),
                           (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE)],
            constraint_list=db_constraint_list)
        # the object to be stored and then iterated over in jinja:
        self._outp["databases"] = {}
        for (dbnr, dbrs) in db_categories:
            db_inp = t1ai.Input()
            db_inp[t1s.DBF_NUMRECORDS] = dbnr
            db_inp[t1s.DBF_RECORDSIZE] = dbrs
            query_constraint_list = db_constraint_list + db_inp.get_constraint_list()
            query_categories = self._config.results_db.get_unique_query_values(
                simple_fields=[(t1s.DBF_TABLENAME, t1s.DBF_CAT),
                               (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS)],
                constraint_list=query_constraint_list)
            self._outp["databases"][(dbnr, dbrs)] = {
                'name': db_inp.test_db.get_short_database_name(),
                'query_cats': []}
            for (query_cat, selection_cols) in query_categories:
                query_inp = t1ai.Input()
                query_inp[t1s.DBF_CAT] = query_cat
                query_inp[t1s.DBF_NUMRECORDS] = dbnr
                query_inp[t1s.DBF_RECORDSIZE] = dbrs
                query_inp[t1s.DBP_SELECTIONCOLS] = selection_cols
                latency_percentiles = LatencyPercentiles(
                    self, self._config, query_inp)
                self._outp["databases"][
                    (dbnr, dbrs)]['query_cats'].append(latency_percentiles)               

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_percentiles()
