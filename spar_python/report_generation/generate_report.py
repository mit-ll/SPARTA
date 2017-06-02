# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        main method for report generation
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  09 Sep 2013   SY             Original Version
# *****************************************************************

# general imports:
from optparse import OptionParser
import shutil
import subprocess
import os
import sys
import jinja2
import logging

# SPAR imports:
sys.path.append(os.path.join(os.path.dirname(__file__), '..' + os.sep + '..'))
import spar_python.report_generation.ta1.ta1_report_generator as t1rg
import spar_python.report_generation.ta2.ta2_report_generator as t2rg

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

NUM_TYPESETS = 4
JINJA_TEMPLATES_DIR = "templates"

PARSER = OptionParser()
PARSER.add_option(
    "-l", "--loglevel",
    help="the log level",
    default=logging.INFO)
PARSER.add_option(
    "-c", "--configfile",
    help="the path of the file containing all of the configuration parameters"
    " (should be a python file name without the '.py')")
PARSER.add_option(
    "-d", "--destfile",
    help="the path of the file where the report will be stored")
PARSER.add_option(
    "-i", "--imgdir",
    help=("the path of the directory where report images will be stored."
          "CLOBBERS CONFIG FILE VALUE"))
PARSER.add_option(
    "-r", "--resultsdbpath",
    help="the path of the results database. CLOBBERS CONFIG FILE VALUE")
PARSER.add_option(
    "-p", "--performername",
    help="the name of the performer. CLOBBERS CONFIG FILE VALUE")
PARSER.add_option(
    "--performerprototype",
    help="the name of the performer prototype. CLOBBERS CONFIG FILE VALUE")
PARSER.add_option(
    "-b", "--baselinename",
    help="the name of the baseline. CLOBBERS CONFIG FILE VALUE")
PARSER.add_option(
    "-m", "--monitorimgdir",
    help="the path to the performance monitoring image directory")

if __name__ == "__main__":
    (options, args) = PARSER.parse_args()
    logging.basicConfig(level = options.loglevel,
                        format = '%(levelname)s: %(message)s')
    exec "from %s import config" % options.configfile
    if options.imgdir:
        config.img_dir = options.imgdir
    if options.resultsdbpath:
        config.results_db_path = options.resultsdbpath
    if options.performername:
        config.performername = options.performername
    if options.performerprototype:
        config.performerprototype = options.performerprototype
    if options.baselinename:
        config.baselinename = options.baselinename
    if options.monitorimgdir:
        config.perf_img_dir = options.monitorimgdir
    if not options.destfile:
        options.destfile = "_".join(
            ["ta" + str(config.tanum), config.performername, "report"])
    if not os.path.isdir(config.img_dir):
        os.mkdir(config.img_dir)
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(JINJA_TEMPLATES_DIR))
    if config.tanum == 1:
        LOGGER.info("generating a TA1 report")
        report_generator = t1rg.Ta1ReportGenerator(config, jinja_env)
    elif config.tanum == 2:
        LOGGER.info("generating a TA2 report")
        report_generator = t2rg.Ta2ReportGenerator(config, jinja_env)
    else:
        assert False # tanum should be 1 or 2
    tex = open(options.destfile + ".tex", 'w')
    tex.write(report_generator.get_string())
    tex.close()
    for typeset_num in xrange(NUM_TYPESETS):
        subprocess.call("pdflatex " + options.destfile, shell=True)
