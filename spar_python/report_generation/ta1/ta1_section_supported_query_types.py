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

class Ta1SupportedQueryTypesSection(section.Ta1Section):
    """The supported query types section of the TA1 report"""

    def _store_atomic_queries_table(self):
        """Stores the LaTeX string representing the supported queries table
        on the output object."""
        fieldtypes = t1s.TEST_FIELD_TYPES.numbers_list()
        fieldtype_strings = [t1s.TEST_FIELD_TYPES.to_string(ft)
                              for ft in fieldtypes]
        categories = [] # a list of atomic (cat, subcat) tuples
        for cat in t1s.ATOMIC_CATEGORIES:
            if cat in t1s.SUBCATEGORIES.keys():
                for subcat in t1s.SUBCATEGORIES[cat].numbers_list():
                    categories.append((cat, subcat))
            else:
                categories.append((cat, None))
        table = latex_classes.LatexTable(
            "Supported Query Types", "supported_query_types",
            ["Query Type", "Subtype"] + [
                "on " + fts for fts in fieldtype_strings])
        for (cat, subcat) in categories:
            cat_string = t1s.CATEGORIES.to_string(cat)
            if subcat != None:
                subcat_string = t1s.SUBCATEGORIES[cat].to_string(subcat)
            else:
                subcat_string = ""
            row = [cat_string, subcat_string]
            for fieldtype in fieldtypes:
                if fieldtype not in t1s.CATEGORY_TO_FIELDS[cat]:
                    status = "N/A"
                else:
                    correctness_getter = self._report_generator.get_correctness_getter(
                        cat=cat, subcat=subcat, fieldtype=fieldtype)
                    if correctness_getter.get_count() == 0:
                        status = "-"
                    elif correctness_getter.get_num_correct() > 0:
                        status = "pass"
                    else:
                        status = "fail"
                row.append(status)
            table.add_content(row)
        self._outp["atomic_queries_table"] = table.get_string()
        
    def _store_composite_queries_table(self):
        """Stores the LaTeX string representing the supported composite queries
        table on the output object."""
        # the list of all composite categories:
        categories = sum(
            [[(cat, subcat) for subcat in t1s.SUBCATEGORIES[cat].numbers_list()]
             for cat in t1s.CATEGORIES.numbers_list()
             if cat not in t1s.ATOMIC_CATEGORIES], [])
        present_categories = [
            (cat, subcat) for (cat, subcat) in categories
            if (cat, subcat)
            in self._report_generator.get_present_cats(
                subsubcat=False, dbnr=False, dbrs=False)]
        table = latex_classes.LatexTable(
            "Supported Query Types", "supported_query_types",
            ["Query Type", "Subtype", "Supported Atomic Sub-Query Types"])
        for (cat, subcat) in present_categories:
            cat_string = t1s.CATEGORIES.to_string(cat)
            if subcat != None:
                subcat_string = t1s.SUBCATEGORIES[cat].to_string(subcat)
            else:
                subcat_string = ""
            # the following is a function so that later, if we choose to add
            # composite sub-query reporting here, it will be simpler:
            def get_sub_query_types():
                """returns a string represenging the sub-query types."""
                sub_query_types = self._config.results_db.get_unique_query_values(
                    atomic_fields_and_functions=[
                        (t1s.DBA_CAT, t1s.Ta1ResultsSchema().get_complex_function(
                            t1s.DBA_TABLENAME, t1s.DBA_CAT, is_list=True))],
                    constraint_list=self._config.get_constraint_list() + [
                        (t1s.DBF_TABLENAME, t1s.DBF_CAT, cat_string),
                        (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT, subcat_string)])
                sub_query_types = list(set(sum(sub_query_types, ())))
                sub_query_types_string = ",".join(sub_query_types)
                return sub_query_types_string
            atomic_sub_query_types_string = get_sub_query_types()
            #full_sub_query_types_string = get_sub_query_types(full=True)
            table.add_content([cat_string, subcat_string,
                               atomic_sub_query_types_string])
        self._outp["composite_queries_table"] = table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_atomic_queries_table()
        self._store_composite_queries_table()
