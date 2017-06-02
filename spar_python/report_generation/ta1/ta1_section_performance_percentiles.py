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

class Ta1PercentilesSection(section.Ta1Section):
    """The percentiles section of the TA1 report"""

    def _store_query_percentiles_table(self):
        """Stores the LaTeX string representing the query percentiles table
        on the output object."""
        constraint_list = self._config.get_constraint_list(
            require_correct=True)
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS),
                           (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE),
                           (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
                           (t1s.DBF_TABLENAME, t1s.DBF_CAT)],
            constraint_list=constraint_list)
        # create the percentiles table:
        caption = "Number of Percentiles passing the $%s+%sx$ requirement" % (
            str(self._config.a_req), str(self._config.b_req))
        percentiles_table = latex_classes.LatexTable(
            caption, "perc_main",
            ["DBNR", "DBRS", "Select", "Query Type", "Num Passing $\%$iles"])
        # compute number of percentiles met for every query category:
        for (dbnr, dbrs, selection_cols, query_cat) in categories:
            inp = t1ai.Input()
            inp[t1s.DBF_CAT] = query_cat
            inp[t1s.DBF_NUMRECORDS] = dbnr
            inp[t1s.DBF_RECORDSIZE] = dbrs
            inp[t1s.DBP_SELECTIONCOLS] = selection_cols
            performer_constraint_list = self._config.get_constraint_list(
                usebaseline=False) + inp.get_constraint_list()
            baseline_constraint_list = self._config.get_constraint_list(
                usebaseline=True) + inp.get_constraint_list()
            percentile_getter = percentiles.Ta1PercentileGetter(
                self._config.results_db, performer_constraint_list,
                baseline_constraint_list)
            if percentile_getter.has_values():
                all_met = percentile_getter.get_all_met(
                    self._config.a_req, self._config.b_req)
                percentiles_table.add_content([
                    inp.test_db.get_db_num_records_str(),
                    inp.test_db.get_db_record_size_str(), selection_cols,
                    query_cat, len(all_met)])
        self._outp["query_percentiles_table"] = percentiles_table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_query_percentiles_table()
