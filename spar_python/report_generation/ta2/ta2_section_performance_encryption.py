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
from __future__ import division

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta2.ta2_section_performance as t2sp
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.graphing as graphing
import spar_python.report_generation.common.latex_classes as latex_classes

# logging:
LOGGER = logging.getLogger(__file__)

class Ta2EncryptionSection(t2sp.Ta2PerformanceSection):
    """The encryption section of the TA2 report"""

    def _store_encryption_latency_graph(self):
        """Stores the encryption latency information."""
        caption = "Encryption Time"
        tag = "encryptionlatency"
        graph_path = self.get_img_path(aux=tag)
        labels = (
            self._config.var_depth + " = circuit depth",
            self._config.var_numbatches + " = number of batches",
            self._config.var_latency + " = encryption latency")
        fields=[
            (t2s.PARAM_TABLENAME, t2s.PARAM_D),
            (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_W),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_ENCRYPTIONLATENCY)]
        (functionstr, rsquared, graphstr) = self._make_3d_info(
            labels=labels, fields=fields, caption=caption, tag=tag,
            graph_path=graph_path,
            function_to_regress=self._config.encryptionlatency_ftr)
        self._outp["encryption_functionstr"] = functionstr
        self._outp["encryption_rsquared"] = rsquared
        self._outp["encryption_graph"] = graphstr

    def _store_ciphertextsize_table_and_graph(self):
        """Stores the ciphertext size information."""
        caption = "Fresh Ciphertext Sizes"
        tag = "freshciphertextsizes"
        graph_path = self.get_img_path(aux=tag)
        # make the table:
        fields = [(t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_W),
                  (t2s.PEREVALUATION_TABLENAME,
                   t2s.PEREVALUATION_INPUTSIZE)]
        unique_ls = self._config.results_db.get_unique_values(
            fields=[(t2s.PARAM_TABLENAME, t2s.PARAM_L)])
        adjusted_ciphertext_sizes_list = []
        constraint_list = self._config.get_constraint_list(
            fields=fields, require_correct=True, usebaseline=False)
        for l in unique_ls:
            [ws, ciphertextsizes] = self._config.results_db.get_values(
                fields=fields,
                constraint_list=constraint_list + [
                    (t2s.PARAM_TABLENAME, t2s.PARAM_L, l)])
            adjusted_ciphertext_sizes = [
                ciphertextsize / w
                for (w, ciphertextsize) in zip(ws, ciphertextsizes)]
            adjusted_ciphertext_sizes_list.append(adjusted_ciphertext_sizes)
        ciphertextsize_table = self._make_values_table(
            caption=caption, tag=tag,
            values_list=adjusted_ciphertext_sizes_list,
            header_name=self._config.var_batchsize,
            header_values=unique_ls,
            flip=False)
        self._outp["ciphertextsize_table"] = ciphertextsize_table
        # make the graph:
        inputs = [(self._config.var_batchsize + "=" + str(l),
                   adjusted_ciphertext_sizes) for (l, adjusted_ciphertext_sizes)
                  in zip(unique_ls, adjusted_ciphertext_sizes_list)]
        ciphertextsize_graph = graphing.box_plot("", inputs, y_scale='log')
        self.write(graph_path, ciphertextsize_graph)
        ciphertextsize_latexgraph = latex_classes.LatexImage(
            caption, tag, graph_path, .8)
        self._outp[
            "ciphertextsize_graph"] = ciphertextsize_latexgraph.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_encryption_latency_graph()
        self._store_ciphertextsize_table_and_graph()
    
