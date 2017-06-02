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
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai

class Ta1LatencySection(section.Ta1Section):
    """The latency section of the TA1 report"""

    def _store_query_latency_table(self):
        """Stores the LaTeX string representing the query latency table
        on the output object."""
        constraint_list = self._config.get_constraint_list(
            require_correct=True)
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS),
                           (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE),
                           (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
                           (t1s.DBF_TABLENAME, t1s.DBF_CAT)],
            constraint_list=constraint_list)
        # create the latency table:
        latency_table = latex_classes.LatexTable(
            "Query Latency vs. Number of Records Returned Best Fit Functions",
            "lat_main",
            ["DBNR", "DBRS", "Select", "Query Type",
             "Best-Fit Func", "R-Squared"])
        # compute correctness for every query category:
        for (dbnr, dbrs, selection_cols, query_cat) in categories:
            inp = t1ai.Input()
            inp[t1s.DBF_CAT] = query_cat
            inp[t1s.DBF_NUMRECORDS] = dbnr
            inp[t1s.DBF_RECORDSIZE] = dbrs
            inp[t1s.DBP_SELECTIONCOLS] = selection_cols
            this_constraint_list = constraint_list + inp.get_constraint_list()
            [x_values, y_values] = self._config.results_db.get_query_values(
                simple_fields=[
                    (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS),
                    (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)],
                constraint_list=this_constraint_list)
            try:
                inputs = [x_values]
                outputs = y_values
                function = regression.regress(
                    function_to_regress=self._config.ql_all_ftr,
                    outputs=outputs, inputs=inputs)
                function_string = function.string
                rsquared = function.get_rsquared(inputs, outputs)
            except regression.BadRegressionInputError:
                function_string = "-"
                rsquared = "-"
            latency_table.add_content(
                [inp.test_db.get_db_num_records_str(),
                 inp.test_db.get_db_record_size_str(),
                 selection_cols, query_cat, function_string, rsquared])
        self._outp["query_latency_table"] = latency_table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_query_latency_table()
