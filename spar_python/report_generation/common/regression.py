# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A regression tool for use with the results database 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  5 Aug 2013    MZ             Original Version
#  15 Aug 2013   SY             Updated for extensibility to TA2
# **************************************************************

# general imports:
import numpy as np
from scipy.optimize import curve_fit
import logging

# SPAR imports:
import spar_python.report_generation.common.graphing

# LOGGER:
LOGGER = logging.getLogger(__file__)

class BadRegressionInputError(Exception): pass

class Function(object):
    """
    Stores all the information about a best-fit function.

    Attributes:
        function: the function itself
        string: a string describing the function
    """

    def __init__(self, function, string):
        self.function = function
        self.string = string

    def get_rsquared(self, inputs, outputs):
        """
        Returns the coefficient of determination (r-squared value)
        """
        processed_inputs = np.array([np.array([np.float64(j)for j in i])
                                     for i in inputs])
        processed_outputs = np.array([np.float64(i) for i in outputs])
        func = self.function
        yhat = func(processed_inputs)
        ybar = np.sum(processed_outputs) / len(processed_outputs)
        ssreg = np.sum((yhat-ybar)**2)
        sstot = np.sum((processed_outputs - ybar)**2)
        return round(ssreg / sstot, 3)

class FunctionToRegress(object):
    """
    Stores all the information about the curve which is necessary to perform
    regression.

    Attributes:
        function_to_regress_template: a functions with the variable (or list
            of variables) x, corresponding to the independent variables,
            and an arbitrary number of coefficients.
            For example, a function_to_regress might take (x, a, b, c), where
            a, b, and c are used as coefficients.
        function_to_regress_str: a string representing the function, with %s
            as placeholders for the constants
    """

    def __init__(self, function_to_regress_template,
                 function_to_regress_string):
        self.function_to_regress_template = function_to_regress_template
        self.function_to_regress_string = function_to_regress_string

    def _get_function(self, coefficients):
        """Returns the function with the coefficients subbed in"""
        def func(inps):
            return self.function_to_regress_template(inps, *coefficients)
        return func
    
    def _get_function_string(self, coefficients):
        """Returns a string representing the function with the coefficients
        subbed in"""
        coeff_strings = tuple([str(round(coefficient, 3))
                               for coefficient in coefficients])
        function_string = self.function_to_regress_string % coeff_strings
        # make sure negative numbers are displayed properly:
        function_string = function_string.replace("+ -", "-")
        function_string = function_string.replace("+=", "-")
        return function_string

    def get_function(self, coefficients):
        """Returns a Function object"""
        return Function(self._get_function(coefficients),
                        self._get_function_string(coefficients))

def regress(function_to_regress, outputs, inputs,
            guesses=None, sdeviations=None):
    """
    Performs a regression on the given function with the given data points.
    Uses the curve_fit function from the scipy package (http://short/curvefit).
    
    Args:
        function_to_regress: a FunctionToRegress object
        outputs: a list of values of the dependent variable
        inputs: a list of lists of values of the independent variables
        guesses: a list of guesses of the values of each coefficient
        sdeviation: the standard deviation of the output data
    """
    # make sure that regression is possible before continuing:
    if not len(outputs) > len(inputs):
        LOGGER.info("Cannot regress - only have %s data points: %s"
                    % (str(len(inputs)), str(inputs)))
        raise BadRegressionInputError("too few data points: %s"
                                      % str(inputs))
    input_tuples = [tuple([inp[var_idx] for inp in inputs])
                    for var_idx in xrange(len(inputs[0]))]
    if not len(list(set(outputs))) > 1:
        LOGGER.info("Cannot regress - have fewer than two output values: %s"
                    % str(list(set(outputs))))
        raise BadRegressionInputError(
            "need more than one unique output value to regress: %s"
            % str(list(set(outputs))))
    if not len(list(set(input_tuples))) > 1:
        LOGGER.info("Cannot regress - have fewer than two values: %s"
                    % str(list(set(input_tuples))))
        raise BadRegressionInputError(
            "need more than one unique input to regress: %s"
            % str(list(set(input_tuples))))
    this_maxfev = 10000 * len(outputs)
    # Returns the coefficients generated by curve_fit.
    # [1] returns the covariance
    processed_inputs = np.array([np.array([np.float64(j)for j in i])
                                 for i in inputs])
    processed_outputs = np.array([np.float64(i) for i in outputs])
    coefficients = curve_fit(
        function_to_regress.function_to_regress_template, processed_inputs,
        processed_outputs, p0=guesses, sigma=sdeviations, maxfev=this_maxfev)[0]
    return function_to_regress.get_function(coefficients)
