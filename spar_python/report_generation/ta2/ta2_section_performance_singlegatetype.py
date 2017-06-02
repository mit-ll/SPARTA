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

class Ta2SingleGateTypeSection(t2sp.Ta2PerformanceSection):
    """The single gate type section of the TA2 report"""

    def _store_singlegatetype_chart(self):
        """Stores the total elapsed time information."""
        caption = "Time Per Gate"
        tag = "singlegatetype"
        values_list = []
        header_name = "Gate Type"
        header_values = []
        these_fields = [(t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_TESTTYPE)]
        this_constraint_list = self._config.get_constraint_list(
            fields=these_fields, require_correct=True, usebaseline=False)
        present_test_types = self._config.results_db.get_unique_values(
            fields=these_fields,
            constraint_list=this_constraint_list)
        for test_type in present_test_types:
            if test_type == "RANDOM":
                # all test types other than RANDOM represent a single-gate-type
                # test
                continue
            header_values.append(test_type)
            this_test_type_fields = [
                (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_NUMGATES),
                (t2s.PEREVALUATION_TABLENAME,
                 t2s.PEREVALUATION_EVALUATIONLATENCY)]
            this_test_type_constraint_list = self._config.get_constraint_list(
                fields=this_test_type_fields,
                require_correct=True, usebaseline=False) + [
                (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_TESTTYPE, test_type)]
            [num_gates, latencies] = self._config.results_db.get_values(
                fields=this_test_type_fields,
                constraint_list=this_test_type_constraint_list)
            values = [latency / float(ng) for (ng, latency)
                      in zip(num_gates, latencies)]
            values_list.append(values)
        table_string = self._make_values_table(caption, tag, values_list,
                                               header_name, header_values,
                                               flip=False, numsigfigs=6)
        self._outp["singlegatetype_table"] = table_string
        
    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_singlegatetype_chart()        
    
