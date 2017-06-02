# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA1 report generator
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Sep 2013   SY             Original version
# *****************************************************************

# general imports:
import logging
import os
import functools

# SPAR imports:
import spar_python.report_generation.common.report_generator as report_generator
import spar_python.report_generation.common.results_schema as results_schema
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_analysis_correctness as correctness
import spar_python.report_generation.common.section as section
import spar_python.report_generation.ta1.ta1_section_correctness_query as t1scq
import spar_python.report_generation.ta1.ta1_section_correctness_policy as t1scp
import spar_python.report_generation.ta1.ta1_section_supported_query_types as t1ssqt
import spar_python.report_generation.ta1.ta1_section_overview as t1so
import spar_python.report_generation.ta1.ta1_section_overview_eq as t1soeq
import spar_python.report_generation.ta1.ta1_section_overview_common as t1soc
import spar_python.report_generation.ta1.ta1_section_overview_p1_eqand as t1sop1eqand
import spar_python.report_generation.ta1.ta1_section_overview_p1_eqor as t1sop1eqor
import spar_python.report_generation.ta1.ta1_section_overview_p1_eqdnf as t1sop1eqdnf
import spar_python.report_generation.ta1.ta1_section_overview_p1_proofofconcept as t1sop1poc
import spar_python.report_generation.ta1.ta1_section_overview_p1_otheribm as t1sop1otheribm
import spar_python.report_generation.ta1.ta1_section_overview_p2 as t1sop2
import spar_python.report_generation.ta1.ta1_section_overview_p3p4p6p7 as t1sop3p4p6p7
import spar_python.report_generation.ta1.ta1_section_overview_p8p9_eq as t1sop8p9eq
import spar_python.report_generation.ta1.ta1_section_overview_p8p9_other as t1sop8p9other
import spar_python.report_generation.ta1.ta1_section_performance_latency as t1spl
import spar_python.report_generation.ta1.ta1_section_performance_throughput as t1spt
import spar_python.report_generation.ta1.ta1_section_performance_percentiles as t1spp
import spar_python.report_generation.ta1.ta1_section_performance_percentiles_aux as t1sppa
import spar_python.report_generation.ta1.ta1_section_modifications as t1sm
import spar_python.report_generation.ta1.ta1_section_system_utilization as t1su

# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta1ReportGenerator(report_generator.ReportGenerator):
    """A TA1 report generator.
    This class creates all the necessary section objects, and combines their
    outputs to create the full report.

    Attributes:
        config: a configuration object
        jinja_env: a jinja environment
        present_cats: a list of tuples of the form (cat, subcat), where a tuple
            is present for each combination of query category and subcategory
            that appear in the database.
        correctness_getters: a dictionary mapping tuples of the form
            (cat, subcat) to a corresponding correctness getter object.
    """
    def __init__(self, config, jinja_env):
        """Initializes the report generator with a configuration object and
        a jinja environment."""
        super(Ta1ReportGenerator, self).__init__(config, jinja_env)
        # the following dictionary maps each section name to the name of the
        # corresponding template and the class which is responsible for
        # populating it:
        self._section_name_to_template_name_and_class = {
            "ta1_other_sections": ("ta1_other_sections.txt", section.Section),
            "ta1_correctness": ("ta1_correctness.txt", section.Section),
            "ta1_correctness_query": ("ta1_correctness_query.txt",
                                t1scq.Ta1QueryCorrectnessSection),
            "ta1_correctness_policy": ("ta1_correctness_policy.txt",
                                t1scp.Ta1PolicyCorrectnessSection),
            "ta1_supported_query_types": ("ta1_supported_query_types.txt",
                                          t1ssqt.Ta1SupportedQueryTypesSection),
            "ta1_overview": ("ta1_overview.txt", t1so.Ta1OverviewSection),
            "ta1_overview_eq": ("ta1_overview_eq.txt",
                                t1soeq.Ta1OverviewEqSection),
            "ta1_overview_p1": (
                "ta1_overview_complex.txt",
                functools.partial(t1soc.Ta1OverviewCommonSection,
                                  cat=t1s.CATEGORIES.P1)),
            "ta1_overview_p1_eqand": ("ta1_overview_p1_eqand.txt",
                                      t1sop1eqand.Ta1OverviewP1EqAndSection),
            "ta1_overview_p1_eqor": ("ta1_overview_p1_eqor.txt",
                                      t1sop1eqor.Ta1OverviewP1EqOrSection),
            "ta1_overview_p1_eqdnf": ("ta1_overview_p1_eqdnf.txt",
                                      t1sop1eqdnf.Ta1OverviewP1EqDnfSection),
            "ta1_overview_p1_eqdeep": (
                "ta1_overview_p1_proofofconcept.txt",
                functools.partial(
                    t1sop1poc.Ta1OverviewP1POCSection,
                    subcat=t1s.SUBCATEGORIES[t1s.CATEGORIES.P1].eqdeep)),
            "ta1_overview_p1_eqcnf": (
                "ta1_overview_p1_proofofconcept.txt",
                functools.partial(
                    t1sop1poc.Ta1OverviewP1POCSection,
                    subcat=t1s.SUBCATEGORIES[t1s.CATEGORIES.P1].eqcnf)),
            "ta1_overview_p1_eqnot": (
                "ta1_overview_p1_proofofconcept.txt",
                functools.partial(
                    t1sop1poc.Ta1OverviewP1POCSection,
                    subcat=t1s.SUBCATEGORIES[t1s.CATEGORIES.P1].eqnot)),
            "ta1_overview_p1_otherand": (
                "ta1_overview_p1_proofofconcept.txt",
                functools.partial(
                    t1sop1poc.Ta1OverviewP1POCSection,
                    subcat=t1s.SUBCATEGORIES[t1s.CATEGORIES.P1].otherand)),
            "ta1_overview_p1_otheror": (
                "ta1_overview_p1_proofofconcept.txt",
                functools.partial(
                    t1sop1poc.Ta1OverviewP1POCSection,
                    subcat=t1s.SUBCATEGORIES[t1s.CATEGORIES.P1].otheror)),
            "ta1_overview_p1_otheribm": (
                "ta1_overview_p1_otheribm.txt",
                t1sop1otheribm.Ta1OverviewP1OtherIbmSection),
            "ta1_overview_p2": ("ta1_overview_p2.txt",
                                t1sop2.Ta1OverviewP2Section),
            "ta1_overview_p3": (
                "ta1_overview_p3p4p6p7.txt",
                functools.partial(t1sop3p4p6p7.Ta1OverviewP3P4P6P7Section,
                                  cat=t1s.CATEGORIES.P3)),
            "ta1_overview_p4": (
                "ta1_overview_p3p4p6p7.txt",
                functools.partial(t1sop3p4p6p7.Ta1OverviewP3P4P6P7Section,
                                  cat=t1s.CATEGORIES.P4)),
            "ta1_overview_p6": (
                "ta1_overview_p3p4p6p7.txt",
                functools.partial(t1sop3p4p6p7.Ta1OverviewP3P4P6P7Section,
                                  cat=t1s.CATEGORIES.P6)),
            "ta1_overview_p7": (
                "ta1_overview_p3p4p6p7.txt",
                functools.partial(t1sop3p4p6p7.Ta1OverviewP3P4P6P7Section,
                                  cat=t1s.CATEGORIES.P7)),
            "ta1_overview_p8": (
                "ta1_overview_complex.txt",
                functools.partial(t1soc.Ta1OverviewCommonSection,
                                  cat=t1s.CATEGORIES.P8)),
            "ta1_overview_p8_eq": (
                "ta1_overview_p8p9_eq.txt",
                functools.partial(t1sop8p9eq.Ta1OverviewP8P9EqSection,
                                  cat=t1s.CATEGORIES.P8)),
            "ta1_overview_p8_other": (
                "ta1_overview_p8p9_other.txt",
                functools.partial(t1sop8p9other.Ta1OverviewP8P9OtherSection,
                                  cat=t1s.CATEGORIES.P8)),
            "ta1_overview_p9": (
                "ta1_overview_complex.txt",
                functools.partial(t1soc.Ta1OverviewCommonSection,
                                  cat=t1s.CATEGORIES.P9)),
            "ta1_overview_p9_eq": (
                "ta1_overview_p8p9_eq.txt",
                functools.partial(t1sop8p9eq.Ta1OverviewP8P9EqSection,
                                  cat=t1s.CATEGORIES.P9)),
            "ta1_overview_p9_other": (
                "ta1_overview_p8p9_other.txt",
                functools.partial(t1sop8p9other.Ta1OverviewP8P9OtherSection,
                                  cat=t1s.CATEGORIES.P9)),
            "ta1_overview_p11": ("ta1_overview_common.txt",
                                 functools.partial(t1soc.Ta1OverviewCommonSection,
                                                   cat=t1s.CATEGORIES.P11)),
            "ta1_performance": ("ta1_performance.txt", section.Section),
            "ta1_performance_latency": ("ta1_performance_latency.txt",
                                        t1spl.Ta1LatencySection),
            "ta1_performance_throughput": ("ta1_performance_throughput.txt",
                                           t1spt.Ta1ThroughputSection),
            "ta1_performance_percentiles": ("ta1_performance_percentiles.txt",
                                            t1spp.Ta1PercentilesSection),
            "ta1_performance_percentiles_aux": (
                "ta1_performance_percentiles_aux.txt",
                t1sppa.Ta1PercentilesAuxSection),
            "ta1_modifications": ("ta1_modifications.txt",
                                  t1sm.Ta1ModificationsSection),
            "ta1_system_utilization": ("ta1_system_utilization.txt", t1su.Ta1SystemUtilizationSection)}
        # the following is the name of the report template:
        self._report_template_name = "report.txt"
        # the following are to be populated in discover_querytypes:
        self._present_cats = None
        self._atomic_present_cats = None
        # the following are to be populated in discover_correctness:
        self._correctness_getters = {} # maps (cat, subcat, subsubcat) to a
                                       # correctness getter
        self._atomic_correctness_getters = {} # maps (cat, subcat, subsubcat,
                                              # field) to a correctness_getter
        # the following is to be populated in create_sections:
        self._sections = []
        # perform all of the pre-processing:
        self._check_baseline_correctness()
        self._populate_num_new_matches()
        self._discover_querytypes()
        self._discover_correctness()

    def _populate_num_new_matches(self):
        """Populates the num_cache_hits field"""
        cachehitid = 99
        fields = [
            (t1s.DBP_TABLENAME, "ROWID"),
            (t1s.DBP_TABLENAME, t1s.DBP_EVENTMSGIDS),
            (t1s.DBF_TABLENAME, t1s.DBF_NUMMATCHINGRECORDS),
            (t1s.DBP_TABLENAME, t1s.DBP_NUMNEWRETURNEDRECORDS)]
        constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
             self.config.performername)]
        values = self.config.results_db.get_values(
            fields=fields, constraint_list=constraint_list)
        for (pqid, eventmsgids, nummatchingrecords,
             storednumnewrecords) in zip(*values):
            numcachehits = len([eventmsgid for eventmsgid in eventmsgids
                                if eventmsgid == cachehitid])
            numnewrecords = nummatchingrecords - numcachehits
            if numnewrecords != storednumnewrecords:
                this_constraint_list = constraint_list + [
                    (t1s.DBP_TABLENAME, "ROWID", pqid)]
                self.config.results_db.update(
                    table=t1s.DBP_TABLENAME,
                    field=t1s.DBP_NUMNEWRETURNEDRECORDS,
                    value=numnewrecords,
                    constraint_list=this_constraint_list)

    def _check_baseline_correctness(self):
        """Checks and populates the baseline correctness."""
        baseline_constraint_list = [
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
             self.config.baselinename)]
        baseline_correctness_getter = correctness.QueryCorrectnessGetter(
            self.config.results_db, baseline_constraint_list, update_db=True)
        if not baseline_correctness_getter.is_perfect():
            LOGGER.error("Baseline is not perfectly correct")

    def _discover_querytypes(self):
        """Populates the present_categories and atomic_present_categories
        attributes."""
        constraint_list = [(t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
                            self.config.performername)]
        simple_fields = [(t1s.DBF_TABLENAME, t1s.DBF_CAT),
                         (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT),
                         (t1s.DBF_TABLENAME, t1s.DBF_SUBSUBCAT),
                         (t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS),
                         (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE)]
        present_cat_strings = self.config.results_db.get_unique_query_values(
            simple_fields=simple_fields,
            constraint_list=constraint_list)
        self.present_cats = []
        self.atomic_present_cats = []
        for (cat_str, subcat_str, subsubcat_str,
             dbnr, dbrs) in present_cat_strings:
            cat = t1s.CATEGORIES.value_to_number[cat_str]
            if subcat_str:
                subcat = t1s.SUBCATEGORIES[cat].value_to_number[subcat_str]
            else:
                subcat = None
            if subsubcat_str:
                subsubcat = int(subsubcat_str)
            else:
                subsubcat = None
            self.present_cats.append((cat, subcat, subsubcat, dbnr, dbrs))
            if cat in t1s.ATOMIC_CATEGORIES:
                these_atomic_fields_and_functions = [
                    (t1s.DBA_FIELDTYPE,
                     t1s.Ta1ResultsSchema().get_complex_function(
                        t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE))]
                this_constraint_list = constraint_list + [
                    (t1s.DBF_TABLENAME, t1s.DBF_CAT, cat_str),
                    (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT, subcat_str),
                    (t1s.DBF_TABLENAME, t1s.DBF_SUBSUBCAT, subsubcat_str),
                    (t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS, dbnr),
                    (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE, dbrs)]
                present_fieldtype_strings = self.config.results_db.get_unique_query_values(
                    atomic_fields_and_functions=these_atomic_fields_and_functions,
                    constraint_list=this_constraint_list)
                for fieldtype_str in present_fieldtype_strings:
                    fieldtype = t1s.TEST_FIELD_TYPES.value_to_number[
                        fieldtype_str]
                    self.atomic_present_cats.append(
                        (cat, subcat, subsubcat, dbnr, dbrs, fieldtype))

    def _discover_correctness(self):
        """Populates the correctness_getters attribute."""
        for (cat, subcat, subsubcat, dbnr, dbrs) in self.present_cats:
            cat_string = t1s.CATEGORIES.to_string(cat)
            if subcat not in results_schema.NULL_VALUES:
                subcat_string = t1s.SUBCATEGORIES[cat].to_string(subcat)
            else:
                subcat_string = ""
            if subsubcat not in results_schema.NULL_VALUES:
                subsubcat_string = str(subsubcat)
            else:
                subsubcat_string = ""
            category = (cat, subcat, subsubcat, dbnr, dbrs)
            this_constraint_list = [
                (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
                 self.config.performername),
                (t1s.DBF_TABLENAME, t1s.DBF_CAT, cat_string),
                (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT, subcat_string),
                (t1s.DBF_TABLENAME, t1s.DBF_SUBSUBCAT, subsubcat_string),
                (t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS, dbnr),
                (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE, dbrs)]
            if cat in t1s.ATOMIC_CATEGORIES:
                for fieldtype in t1s.TEST_FIELD_TYPES.numbers_list():
                    fieldtype_str = t1s.TEST_FIELD_TYPES.to_string(fieldtype)
                    atomic_constraint_list = this_constraint_list + [
                        (t1s.DBA_TABLENAME, t1s.DBA_FIELDTYPE,
                         fieldtype_str)]
                    atomic_correctness_getter = correctness.QueryCorrectnessGetter(
                        self.config.results_db,
                        constraint_list=atomic_constraint_list, update_db=True)
                    self._atomic_correctness_getters[
                        category + tuple([fieldtype])
                        ] = atomic_correctness_getter
                correctness_getter = sum(
                    [self._atomic_correctness_getters[
                        category + tuple([fieldtype])]
                     for fieldtype in t1s.TEST_FIELD_TYPES.numbers_list()],
                    correctness.QueryCorrectnessGetter())
            else:
                correctness_getter = correctness.QueryCorrectnessGetter(
                    self.config.results_db,
                    constraint_list=this_constraint_list, update_db=True)
            self._correctness_getters[category] = correctness_getter

    def get_correctness_getter(self, cat=None, subcat=None, subsubcat=None,
                               dbnr=None, dbrs=None, fieldtype=None):
        """Returns the desired correctness getter"""
        correctness_getter = correctness.QueryCorrectnessGetter()
        if cat != None:
            assert cat in t1s.CATEGORIES.numbers_list(), (
                "invalid cat number %s" % str(cat))
        if subcat != None:
            assert cat, "invalid subcat %s without cat" % str(subcat)
            assert subcat in t1s.SUBCATEGORIES[cat].numbers_list(), (
                "invalid subcat number %s" % str(subcat))
        if subsubcat != None:
            assert cat, "invalid subsubcat %s without cat" % str(subsubcat)
            assert subcat, ("invalid subsubcat %s without subsubcat"
                            % str(subsubcat))
            assert subsubcat in t1s.SUBSUBCATEGORIES[
                (cat, subcat)].numbers_list(), (
                    "invalid subsubcat number %s" % str(subsubcat))
        if fieldtype != None:
            assert cat in t1s.ATOMIC_CATEGORIES, (
                "cannot obtain correctness getters by field type for composite "
                "query category %s" % t1s.CATEGORIES.to_string(cat))
            correctness_getters = self._atomic_correctness_getters
            comparison_bases = [cat, subcat, subsubcat, dbnr, dbrs, fieldtype]
        else:
            correctness_getters = self._correctness_getters
            comparison_bases = [cat, subcat, subsubcat, dbnr, dbrs]
        for comparison_objects in correctness_getters.keys():
            if all([(base in [None, obj]) for (base, obj)
                    in zip(comparison_bases, comparison_objects)]):
                correctness_getter += correctness_getters[comparison_objects]
        return correctness_getter

    def get_present_cats(self, cat=True, subcat=True, subsubcat=True,
                         dbnr=True, dbrs=True):
        """Returns a list of the present categories. If subcat is True,
        returns a list of present (cat, subcat) tuples, and if subsubcat is True,
        returns a list of present (cat, subcat, subsubcat) tuples."""
        if subsubcat: assert subcat, (
            "cannot list the present sub-sub-cateogories without listing the "
            "present sub-categories.")
        these_present_cats = []
        for (this_cat, this_subcat, this_subsubcat,
             this_dbnr, this_dbrs) in self.present_cats:
            tuples = zip(
                [this_cat, this_subcat, this_subsubcat, this_dbnr, this_dbrs],
                [cat, subcat, subsubcat, dbnr, dbrs])
            these_items = tuple([this_item for (this_item, item) in tuples
                                 if item])
            if these_items not in these_present_cats:
                these_present_cats.append(these_items)
        return these_present_cats
