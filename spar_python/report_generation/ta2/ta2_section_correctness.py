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


# SPAR imports:
import spar_python.report_generation.ta2.ta2_section as section
import spar_python.report_generation.common.latex_classes as latex_classes
import spar_python.report_generation.ta2.ta2_analysis_correctness as t2ac
import spar_python.report_generation.ta2.ta2_schema as t2s

class Ta2CorrectnessSection(section.Ta2Section):
    """The correctness section of the TA2 report"""

    def _store_correctness_table(self):
        """Stores the LaTeX string representing the correctness table
        on the output object."""
        config = self._report_generator.config
        # create the correctness table:
        correctness_table = latex_classes.LatexCleanTable(
            "Correctness", "corr",
            ["Evaluation Accuracy", "Count"],
            flip=True)
        # compute the correctness:
        correctness_getter = t2ac.CircuitCorrectnessGetter(
            results_db=config.results_db,
            constraint_list=[(t2s.PEREVALUATION_TABLENAME,
                              t2s.PEREVALUATION_PERFORMERNAME,
                              config.performername)])
        correctness_table.add_content(
            [correctness_getter.get_evaluation_accuracy(),
             correctness_getter.get_count()])
        self._outp["correctness_table"] = correctness_table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_correctness_table()
