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

# logging:
LOGGER = logging.getLogger(__file__)

class Ta2KeygenSection(t2sp.Ta2PerformanceSection):
    """The key generation section of the TA2 report"""

    def _store_keygen_latency_graph(self):
        """Stores the key generation latency information."""
        caption = "Key Generation Time"
        tag = "keygenlatency"
        graph_path = self.get_img_path(aux=tag)
        labels = (
            self._config.var_depth + " = circuit depth",
            self._config.var_batchsize + " = batch size",
            self._config.var_latency + " = key generation latency")
        fields=[
            (t2s.PARAM_TABLENAME, t2s.PARAM_D),
            (t2s.PARAM_TABLENAME, t2s.PARAM_L),
            (t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_LATENCY)]
        (functionstr, rsquared, graphstr) = self._make_3d_info(
            labels=labels, fields=fields, caption=caption, tag=tag,
            graph_path=graph_path,
            function_to_regress=self._config.keygenlatency_ftr)
        self._outp["keygen_functionstr"] = functionstr
        self._outp["keygen_rsquared"] = rsquared
        self._outp["keygen_graph"] = graphstr

    def _store_keysize_table(self):
        """Stores the key size information."""
        caption = "Key Sizes"
        tag = "keysizes"
        fields = [(t2s.PERKEYGEN_TABLENAME, t2s.PERKEYGEN_KEYSIZE)]
        keysize_values = self._config.results_db.get_values(
            fields=fields,
            constraint_list=self._config.get_constraint_list(
                fields=fields, require_correct=True, usebaseline=False))
        keysize_table = self._make_values_table(
            caption=caption, tag=tag, values_list=keysize_values)
        self._outp["keysize_table"] = keysize_table

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_keygen_latency_graph()
        self._store_keysize_table()
        
    
