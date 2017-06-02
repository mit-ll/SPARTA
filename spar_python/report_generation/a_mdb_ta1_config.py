# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A sample TA1 configuration file
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  04 Nov 2013   SY             Original version
# *****************************************************************

# general imports:
import sys
import os
import logging

# SPAR imports:
import spar_python.report_generation.ta1.ta1_database as t1d
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_test_database as t1td
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.ta1.ta1_config as config

config = config.Ta1Config()

################# CONFIGURE THESE PARAMETERS ONLY FOR EACH TEST ################
config.results_db_path = os.path.expanduser("~/spar-testing/results/results_databases/1krows_100kBpr_v2.db") # the path to the results database
config.img_dir = "./a_mdb_ta1_figures" # the path to the directory where created figures
                             # are to be stored.
                             # be sure to create new image directory
                             # if you do not want to override previous images.
config.performername = "MDB" # the name of the performer
config.performerprototype = "MDB TA1 Prototype" # the name of the performer
                                               # prototype
config.baselinename = "MDB" # the name of the baseline

# function to be regressed for computing query latency based on number of
# records returned (inputs should be [numrecords]):
config.ql_all = lambda inputs, a, b: a * inputs[0] + b
config.ql_all_str = config.var_ql + " = %s " + config.var_nummatches + " + %s"

# P2 function to be regressed for computing query latency based on range size
# and number of results (inputs should be [numrecords, range]):
config.ql_p2 = lambda inputs, a, b, c: a * inputs[0] + b * inputs[1] + c
config.ql_p2_str = " ".join([config.var_ql, "= %s", config.var_nummatches,
                             " + %s", config.var_rangesize, "+ %s"])
# P1-and function to be regressed for computing query latency based on
# number of records matching the first term
# and number of results (inputs should be [numrecords, firstmatches]):
config.ql_p1and = lambda inputs, a, b, c: a * inputs[0] + b * inputs[1] + c
config.ql_p1and_str = " ".join([config.var_ql, "= %s", config.var_nummatches,
                             " + %s", config.var_firstmatches, "+ %s"])
# P1-or function to be regressed for computing query latency based on
# sum of the numbers of records matching each term
# and number of results (inputs should be [numrecords, summatches]):
config.ql_p1or = lambda inputs, a, b, c: a * inputs[0] + b * inputs[1] + c
config.ql_p1or_str = " ".join([config.var_ql, "= %s", config.var_nummatches,
                             " + %s", config.var_summatches, "+ %s"])
# P1-dnf function to be regressed for computing query latency based on
# sum of the numbers of records matching each first term
# and number of results (inputs should be [numrecords, sumfirstmatches]):
config.ql_p1dnf = lambda inputs, a, b, c: a * inputs[0] + b * inputs[1] + c
config.ql_p1dnf_str = " ".join([config.var_ql, "= %s", config.var_nummatches,
                             " + %s", config.var_sumfirstmatches, "+ %s"])
# P1-dnf function in five variables to be regressed for computing query latency
# based on sum of the numbers of records matching each first term,
# number of results, number of clauses, and number of terms per clause
# (inputs should be [numrecords, numclauses, numterms, sumfirstmatches]):
def ql_p1dnfcomplex(inputs, a, b, c, d, e):
    output = a * inputs[0] + b * inputs[1] + c * inputs[2] + d * inputs[3] + e
    return output
config.ql_p1dnfcomplex = ql_p1dnfcomplex
config.ql_p1dnfcomplex_str = " ".join([
    config.var_ql,
    "= %s", config.var_nummatches,
    " + %s", config.var_numclauses,
    " + %s", config.var_numterms,
    " + %s", config.var_sumfirstmatches,
    " + %s"])
# P8-eq function to be regressed for computing query latency based on
# sum of the numbers of records matching first n-m+1 terms
# and number of results (inputs should be [numrecords, sumfirstmatches]):
config.ql_p8eq = lambda inputs, a, b, c: a * inputs[0] + b * inputs[1] + c
config.ql_p8eq_str = " ".join([config.var_ql, "= %s", config.var_nummatches,
                             " + %s", config.var_sumfirstmatches, "+ %s"])

################################################################################
# queries which return x records such that
# KEYWORDLEN_NUMRECORDS_MIN < x < KEYWORDLEN_NUMRECORDS_MAX
# will be considered for keyword length P3, P4, P6 and P7 analysis on the main
# database:
config.keywordlen_numrecords_min = {t1s.CATEGORIES.P3: 0,
                                    t1s.CATEGORIES.P4: 0,
                                    t1s.CATEGORIES.P6: 0,
                                    t1s.CATEGORIES.P7: 0}
config.keywordlen_numrecords_max = {t1s.CATEGORIES.P3: 600,
                                    t1s.CATEGORIES.P4: 600,
                                    t1s.CATEGORIES.P6: 600,
                                    t1s.CATEGORIES.P7: 600}
# threshold queries which return x records such that
# THRESHOLD_NUMRECORDS_MIN < x < THRESHOLD_NUMRECORDS_MAX
# will be considered for m and n -depondent runtime analysis on the main
# database:
config.threshold_numrecords_min = 0
config.threshold_numrecords_max = 100
# queries which return x records such that
# DATABASE_NUMRECORDS_MIN < x < DATABASE_NUMRECORDS_MAX
# will be considered for cross-database analysis:
config.crossdb_numrecords_min = 100
config.crossdb_numrecords_max = 1000
# fixed n and m for threshold (P8) queries:
config.fixed_m = 2
config.fixed_n = 3
