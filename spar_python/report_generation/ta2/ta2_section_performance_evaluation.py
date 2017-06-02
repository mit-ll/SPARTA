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
import spar_python.report_generation.common.graphing as graphing
import spar_python.report_generation.common.latex_classes as latex_classes

# logging:
LOGGER = logging.getLogger(__file__)

class Ta2EvaluationSection(t2sp.Ta2PerformanceSection):
    """The evaluation section of the TA2 report"""

    def _store_evaluation_latency_graph(self, secparam):
        """Stores the evaluation latency information."""
        caption = "Evaluation Time for %s = %s" % (
            self._config.var_secparam, str(secparam))
        tag = "evaluationlatency" + str(secparam)
        graph_path = self.get_img_path(aux=tag)
        labels = (
            self._config.var_depth + " = circuit depth",
            self._config.var_numbatches + " = number of batches",
            self._config.var_latency + " = evaluation latency")
        fields=[
            (t2s.PARAM_TABLENAME, t2s.PARAM_D),
            (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_W),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_EVALUATIONLATENCY)]
        additional_constraint_list = [
            (t2s.PARAM_TABLENAME, t2s.PARAM_K, secparam),
            (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_TESTTYPE, "RANDOM")]
        (functionstr, rsquared, graphstr) = self._make_3d_info(
            labels=labels, fields=fields, caption=caption, tag=tag,
            graph_path=graph_path,
            function_to_regress=self._config.encryptionlatency_ftr,
            additional_constraint_list=additional_constraint_list)
        self._outp["evaluation_functionstr" + str(secparam)] = functionstr
        self._outp["evaluation_rsquared" + str(secparam)] = rsquared
        self._outp["evaluation_graph" + str(secparam)] = graphstr

    def _store_complex_evaluation_latency_graph(self, secparam):
        """Stores the evaluation latency function information for dependence on
        more than two variables."""
        fields=[
            (t2s.PARAM_TABLENAME, t2s.PARAM_D),
            (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_W),
            (t2s.PARAM_TABLENAME, t2s.PARAM_L),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_EVALUATIONLATENCY)]
        additional_constraint_list = [
            (t2s.PARAM_TABLENAME, t2s.PARAM_K, secparam),
            (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_TESTTYPE, "RANDOM")]
        this_constraint_list = self._config.get_constraint_list(
            fields=fields, require_correct=True,
            usebaseline=False) + additional_constraint_list
        # this weeds out tests with no D defined (single gate type tests):
        this_non_standard_constraint_list = [
            (t2s.PARAM_TABLENAME, t2s.PARAM_D, "%s.%s IS NOT 'None'")]
        [x_values, y_values, z_values,
         w_values] = self._config.results_db.get_values(
            fields, constraint_list=this_constraint_list,
            non_standard_constraint_list=this_non_standard_constraint_list)
        function_to_regress = self._config.complexevallatency_ftr
        try:
            function = regression.regress(
                function_to_regress=function_to_regress,
                outputs=w_values, inputs=[x_values, y_values, z_values])
            functionstr = function.string
            rsquared = function.get_rsquared(
                inputs=[x_values, y_values, z_values], outputs=w_values)
        except (regression.BadRegressionInputError, TypeError):
            functionstr = None
            rsquared = None
        self._outp[
            "evaluation_complexfunctionstr" + str(secparam)] = functionstr
        self._outp["evaluation_complexrsquared" + str(secparam)] = rsquared

    def _store_ciphertextsize_table_and_graph(self):
        """Stores the ciphertext size information."""
        caption = "Evaluated Ciphertext Sizes"
        tag = "evaluatedciphertextsizes"
        graph_path = self.get_img_path(aux=tag)
        # make the table:
        fields = [(t2s.PEREVALUATION_TABLENAME,
                   t2s.PEREVALUATION_OUTPUTSIZE)]
        unique_ls = self._config.results_db.get_unique_values(
            fields=[(t2s.PARAM_TABLENAME, t2s.PARAM_L)])
        ciphertext_sizes_list = []
        constraint_list = self._config.get_constraint_list(
            fields=fields, require_correct=True, usebaseline=False)
        for l in unique_ls:
            [ciphertextsizes] = self._config.results_db.get_values(
                fields=fields,
                constraint_list=constraint_list + [
                    (t2s.PARAM_TABLENAME, t2s.PARAM_L, l)])
            ciphertext_sizes_list.append(ciphertextsizes)
        ciphertextsize_table = self._make_values_table(
            caption=caption, tag=tag,
            values_list=ciphertext_sizes_list,
            header_name=self._config.var_batchsize,
            header_values=unique_ls,
            flip=False)
        self._outp["ciphertextsize_table"] = ciphertextsize_table
        # make the graph:
        inputs = [(self._config.var_batchsize + "=" + str(l),
                   ciphertext_sizes) for (l, ciphertext_sizes)
                  in zip(unique_ls, ciphertext_sizes_list)]
        ciphertextsize_graph = graphing.box_plot("", inputs, y_scale='log')
        self.write(graph_path, ciphertextsize_graph)
        ciphertextsize_latexgraph = latex_classes.LatexImage(
            caption, tag, graph_path, .8)
        self._outp[
            "ciphertextsize_graph"] = ciphertextsize_latexgraph.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        present_secparams = self._config.results_db.get_unique_values(
            fields=[(t2s.PARAM_TABLENAME, t2s.PARAM_K)])
        for secparam in present_secparams:
            self._store_evaluation_latency_graph(secparam)
            self._store_complex_evaluation_latency_graph(secparam)
        self._store_ciphertextsize_table_and_graph()
