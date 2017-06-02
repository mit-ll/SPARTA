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
#  24 Oct 2013   SY             Original version
# *****************************************************************

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta2.ta2_section_performance as t2sp
import spar_python.report_generation.ta2.ta2_schema as t2s

# logging:
LOGGER = logging.getLogger(__file__)

class Ta2IngestionSection(t2sp.Ta2PerformanceSection):
    """The ingestion section of the TA2 report"""

    def _store_ingestion_latency_table(self):
        """Stores the circuit ingestion latency information."""
        caption = "Circuit Ingestion Latency"
        tag = "ingestionlatency"
        fields = [(t2s.PERINGESTION_TABLENAME, t2s.PERINGESTION_LATENCY)]
        ingestion_latency_values = self._config.results_db.get_values(
            fields=fields,
            constraint_list=self._config.get_constraint_list(
                fields=fields, require_correct=True, usebaseline=False,
                require_random=True))
        ingestion_table = self._make_values_table(
            caption=caption, tag=tag, values_list=ingestion_latency_values)
        self._outp["ingestion_table"] = ingestion_table

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_ingestion_latency_table()
        
    
