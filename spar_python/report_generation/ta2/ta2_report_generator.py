# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA2 report generator
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  21 Oct 2013   SY             Original version
# *****************************************************************

# general imports:
import logging
import os
import functools

# SPAR imports:
import spar_python.report_generation.common.report_generator as report_generator
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.section as section
import spar_python.report_generation.ta2.ta2_section_correctness as t2sc
import spar_python.report_generation.ta2.ta2_section_performance_totalelapsedtime as t2sptet
import spar_python.report_generation.ta2.ta2_section_performance_keygen as t2spkg
import spar_python.report_generation.ta2.ta2_section_performance_ingestion as t2spi
import spar_python.report_generation.ta2.ta2_section_performance_encryption as t2spenc
import spar_python.report_generation.ta2.ta2_section_performance_evaluation as t2speval
import spar_python.report_generation.ta2.ta2_section_performance_decryption as t2spd
import spar_python.report_generation.ta2.ta2_section_performance_singlegatetype as t2spsgt
import spar_python.report_generation.ta2.ta2_section_system_utilization as t2su
# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta2ReportGenerator(report_generator.ReportGenerator):
    """A TA2 report generator.
    This class creates all the necessary section objects, and combines their
    outputs to create the full report.

    Attributes:
        config: a configuration object
        jinja_env: a jinja environment
    """
    def __init__(self, config, jinja_env):
        """Initializes the report generator with a configuration object and
        a jinja environment."""
        super(Ta2ReportGenerator, self).__init__(config, jinja_env)
        # the following dictionary maps each section name to the name of the
        # corresponding template and the class which is responsible for
        # populating it:
        self._section_name_to_template_name_and_class = {
            "ta2_other_sections": ("ta2_other_sections.txt", section.Section),
            "ta2_correctness": ("ta2_correctness.txt",
                                t2sc.Ta2CorrectnessSection),
            "ta2_performance": ("ta2_performance.txt", section.Section),
            "ta2_performance_totalelapsedtime": (
                "ta2_performance_totalelapsedtime.txt",
                t2sptet.Ta2TotalElapsedTimeSection),
            "ta2_performance_keygen": ("ta2_performance_keygen.txt",
                                       t2spkg.Ta2KeygenSection),
            "ta2_performance_ingestion": ("ta2_performance_ingestion.txt",
                                          t2spi.Ta2IngestionSection),
            "ta2_performance_encryption": ("ta2_performance_encryption.txt",
                                           t2spenc.Ta2EncryptionSection),
            "ta2_performance_evaluation": ("ta2_performance_evaluation.txt",
                                           t2speval.Ta2EvaluationSection),
            "ta2_performance_decryption": ("ta2_performance_decryption.txt",
                                           t2spd.Ta2DecryptionSection),
            "ta2_performance_singlegatetype": (
                "ta2_performance_singlegatetype.txt",
                t2spsgt.Ta2SingleGateTypeSection),
           "ta2_system_utilization": ("ta2_system_utilization.txt", t2su.Ta2SystemUtilizationSection)}
                                                   
        # the following is the name of the report template:
        self._report_template_name = "report.txt"
        # the following is to be populated in create_sections:
        self._sections = []
        # perform all of the pre-processing:
        self._populate_ground_truth()

    def _populate_ground_truth(self):
        """Populates the ground truth with the baseline outputs."""
        fields = [(t2s.INPUT_TABLENAME, t2s.INPUT_IID),
                  (t2s.INPUT_TABLENAME, t2s.INPUT_CORRECTOUTPUT),
                  (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_OUTPUT),
                  (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_CORRECTNESS),
                  (t2s.PEREVALUATION_TABLENAME, "ROWID")]
        baseline_constraint_list = self.config.get_constraint_list(
            fields=fields, require_correct=False, usebaseline=True)
        baseline_values = self.config.results_db.get_values(
            fields=fields,
            constraint_list=baseline_constraint_list)
        for (inputid, correctoutput, baselineoutput, stored_correctness,
             evaluationid) in zip(*baseline_values):
            # all baseline evaluations are assumed to be correct:
            if correctoutput != baselineoutput:
                self.config.results_db.update(
                    t2s.INPUT_TABLENAME, t2s.INPUT_CORRECTOUTPUT, baselineoutput,
                    constraint_list=[(t2s.INPUT_TABLENAME, t2s.INPUT_IID,
                                      inputid)])
            if not stored_correctness:
                self.config.results_db.update(
                    t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_CORRECTNESS,
                    True, constraint_list=[
                        (t2s.PEREVALUATION_TABLENAME, "ROWID", evaluationid)])
        performer_constraint_list = self.config.get_constraint_list(
            fields=fields, require_correct=False, usebaseline=False)
        performer_values = self.config.results_db.get_values(
            fields=fields, constraint_list=performer_constraint_list)
        for (inputid, correctoutput, output, stored_correctness,
             evaluationid) in zip(*performer_values):
            correctness = correctoutput == output
            if stored_correctness != correctness:
                self.config.results_db.update(
                    t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_CORRECTNESS,
                    correctness,
                    constraint_list=[(t2s.PEREVALUATION_TABLENAME,
                                      "ROWID", evaluationid)])
