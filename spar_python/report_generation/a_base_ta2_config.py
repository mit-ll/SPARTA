# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A sample TA2 configuration file
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
import spar_python.report_generation.ta2.ta2_database as t2d
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.ta2.ta2_config as config

config = config.Ta2Config()

################# CONFIGURE THESE PARAMETERS ONLY FOR EACH TEST ################
config.results_db_path = "../circuit_generation/ibm/phase2_tests/resultsdb.db" # the path to the results database
config.img_dir = "./figures" # the path to the directory where created figures
                             # are to be stored.
                             # be sure to create new image directory
                             # if you do not want to override previous images.
config.performername = "BASE" # the name of the performer
config.performerprototype = "Baseline" # the name of the performer
                                               # prototype
config.baselinename = "BASE" # the name of the baseline

# key generation latency:
def keygenlatencyfunc(inputs, a, b, c, d):
    return a * inputs[0]**2 + b * inputs[0] + c * inputs[1] + d
config.keygenlatency = keygenlatencyfunc
config.keygenlatency_str = (config.var_latency + 
                            " = %s" + config.var_depth + "^2 " + 
                            " + %s" + config.var_depth +
                            " + %s" + config.var_batchsize +
                            " + %s")

# evaluation latency:
def encryptionlatencyfunc(inputs, a, b, c, d, e):
    return (a * inputs[0]**2 +
            b * inputs[0] +
            c * inputs[1] +
            d * inputs[0] * inputs[1] + e)
config.encryptionlatency = encryptionlatencyfunc
config.encryptionlatency_str = (config.var_latency + 
                          " = %s" + config.var_depth + "^2 " + 
                          " + %s" + config.var_depth +
                          " + %s" + config.var_numbatches +
                          " + %s" + config.var_numbatches + config.var_depth +
                          " + %s")

# evaluation latency:
def evallatencyfunc(inputs, a, b, c, d):
    return a * inputs[0]**2 + b * inputs[0] + c * inputs[1] + d
config.evallatency = evallatencyfunc
config.evallatency_str = (config.var_latency + 
                          " = %s" + config.var_depth + "^2 " + 
                          " + %s" + config.var_depth +
                          " + %s" + config.var_numbatches +
                          " + %s")

# complex evaluation latency:
def complexevallatencyfunc(inputs, a, b, c, d, e):
    return a * inputs[0]**2 + b * inputs[0] + c * inputs[1] + d * inputs[2] + e
config.complexevallatency = complexevallatencyfunc
config.complexevallatency_str = (config.var_latency + 
                                 " = %s" + config.var_depth + "^2 " + 
                                 " + %s" + config.var_depth +
                                 " + %s" + config.var_numbatches +
                                 " + %s" + config.var_batchsize +
                                 " + %s")


################################################################################
