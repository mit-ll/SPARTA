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

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta1.ta1_section_overview as t1so
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_config as config
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.common.graphing as graphing
import spar_python.report_generation.common.latex_classes as latex_classes

# logging:
LOGGER = logging.getLogger(__file__)

class Ta1OverviewCommonSection(t1so.Ta1OverviewSection):
    """The superclass of all of the query type specific overview sections of
    the TA1 report"""

    def __init__(self, jinja_template, report_generator, cat, subcat=None):
        """Initializes the section with a jinja template, a report generator,
        and a query category."""
        super(Ta1OverviewCommonSection, self).__init__(
            jinja_template, report_generator)
        # create the input object for this section:
        self._inp["cat_number"] = cat
        self._inp[t1s.DBF_CAT] = t1s.CATEGORIES.to_string(cat)
        if subcat != None:
            self._inp[t1s.DBF_SUBCAT] = t1s.SUBCATEGORIES[cat].to_string(subcat)
            self._inp["subcat_number"] = subcat
        # populate the output object:
        self._outp["main_database_name"] = self._inp.test_db.get_short_database_name(
            lower=True)
        self._outp["query_cat"] = self._inp[t1s.DBF_CAT]
        self._outp["query_cat_name"] = t1s.CATEGORY_NAMES[
            self._inp["cat_number"]]
        if subcat != None:
            self._outp["query_subcat"] = self._inp[t1s.DBF_SUBCAT]
            if (cat, subcat) in t1s.CATEGORY_AND_SUBCATEGORY_NAMES:
                self._outp["query_name"] = t1s.CATEGORY_AND_SUBCATEGORY_NAMES[
                    (cat, subcat)]
        # do not include this section if there is no data present for the
        # category/subcategory in question:
        simple_fields = [(t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)]
        constraint_list = self._config.get_constraint_list(
                ) + self._inp.get_constraint_list()
        self._has_content = True
        unique_lat_values = self._config.results_db.get_unique_query_values(
            simple_fields=simple_fields,
            constraint_list=constraint_list)
        if not unique_lat_values:
            self._has_content = False

    def _store_common_correctness_info(self):
        """Stores all of the correctness info that each overview section has
        on the output object."""
        correctness_getter = self._report_generator.get_correctness_getter(
            cat=self._inp["cat_number"], dbnr=self._inp[t1s.DBF_NUMRECORDS],
            dbrs=self._inp[t1s.DBF_RECORDSIZE])
        self._outp["num_queries"] = correctness_getter.get_count()
        self._outp["recall"] = correctness_getter.get_recall()
        self._outp["precision"] = correctness_getter.get_precision()
        self._outp["badhash_fraction"] = correctness_getter.get_badhash_fraction()

    def _store_common_latency_graph(
        self, simple_fields=None,
        label_template=None):
        """Stores a graph of latency against number of records returned on the
        output object."""
        if not simple_fields:
            # set the simple_fields (which the categories will be based on) to
            # the default value:
            simple_fields = [(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
                             (t1s.DBF_TABLENAME, t1s.DBF_CAT),
                             (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT)]
            def get_label(category):
                (selectioncols, cat, subcat) = category
                label = "select %s %s" % (selectioncols, cat)
                if subcat:
                    label += "-%s" % subcat
                return label
        else:
            def get_label(category):
                return label_template % category
        # find all of the naming and reference strings:
        caption = "Type %s Queries (%s)" % (
            self._inp[t1s.DBF_CAT],
            self._inp.test_db.get_short_database_name())
        tag = self.get_tag(self._inp)
        graph_path = self.get_img_path(self._inp)
        # find the data and create the graph:
        constraint_list = (
            self._config.get_constraint_list() +
            self._inp.get_constraint_list())
        categories = self._config.results_db.get_unique_query_values(
            simple_fields=simple_fields, constraint_list=constraint_list)
        (x_label, y_label) = (
            self._config.var_nummatches + " = # new matching records",
            self._config.var_ql + " = query latency (s)")
        datasets = []
        for category in categories:
            # make the data label
            data_label = get_label(category)
            # get the data:
            auxiliary_constraint_list = [
                (table, field, val) for ((table, field), val) in zip(
                    simple_fields, category)]
            this_constraint_list = constraint_list + auxiliary_constraint_list
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
            except regression.BadRegressionInputError:
                function = None
            datasets.append(
                (x_values, y_values, data_label, function))
        if categories:
            graph = graphing.graph2d(
                plot_name="", datasets=datasets,
                x_label=x_label, y_label=y_label)
            self.write(graph_path, graph)
            graph_image = latex_classes.LatexImage(caption, tag, graph_path)
            self._outp["common_latency_graph"] = graph_image.get_string()

    def _get_parameters(self, selection_cols):
        """Returns parameters for the 3d graph."""
        assert False, "should be extended by subclasses"

    def _store_3d_latency_graph(self, selection_cols):
        """Stores the latency as a function of number of records returned and
        one other parameter, and its auxiliary information like rsquared value
        and function."""
        assert selection_cols in ["id", "*"], (
            "invalid selection cols %s" % selection_cols)
        parameters = self._get_parameters(selection_cols)
        # because python cannot handle attribute names containing "*", we must
        # map * to something else:
        selection_cols_attr_string = selection_cols
        if selection_cols == "*":
            selection_cols_attr_string = "star"
        # find all of the naming and reference strings:
        cat_name = self._inp[t1s.DBF_CAT]
        if self._inp.get(t1s.DBF_SUBCAT) != None:
            cat_name = self._inp[t1s.DBF_CAT] + "-" + self._inp[t1s.DBF_SUBCAT]
        caption = "Type %s SELECT %s Queries (%s)" % (
            cat_name, selection_cols,
            self._inp.test_db.get_short_database_name())
        tag = self.get_tag(inp=self._inp, aux=selection_cols_attr_string)
        graph_path = self.get_img_path(inp=self._inp,
                                       aux=selection_cols_attr_string)
        # find the data and create the graphs, etc:
        (x_label, y_label, z_label) = (
            self._config.var_nummatches + " = # new matching records",
            self._config.var_ql + " = query latency (s)",
            parameters["z_label"])
        [x_values, y_values, z_values] = parameters["values"]
        try:
            function = regression.regress(
                function_to_regress=parameters["ftr"],
                outputs=z_values, inputs=[x_values, y_values])
            functionstr = function.string
            rsquared = function.get_rsquared(inputs=[x_values, y_values],
                                             outputs=z_values)
        except regression.BadRegressionInputError:
            function = None
            functionstr = None
            rsquared = None
        try:
            graph = graphing.graph3d(
                "", x_values, y_values, z_values,
                x_label, y_label, z_label,
                best_fit_function=function)
            self.write(graph_path, graph)
            graphimage = latex_classes.LatexImage(caption, tag, graph_path)
            graphstr = graphimage.get_string()
        except:
            graphstr = None
        for (suffix, value) in [("functionstr", functionstr),
                                ("rsquared", rsquared),
                                ("graph", graphstr)]:
            self._outp[selection_cols_attr_string + "_" + suffix] = value

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        super(Ta1OverviewCommonSection, self)._populate_output()
        self._store_common_correctness_info()
        self._store_common_latency_graph()

    def should_be_included(self):
        """Returns True if there are queries of the category associated with
        this section, and False otherwise."""
        return self._has_content
        
    
