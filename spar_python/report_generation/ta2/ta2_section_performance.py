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
import math

# SPAR imports:
import spar_python.report_generation.ta2.ta2_section as section
import spar_python.report_generation.common.latex_classes as latex_classes
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.common.graphing as graphing

class Ta2PerformanceSection(section.Ta2Section):
    """The performance section superclass of the TA2 report"""

    def _make_3d_info(self, labels, fields, caption, tag, graph_path,
                      function_to_regress, additional_constraint_list=None):
        """Makes a 3D graph.
        Args:
            labels: a list of the form (x_label, y_label, z_label)
            fields: a list of the form [(table1, field1), (table2, field2),
                (table3, field3)].
            caption: a caption string
            tag: a tag string
            graph_path: a path indicating the location where the graph is to be
                stored.
            function_to_regress: a FunctionToRegress object

        Returns:
            A tuple of the form (functionstr, rsquared, graphstr).
        """
        # find the data and create the graphs, etc:
        assert len(labels) == 3
        (x_label, y_label, z_label) = labels
        assert len(fields) == 3
        if not additional_constraint_list:
            additional_constraint_list = []
        this_constraint_list = self._config.get_constraint_list(
            fields=fields, require_correct=True,
            usebaseline=False) + additional_constraint_list
        # this weeds out tests with no D defined (single gate type tests):
        this_non_standard_constraint_list = [
            (t2s.PARAM_TABLENAME, t2s.PARAM_D, "%s.%s IS NOT 'None'")]
        [x_values, y_values, z_values] = self._config.results_db.get_values(
            fields, constraint_list=this_constraint_list,
            non_standard_constraint_list=this_non_standard_constraint_list)
        try:
            function = regression.regress(
                function_to_regress=function_to_regress,
                outputs=z_values, inputs=[x_values, y_values])
            functionstr = function.string
            rsquared = function.get_rsquared(inputs=[x_values, y_values],
                                             outputs=z_values)
        except (regression.BadRegressionInputError, TypeError):
            function = None
            functionstr = None
            rsquared = None
        try:
            graph = graphing.graph3d(
                "", x_values, y_values, z_values,
                x_label, y_label, z_label,
                best_fit_function=function)
            self.write(graph_path, graph)
            graphimage = latex_classes.LatexImage(caption, tag, graph_path, .8)
            graphstr = graphimage.get_string()
        except graphing.BadGraphingInputs:
            graphstr = None
        return (functionstr, rsquared, graphstr)

    def _make_values_table(self, caption, tag, values_list,
                           header_name = None,
                           header_values = None,
                           flip=True,
                           numsigfigs=None):
        """Makes a table describing the values given, by providing the mean,
        standard deviation, minimum, maximum, and count.
        """
        if numsigfigs == None:
            numsigfigs = self._config.numsigfigs
        header = ["Count", "Mean", "Std Dev", "Min", "Max"]
        if header_name:
            header = [header_name] + header
            if not header_values:
                header_values = range(1, len(values_list) + 1)
        else:
            header_values = [None for idx in xrange(len(values_list))]
        table = latex_classes.LatexCleanTable(
            caption, tag, header, flip)
        for (header_value, values) in zip(header_values, values_list):
            count = len(values)
            if count > 0:
                mean = float(sum(values)) / float(count)
                variance = float(
                    sum([(elt - mean)**2 for elt in values])) / float(count)
                std_dev = math.sqrt(variance)
                minimum = min(values)
                maximum = max(values)
                column = [count,
                          round(mean, numsigfigs),
                          round(std_dev, numsigfigs),
                          round(minimum, numsigfigs),
                          round(maximum, numsigfigs)]
            else:
                column = [count] + ["N/A"] * 4
            if header_name:
                column = [header_value] + column
            table.add_content(column)
        return table.get_string()
                                         
