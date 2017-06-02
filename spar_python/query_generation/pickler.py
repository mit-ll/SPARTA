# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Learn distributions for data-gen variables
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Sept 2012   jch           copied from learn_education.py
# *****************************************************************


"""
Learns and pickles column-distributions for later
data-generation. Final result will be a dictionary which maps field
names to distributions, which is then pickled. Various command-line
options can be used to specify the source of the training data, the
filename for the pickle, and whether learning should be naive or
neural. (Naive learning assumes that all columns are independent,
while neural learning uses neural nets to learn conditional
probabilities.)

Currently, only naive learning is implemented.
"""

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)


import glob
import cPickle
from optparse import OptionParser
from optparse import OptionGroup
import re
import logging
import csv
import zipfile
import spar_python.data_generation.learn_distributions as ld
import spar_python.data_generation.spar_variables as sv
from spar_python.common.enum import Enum

def main():
    
    parser = OptionParser()
    parser.add_option('-n', "--name", dest="pickle_name",
                      default='distributions.pickle',
                      help=\
                      "Name to assign pickle containing naive distributions")
    parser.add_option("-v", '--verbose', dest="verbose",
                      action="store_true", default=False,
                      help="Verbose output")
    parser.add_option("-d", "--data-dir", dest="data_dir",
                      default="./data",
                      help="Directory where data files can be found")
    parser.add_option('--allow-missing-files', dest='allow_missing_files',
            action='store_true', default=False,
            help = 'By default this will crash if any files necessary for '
            'data generation are missing. This flag will cause this '
            'program not to crash and to continue learning what it can. '
            'Generally, this is useful only for debugging')
    (options, args) = parser.parse_args()

        
    # How verbose does the user want us to be?
    logger = logging.getLogger("User-visible output")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    pickle_file = open(options.pickle_name, 'w')    


    dist_holder = ld.learn_distributions(options, logger)
    dist_holder.dist_dict[sv.VARS.NOTES1] = None
    dist_holder.dist_dict[sv.VARS.NOTES2] = None
    dist_holder.dist_dict[sv.VARS.NOTES3] = None
    dist_holder.dist_dict[sv.VARS.NOTES4] = None
    logger.info("Pickling distributions.")
    cPickle.dump(dist_holder, pickle_file)
    pickle_file.close()
    logger.info("Done")


if __name__ == "__main__":
    main()

