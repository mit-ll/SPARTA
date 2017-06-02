# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A report generation configuration class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Sep 2013   SY             Original version
# *****************************************************************

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.common.config as config
import spar_python.report_generation.ta1.ta1_database as t1d
import spar_python.report_generation.ta1.ta1_schema as t1s

# LOGGER:
LOGGER = logging.getLogger(__file__)

# a few constants:
# short database names (all should be in title-case):
SHORT_DATABASE_NAMES = {
    (10000, 100): "Toy Database",
    (1000000, 100): "Skinny 1 Million Row Database",
    (100000000, 100): "Skinny 100 Million Row Database",
    (1000000000, 100): "Skinny 1 Billion Row Database",
    (100000, 100000): "Wide 100 Thousand Row Database",
    (1000000, 100000): "Wide 1 Million Row Database",
    (100000000, 100000): "Wide 100 Million Row Database"}
# main_db heirarchy (the first present database from the following list
# will be used in the overview analysis):
MAIN_DB_HEIRARCHY = [
    (100000000, 100000),
    (10000000, 100000),
    (1000000, 100000),
    (1000000000, 100),
    (100000000, 100),
    (1000000, 100),
    (10000, 100)]

class Ta1Config(config.Config):
    """Represents a configuration object.

    Attributes:
        var_ql: the variable name for query latency
        var_nummatches: the variable name for the number of matching records
        var_rangesize: the variable name for the range size
        var_firstmatches: the variable name for the number of records matching
            the first clause of a boolean statement
        var_summatches: the variable name for the sum of the numbers of
            records matching the clauses of a boolean statement
        var_sumfirstmatches: the variable name for the sum of the numbers of
            records matching the first term of each clause of a boolean
            statement
        var_numclauses: the variable name for the number of clauses of a
            boolean statement
        var_numterms: the variable name for the number of terms in each clause
            of a boolean statement
        results_db_path: the path to the results database
        img_dir: the path to the directory where created figures are to be
            stored. Be sure to create new image directory if you do not want to
            override previous images.
        performername: the name of the performer
        performerprototype: the name of the performer prototype
        baselinename: the name of the baseline
        tanum: the number of the technical area (should be 1)
        ql_all: function to be regressed for computing query latency based on
            number of records returned (inputs should be [numrecords])
        ql_all_str: the string representing ql_all (should have %s for each
            regression parameter)
        ql_p2: P2 function to be regressed for computing query latency based on
            range size and number of results (inputs should be [numrecords,
            range])
        ql_p2_str: the string representing ql_p2 (should have %s for each
            regression parameter)
        ql_p1and: P1-and function to be regressed for computing query latency
            based on number of first-term matches and number of results (inputs
            should be [numrecords, firstmatches])
        ql_p1and_str: the string representing ql_p1and (should have %s for each
            regression parameter)
        ql_p1or: P1-or function to be regressed for computing query latency
            based on number of first-term matches and number of results (inputs
            should be [numrecords, summatches])
        ql_p1or_str: the string representing ql_p1or (should have %s for each
            regression parameter)
        ql_p1dnf: P1-dnf function to be regressed for computing query latency
            based on sum of first-term matches and number of results (inputs
            should be [numrecords, sumfirstmatches])
        ql_p1dnf_str: the string representing ql_p1dnf (should have %s for each
            regression parameter)
        ql_p1dnfcomplex: P1-dnf function to be regressed for computing query
            latency based on the number of results, the number of clauses, the
            number of terms per clause, and the sum of first-term matches,
            (inputs should be [numrecords, numclauses, numterms,
            sumfirstmatches])s
        ql_p1dnfcomplex_str: the string representing ql_p1dnfcomplex (should have %s
            for each regression parameter)
        ql_p8eq: P8-eq function to be regressed for computing query
            latency based on the number of results and the sum of the number of
            records matching ,
            (inputs should be [numrecords, sumfirstmatches])s
        ql_p8eq_str: the string representing ql_p8_eq (should have %s
            for each regression parameter)
        keywords_numrecords_min: a dict mapping query type to the smallest
            number of records returned to be considered for keyword length
            -dependant latency analysis
        keywords_numrecords_max: a dict mapping query type to the largest
            number of records returned to be considered for keyword length
            -dependant latency analysis
        crossdb_numrecords_min: a number such that a query returning fewer
            records than that will not be considered in cross-database analysis
            (so that the analysis reflects database size impact, not number of
            records returned impact)
        crossdb_numrecords_min: a number such that a query returning more
            records than that will not be considered in cross-database analysis
            (so that the analysis reflects database size impact, not number of
            records returned impact)
        fixed_m: the fixed m for threshold (P8) queries
        fixed_n: the fixed n for threshold (P8) queries
        threshold_numrecords_min: the smallest number of records returned to be
            considered for m and n - dependent latency analysis
        threshold_numrecords_max: the largest number of records returned to be
            considered for m and n - dependent latency analysis
        a_req: the value of a for which performers are required to meet the
            performer <= a + b*baseline percentile requirement
        a_max: the greatest value of a for whcih performer will be compared to
            a + b*baseline
        b_req: the value of b for which performers are required to meet the
            performer <= a + b*baseline percentile requirement
        b_max: the greatest value of b for whcih performer will be compared to
            a + b*baseline
        desired_sections: a list of sections to be included in the report
    """
    def __init__(self):
        """Initializes the configuration object"""
        super(Ta1Config, self).__init__()
        # variable names for use in graphs:
        self.var_ql = 'ql'
        self.var_nummatches = 'x'
        self.var_rangesize = 'r'
        self.var_firstmatches = 'f'
        self.var_summatches = 's'
        self.var_sumfirstmatches = 'sf'
        self.var_numclauses = 'c'
        self.var_numterms = 't'
        # per-performer parameters:
        self.performername = None
        self.performerprototype = None
        self.baselinename = None
        self.tanum = 1
        self.ql_all = None
        self.ql_all_str = None
        self.ql_p2 = None
        self.ql_p2_str = None
        self.ql_p1and = None
        self.ql_p1and_str = None
        self.ql_p1or = None
        self.ql_p1or_str = None
        self.ql_p1dnf = None
        self.ql_p1dnf_str = None
        self.ql_p1dnfcomplex = None
        self.ql_p1dnfcomplex_str = None
        self.ql_p8eq = None
        self.ql_p8eq_str = None
        # query generation parameters:
        self.keywordlen_numrecords_min = None
        self.keywordlen_numrecords_max = None
        self.crossdb_numrecords_min = None
        self.crossdb_numrecords_max = None
        self.fixed_m = None
        self.fixed_n = None
        self.threshold_numrecords_min = None
        self.threshold_numrecords_max = None
        # the percentile requirements (performer <= a*baseline + b); the max
        # values are the largest included, and the req values are this phase's
        # requirements:
        self.a_max = 15
        self.a_req = 8
        self.b_max = 10
        self.b_req = 5
        # report generation parameters:
        self.results_db_path = None
        self.__results_db = None
        self.img_dir = None
        self.desired_sections = [
            "ta1_other_sections",
            "ta1_supported_query_types",
            "ta1_correctness",
            "ta1_correctness_query",
            "ta1_correctness_policy",
            "ta1_performance",
            "ta1_performance_latency",
            "ta1_performance_throughput",
            "ta1_performance_percentiles",
            "ta1_modifications",
            "ta1_overview",
            "ta1_overview_eq",
            "ta1_overview_p1",
            "ta1_overview_p1_eqand",
            "ta1_overview_p1_eqor",
            "ta1_overview_p1_eqdnf",
            "ta1_overview_p1_eqdeep",
            "ta1_overview_p1_eqcnf",
            "ta1_overview_p1_eqnot",
            "ta1_overview_p1_otherand",
            "ta1_overview_p1_otheror",
            "ta1_overview_p1_otheribm",
            "ta1_overview_p2",
            "ta1_overview_p3",
            "ta1_overview_p4",
            "ta1_overview_p6",
            "ta1_overview_p7",
            "ta1_overview_p8",
            "ta1_overview_p8_eq",
            "ta1_overview_p8_other",
            "ta1_overview_p9",
            "ta1_overview_p9_eq",
            "ta1_overview_p9_other",
            "ta1_overview_p11",
            "ta1_performance_percentiles_aux",
            "ta1_system_utilization"]
        
    @property
    def ql_all_ftr(self):
        """Gives a function to regress object corresponding to the query latency
        function."""
        return regression.FunctionToRegress(
            self.ql_all, self.ql_all_str)

    @property
    def ql_p2_ftr(self):
        """Gives a function to regress object corresponding to the P2 query
        latency function."""
        return regression.FunctionToRegress(
            self.ql_p2, self.ql_p2_str)
    
    @property
    def ql_p1and_ftr(self):
        """Gives a function to regress object corresponding to the P1-and query
        latency function."""
        return regression.FunctionToRegress(
            self.ql_p1and, self.ql_p1and_str)

    @property
    def ql_p1or_ftr(self):
        """Gives a function to regress object corresponding to the P1-or query
        latency function."""
        return regression.FunctionToRegress(
            self.ql_p1or, self.ql_p1or_str)

    @property
    def ql_p1dnf_ftr(self):
        """Gives a function to regress object corresponding to the P1-dnf query
        latency function."""
        return regression.FunctionToRegress(
            self.ql_p1dnf, self.ql_p1dnf_str)

    @property
    def ql_p1dnfcomplex_ftr(self):
        """Gives a function to regress object corresponding to the P1-dnf query
        latency function for a number of variables greater than 3."""
        return regression.FunctionToRegress(
            self.ql_p1dnfcomplex, self.ql_p1dnfcomplex_str)

    @property
    def ql_p8eq_ftr(self):
        """Gives a function to regress object corresponding to the P8-eq query
        latency function."""
        return regression.FunctionToRegress(self.ql_p8eq, self.ql_p8eq_str)

    @property
    def results_db(self):
        """Returns the results database."""
        if not self.__results_db:
            self.__results_db = t1d.Ta1ResultsDB(self.results_db_path)
        return self.__results_db

    def get_constraint_list(self, require_correct=True, usebaseline=False,
                            throughput=False, mod=False):
        """Returns a constraint list based on the given arguments"""
        constraint_list = []
        if require_correct:
            constraint_list.append(
            (t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT, True))
        if usebaseline:
            constraint_list.append(
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
             self.baselinename))
        else: constraint_list.append(
            (t1s.DBP_TABLENAME, t1s.DBP_PERFORMERNAME,
             self.performername))
        isthroughputquery = bool(throughput)
        constraint_list.append(
            (t1s.DBP_TABLENAME, t1s.DBP_ISTHROUGHPUTQUERY, isthroughputquery))
        ismodquery = bool(mod)
        constraint_list.append(
            (t1s.DBP_TABLENAME, t1s.DBP_ISMODIFICATIONQUERY, ismodquery))
        return constraint_list
