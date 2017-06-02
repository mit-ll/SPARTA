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
import spar_python.report_generation.ta1.ta1_analysis_modifications as t1am

class Ta1ModificationsSection(section.Ta1Section):
    """The modifications section of the TA1 report"""

    def _store_modifications_table(self):
        """Stores the LaTeX string representing the modifications table
        on the output object."""
        
        def add_content(mod_cat):
            """adds a row to the modifications table corresponding to the
            given mod_cat"""
            analysis = modification_getter.get_analysis(mod_cat)
            if analysis.min_correct_rlatencies:
                min_correct_rlatency = str(
                    round(min(analysis.min_correct_rlatencies), 3))
            else:
                min_correct_rlatency = "N/A"
            if analysis.max_wrong_rlatencies:
                max_wrong_rlatency = str(
                    round(max(analysis.max_wrong_rlatencies), 3))
            else:
                max_wrong_rlatency = "N/A"
            modification_table.add_content([
                mod_cat, str(analysis.nummods),
                str(analysis.numfailedmods),
                str(analysis.nummodsbadinfo),
                str(analysis.nummodswrongpostqueries),
                str(analysis.numgoodmods),
                min_correct_rlatency,
                max_wrong_rlatency])
                
        # create the modifications table:
        modification_table = latex_classes.LatexTable(
            "Modifications", "mods",
            ["Type", "\#", "\# failed", "\# bad info", "\# wrong", "\# correct",
             "min good latency", "max bad latency"])
        modification_getter = t1am.ModificationGetter(
            self._report_generator.config)
        for mod_cat in t1s.MOD_CATEGORIES.values_list():
            add_content(mod_cat)
        self._outp["modification_table"] = modification_table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_modifications_table()
