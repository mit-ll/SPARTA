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

# SPAR imports:
import spar_python.report_generation.common.regression as regression

class Config(object):
    """Represents a configuration object.

    Attributes:
        threshold_rsquared: the lowest r-squared such that the associated best-
            fit curve is still displayed
        numsigfigs: the number of significant digits after a decimal point to
            display
        results_db_path: the path to the results database
        img_dir: the path to the directory where created figures are to be
            stored. Be sure to create new image directory if you do not want to
            override previous images.
        performername: the name of the performer
        performerprototype: the name of the performer prototype
        baselinename: the name of the baseline
        tanum: the number of the technical area (should be 1 or 2)
    """
    def __init__(self):
        """Initializes the configuration object"""
        # other parameters with default value:
        self.threshold_rsquared = .75
        self.numsigfigs = 3
        # per-performer parameters:
        self.results_db_path = None
        self.img_dir = None
        self.performername = None 
        self.performerprototype = None
        self.baselinename = None
        self.tanum = None
        self.perf_img_dir = None
