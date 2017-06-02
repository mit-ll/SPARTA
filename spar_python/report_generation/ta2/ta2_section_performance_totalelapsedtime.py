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
#  23 Oct 2013   SY             Original version
# *****************************************************************

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta2.ta2_section_performance as t2sp
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.ta2.ta2_analysis_percentiles as percentiles
import spar_python.report_generation.common.graphing as graphing
import spar_python.report_generation.common.latex_classes as latex_classes

# logging:
LOGGER = logging.getLogger(__file__)

class Ta2TotalElapsedTimeSection(t2sp.Ta2PerformanceSection):
    """The total elapsed time section of the TA2 report"""

    def _store_totalelapsedtime_graphs(self):
        """Stores the total elapsed time information."""
        fields=[
            (t2s.PARAM_TABLENAME, t2s.PARAM_D),
            (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_W),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_EVALUATIONLATENCY)]
        performer_constraint_list = self._config.get_constraint_list(
            fields, require_correct=True, usebaseline=False, require_random=True)
        baseline_constraint_list = self._config.get_constraint_list(
            fields, require_correct=True, usebaseline=True, require_random=True)
        percentile_getter = percentiles.Ta2PercentileGetter(
            self._config.results_db, performer_constraint_list,
            baseline_constraint_list)
        all_met = percentile_getter.get_all_met(self._config.baaratio, 0)
        self._outp["nummet"] = len(all_met)
        if len(all_met) == 100:
            self._outp["baamet"] = True
        else:
            self._outp["baamet"] = False
        # create the percentiles graph:
        percentiles_caption = "Total Elapsed Time Percentiles"
        percentiles_tag = "totalelapsedtimepercentiles"
        percentiles_graph_path = self.get_img_path(aux=percentiles_tag)
        percentiles_graph = graphing.comparison_percentile_graph(
            percentile_getter=percentile_getter,
            y_label="total elapsed time (s)", y_scale='log')
        percentiles_latexgraph = latex_classes.LatexImage(
            caption=percentiles_caption, tag=percentiles_tag,
            image_path=percentiles_graph_path, scale=.8)
        percentiles_latexgraph_string = percentiles_latexgraph.get_string()
        self.write(percentiles_graph_path, percentiles_graph)
        self._outp[
            "totalelapsedtimepercentiles_graph"] = percentiles_latexgraph_string
        # create the ratio graph:
        ratio_values = [float(performer_val) / float(baseline_val)
                        for (performer_val, baseline_val) in
                        zip(percentile_getter.get_performer_percentiles(),
                            percentile_getter.get_baseline_percentiles())]
        ratio_caption = "Total Elapsed Time Percentile Ratios"
        ratio_tag = "totalelapsedtimepercentilesratios"
        ratio_graph_path = self.get_img_path(aux=ratio_tag)
        ratio_graph = graphing.general_percentile_graph(
            datasets=[(ratio_values,
                       "Performer to Baseline Total Elapsed Time Ratio")],
            y_label="Performer to Baseline Ratio")
        ratio_latexgraph = latex_classes.LatexImage(
            caption=ratio_caption, tag=ratio_tag,
            image_path=ratio_graph_path, scale=.8)
        ratio_latexgraph_string = ratio_latexgraph.get_string()
        self.write(ratio_graph_path, ratio_graph)
        self._outp["totalelapsedtimeratio_graph"] = ratio_latexgraph_string
        # find the mean ratio:
        self._outp["meantotalelapsedtimeratio"] = round(
            sum(ratio_values) / float(len(ratio_values)),
            self._config.numsigfigs)
        
    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_totalelapsedtime_graphs()        
    
