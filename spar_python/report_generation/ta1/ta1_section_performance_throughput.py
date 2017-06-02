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
from __future__ import division

# SPAR imports:
import spar_python.report_generation.ta1.ta1_section as section
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.common.latex_classes as latex_classes
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai

class Ta1ThroughputSection(section.Ta1Section):
    """The throughput section of the TA1 report"""

    def _store_query_throughput_table(self):
        """Stores the LaTeX string representing the query throughput table
        on the output object."""
        constraint_list = self._config.get_constraint_list(throughput=True)
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=[(t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS),
                           (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE),
                           (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
                           (t1s.DBF_TABLENAME, t1s.DBF_CAT),
                           (t1s.DBP_TABLENAME, t1s.DBP_TESTCASEID)],
            constraint_list=constraint_list)
        # create the latency table:
        throughput_table = latex_classes.LatexTable(
            "Query Throughputs",
            "thru_main",
            ["DBNR", "DBRS", "Select", "Query Type",
             "testcase", "count", "throughput"])
        # compute correctness for every query category:
        for (dbnr, dbrs, selection_cols, query_cat, tcid) in categories:
            inp = t1ai.Input()
            inp[t1s.DBF_CAT] = query_cat
            inp[t1s.DBF_NUMRECORDS] = dbnr
            inp[t1s.DBF_RECORDSIZE] = dbrs
            inp[t1s.DBP_SELECTIONCOLS] = selection_cols
            this_constraint_list = constraint_list + inp.get_constraint_list() + [
                (t1s.DBP_TABLENAME, t1s.DBP_TESTCASEID, tcid)]
            [starttimes, endtimes] = self._config.results_db.get_query_values(
                simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SENDTIME),
                               (t1s.DBP_TABLENAME, t1s.DBP_RESULTSTIME)],
                constraint_list=this_constraint_list)
            numqueries = len(starttimes)
            assert len(endtimes) == numqueries
            starttime = min(starttimes)
            endtime = max(endtimes)
            duration = endtime - starttime
            if numqueries > 0:
                throughput = numqueries / duration
                throughput_table.add_content(
                    [inp.test_db.get_db_num_records_str(),
                     inp.test_db.get_db_record_size_str(),
                     selection_cols, query_cat,
                     tcid, str(numqueries), str(round(throughput, 3))])
        self._outp["query_throughput_table"] = throughput_table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_query_throughput_table()
