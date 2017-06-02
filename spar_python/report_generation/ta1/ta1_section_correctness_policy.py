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
import spar_python.report_generation.ta1.ta1_analysis_correctness as t1ac

class Ta1PolicyCorrectnessSection(section.Ta1Section):
    """The policy correctness section of the TA1 report"""

    def _store_policy_correctness_table(self):
        """Stores the LaTeX string representing the policy correctness table
        on the output object."""
        # create the correctness table:
        policy_correctness_table = latex_classes.LatexTable(
            "Policy Correctness", "policy_corr",
            ["Precision", "Recall", "Count"])
        # compute the correctness:
        correctness_getter = t1ac.PolicyCorrectnessGetter(
            results_db=self._config.results_db,
            constraint_list=self._config.get_constraint_list(
                require_correct=False))
        policy_correctness_table.add_content(
            [correctness_getter.get_precision(),
             correctness_getter.get_recall(),
             correctness_getter.get_count()])
        self._outp[
            "policy_correctness_table"] = policy_correctness_table.get_string()

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_policy_correctness_table()
