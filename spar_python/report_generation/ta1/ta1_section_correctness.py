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
import spar_python.report_generation.common.latex_classes as latex_classes
import spar_python.report_generation.ta1.ta1_schema as t1s

class Ta1CorrectnessSection(section.Ta1Section):
    """The correctness section of the TA1 report"""

    def _store_query_correctness_table(self):
        """Stores the LaTeX string representing the query correctness table
        on the output object."""
        def add_content(table, cat_string, subcat_string, correctness_getter):
            """adds a row to the given correctness table"""
            table.add_content([
                cat_string, subcat_string,
                str(correctness_getter.get_precision()),
                str(correctness_getter.get_recall()),
                str(correctness_getter.get_badhash_fraction()),
                str(correctness_getter.get_num_bad_rankings()),
                str(correctness_getter.get_count())])
        # create the correctness table:
        query_correctness_table = latex_classes.LatexTable(
            "Query Correctness", "query_corr",
            ["Type", "Subtype",
             "Precision", "Recall", "bcf",
             "nbr", "Count"])
        # compute overall correctness:
        correctness_getter = self._report_generator.get_correctness_getter()
        add_content(query_correctness_table, "All", "", correctness_getter)
        # compute correctness for every query category:
        present_cats = self._report_generator.get_present_cats(
            cat=True, subcat=True, subsubcat=False, dbnr=False, dbrs=False)
        for (cat, subcat) in present_cats:
            cat_string = t1s.CATEGORIES.to_string(cat)
            if subcat != None:
                subcat_string = t1s.SUBCATEGORIES[cat].to_string(subcat)
            else:
                subcat_string = ""
            correctness_getter = self._report_generator.get_correctness_getter(
                cat=cat, subcat=subcat)
            add_content(query_correctness_table, cat_string, subcat_string,
                    correctness_getter)
        self._outp[
            "query_correctness_table"] = query_correctness_table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_query_correctness_table()
