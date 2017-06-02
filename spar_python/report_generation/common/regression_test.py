# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Unit testing for ta1_lmregress.py 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  5 Aug 2013    MZ             Original Version
# **************************************************************

# general imports:
import sys
import os
import warnings
import sqlite3
import unittest

# SPAR imports:
import spar_python.report_generation.common.regression as regression

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
#Allows spar_python imports
import spar_python.common.spar_random  as sr

ACCEPTIBLE_ERROR = 1.0
NUM_TRIALS = 10

def FUNCTION_TO_REGRESS_TEMPLATE(x, a, b, c):
    """
    A simple function to perform regression on.
    Args:
        x: A list of integers.
        a,b,c: Coefficients
    """
    return (x[0] * a/2) + pow(x[1], b) + c

FUNCTION_TO_REGRESS_STRING = "%s x/2 + y^%s + %s"
FUNCTION_TO_REGRESS = regression.FunctionToRegress(
    FUNCTION_TO_REGRESS_TEMPLATE, FUNCTION_TO_REGRESS_STRING)

class RegressionTest(unittest.TestCase):

    def setUp(self):
        SEED = 7 #sr.randint(0, 1000000000)
        sr.seed(SEED)

    def test_function_to_regress(self):
        function = FUNCTION_TO_REGRESS.get_function([1, 2, 3])
        self.assertEquals(FUNCTION_TO_REGRESS_STRING % ("1.0", "2.0", "3.0"),
                          function.string)
        self.assertEquals(FUNCTION_TO_REGRESS_TEMPLATE([1, 2], 1, 2, 3),
                          function.function([1, 2]))

    def test_regress(self):
        NUM_INPUTS = 2
        NUM_DATAPOINTS = sr.randint(5, 1000)
        ACCEPTIBLE_ERROR = 1.0
        NUM_TRIALS = 2
        for trial_num in xrange(NUM_TRIALS):
            A = float(sr.randint(1, 100))
            B = float(sr.randint(1, 5))
            C = float(sr.randint(1, 100))
            inputs = [[sr.randint(1,200)
                       for data_point in xrange(NUM_DATAPOINTS)]
                      for inp in xrange(NUM_INPUTS)]
            outputs = [FUNCTION_TO_REGRESS_TEMPLATE(
                [inputs[inp][data_point] for inp in xrange(NUM_INPUTS)],
                A, B, C) + sr.random()
                for data_point in xrange(NUM_DATAPOINTS)]
            function_guess = regression.regress(
                function_to_regress=FUNCTION_TO_REGRESS,
                outputs=outputs, inputs=inputs)
            test_inputs = [sr.randint(1, 100) for inp in xrange(NUM_INPUTS)]
            self.assertTrue(
                abs(function_guess.function(test_inputs) -
                    FUNCTION_TO_REGRESS_TEMPLATE(test_inputs, A, B, C))
                < ACCEPTIBLE_ERROR)
            rsquared = function_guess.get_rsquared(inputs, outputs)
            self.assertTrue(rsquared > .8)
