# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Executes and profiles small-scale pre-generation
#                      runs (for benchmarking optimization).
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
# 27 Aug 2013    JCH            Original file
# *****************************************************************

"""
This module will learn a data-distribution, and then execute and profile
small-scale pre-generation runs:

* Generating queries,
* Transforming the queries into aggregators, and
* Generating data against those aggregators.

By doing so, this file can be used for benchmarking optimization efforts.

The top results from both profiling runs are both printed to screen and emailed
to Jon Herzog (though the recipient can be easily changed). Also, the resulting
profile-objects are written to files, where each file-name contains the current
data and current git-hash of the repository.
"""


import os
import sys

# Note that realpath (as opposed to abspath) also expands symbolic
# links so the path points to the actual file. This is important when
# installing scripts in the install directory.  Scripts will be
# symbolic linked to the install directory. When a script is run from
# the install directory, realpath will convert it to the actual path
# where the script lives. Appending base_dir to sys.path (as done
# below) allows the imports to work properly.
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)


import cProfile
import pstats
import logging
import datetime
import subprocess
import StringIO
import smtplib
from email.mime.text import MIMEText
from optparse import OptionParser
from email.utils import parseaddr
from string import Template

import spar_python.data_generation.generator_workers as gw
import spar_python.data_generation.learn_distributions as learn_distributions    
import spar_python.query_generation.pre_test_generation as ptg
import spar_python.report_generation.ta1.ta1_database as ta1_database   
import spar_python.query_generation.check_schema as cs



        
class LearnerOptions(object):
    pass



# Various constants
RANDOM_SEED = 17
NUM_PROCESSES = 1
QUERY_SEED = 23

BATCH_SIZE = 1000

SERVER = 'LLPOST.llan.ll.mit.edu'

ROW_WIDTH = 1000

BENCHMARK_NUM_ROWS = 1000

SCHEMA_FILES = [
    ('10_8', 10 ** 8, '100Mrows_100kBpr.csv'),
    ('10_8', 10 ** 8, '100Mrows_100Bpr.csv'),
#    ('10_6', 10 ** 6, '1Mrows_100kBpr.csv'),
#    ('10_6', 10 ** 6, '1Mrows_100Bpr.csv'),
#    ('10_5', 10 ** 5, '100krows_100kBpr.csv'),
    ]


########################################################################
#
# helper_functions
#
#######################################################################



def _get_file_suffix(row_count):
    """
    Return the suffix for profile files (which will identify today's date
    and the current git hash).
    """
    date = datetime.date.today()
    git_hash = subprocess.check_output(['git', 'log', '-1', 
                                        '--pretty=format:%h'])
    file_suffix = "-%s-%s-%s.prof" % (row_count, date.isoformat(), git_hash)
    return file_suffix


def make_prof_name(basename, prof_directory, row_count):
    '''
    Build the name for the prof file.
    '''
    file_suffix = _get_file_suffix(row_count)
    return os.path.join(prof_directory, basename + file_suffix)


def send_string_by_email(addresses, subject, msg_body):
    '''
    Send the given message, using the given subject, as email to the address
    given at the top of this file.
    '''
    for address in addresses:
        msg = MIMEText(msg_body)
        msg['Subject'] = subject
        msg['From'] = address
        msg['To'] = address
    
        s = smtplib.SMTP(SERVER)
        s.sendmail(address, [address], msg.as_string())
        s.quit()
    return



#####################################################################
#
# Benchmarking
#
#######################################################################



def process_profile(prof_object, schema_name, prof_dir, step_name, row_count):

    prof_filename = make_prof_name(schema_name, prof_dir, row_count)
    
    buffer_for_results = StringIO.StringIO()
    buffer_for_results.write("Schema being executed: %s\n" % schema_name)
    buffer_for_results.write("Number of rows: {:,}\n".format(row_count))
    buffer_for_results.write("Step: %s\n" % step_name)

    
    stats = pstats.Stats(prof_object, stream=buffer_for_results)
    stats.strip_dirs().sort_stats('time').print_stats(10)
    
    msg = buffer_for_results.getvalue()
    return msg
    




def do_profiling(dist_holder, schema_name, schema_handle, query_seed,
                 row_count, logger, prof_dir, email_addresses):
    """
    Do a profile run with the given query-schema and print/email the results
    """

    ##################################################################
    #
    # Set up
    #
    ###################################################################


    # Make the GeneratorOptions object:
    options = gw.DataGeneratorOptions(RANDOM_SEED,
                                      NUM_PROCESSES,
                                      row_count,
                                      False, # verbose
                                      [], #aggregators
                                      BATCH_SIZE)

    
    

    # Queries file. Note: we don't actually use this, 
    # but let's define it just in case
    queries_file = StringIO.StringIO()
    
    results_db =  ta1_database.Ta1ResultsDB(':memory:')


    ####################################################################
    #
    # Do the profiling
    #
    ####################################################################


    # generate queries
    pr1 = cProfile.Profile()
    pr1.enable()
    options.row_width = ROW_WIDTH
    (querysets, aggregators) = ptg.generate_queries(schema_handle, logger, 
                                                    dist_holder, options,
                                                    query_seed)
    pr1.disable()
    prof_string1 = process_profile(pr1, schema_name, prof_dir, 'query generation', BENCHMARK_NUM_ROWS)
    
    if email_addresses:
        subject = "Query generation profiling"
        send_string_by_email(email_addresses, subject, prof_string1)
    
    
    # generate data
    pr2 = cProfile.Profile()
    pr2.enable()
    options.num_rows = BENCHMARK_NUM_ROWS
    agg_results = ptg.generate_rows(options, aggregators, logger, dist_holder)
    pr2.disable()
    prof_string2 = process_profile(pr2, schema_name, prof_dir, 'row generation', BENCHMARK_NUM_ROWS)

    if email_addresses:
        subject = "Row generation profiling"
        send_string_by_email(email_addresses, subject, prof_string2)
    
    # # process results
    # pr3 = cProfile.Profile()
    # pr3.enable()
    # ptg.process_results(querysets, agg_results, results_db, queries_file)
    # pr3.disable()
    # prof_string3 = process_profile(pr3, schema_name, prof_dir, 'result processing', BENCHMARK_NUM_ROWS)

    # if email_addresses:
    #     subject = "Resutl-processing profiling"
    #     send_string_by_email(email_addresses, subject, prof_string3)

    prof_string3 = "Result-processing skipped."
    
    return [prof_string1, prof_string2, prof_string3]



        
def main():
    ''' 
    Do a profiling run for each schema at the beginning of this module, and
    print/email the results.
    '''
    

    parser = OptionParser()
    parser.add_option('-v', '--verbose',
                      action = 'store_true',
                      default = False,
                      dest = 'verbose',
                      help = 'Increase verbostity of output')
    parser.add_option("-a", '--address',
                      action = 'append',
                      dest = 'email_addresses',
                      help="Email address to which to send these results. "
                      "Can be used repeatedly for more than one address. ")
    parser.add_option("-d", '--data-dir',
                      action = 'store',
                      dest = 'data_dir',
                      default = None,
                      help = 'Directory in which to find demographic data')
    parser.add_option("-p", '--prof-dir',
                      action = 'store',
                      dest = 'prof_dir',
                      default = None,
                      help = 'Directory in which to store profile-result '
                      'objects. Note: will be made if it does not already '
                      'exist.')
    parser.add_option('--pickle-file', 
                      dest = 'pickle_file',
                      default = None,
                      help = 'Used only for short circuiting the load '
                      'of the PUMS data, used ONLY for testing query '
                      'generation ')

    (cl_flags, _) = parser.parse_args()
    
    ########################################################################
    # Validte flags
    #######################################################################
    
    # verbose
    if cl_flags.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(
            level = log_level, format = '%(levelname)s: %(message)s')
    logger = logging.getLogger('benchmarker')

    
    #addresses
    if cl_flags.email_addresses:
        email_addresses = cl_flags.email_addresses
    else:
        logger.info('Note: no email address given for profile results.')
        email_addresses = []


    address_part_pairs = [parseaddr(addr) for addr in email_addresses]

    for (input_addr, (_, addr_part)) in zip(email_addresses, 
                                            address_part_pairs):
        if not addr_part:
            logger.error("%s does not seem to be a valid email address",
                         input_addr)
            sys.exit(1)
    
    validated_addresses = [addr_part for (_,addr_part) in address_part_pairs]


    # data_dir
    if not cl_flags.data_dir:
        logger.error("Please use the -d flag to specify a data directory.")
        sys.exit(1)
    if not os.path.exists(cl_flags.data_dir):
        logger.error("Error: the data-directory %s does not exist", 
                     cl_flags.data_dir)
        sys.exit(1)
    if not os.path.isdir(cl_flags.data_dir):
        logger.error("Error: the data-directory %s is not a directory.",
                     cl_flags.data_dir)
        sys.exit(1)
        
    # prof_dir
    if not cl_flags.prof_dir:
        logger.error("Error: please use the -p flag to specify a profile directory.")
        sys.exit(1)
    if not os.path.exists(cl_flags.prof_dir):
        logger.info("The prof-directory %s does not exist, making", 
                     cl_flags.prof_dir)
        os.mkdir(cl_flags.prof_dir)
    if not os.path.isdir(cl_flags.prof_dir):
        logger.error("Error: the prof-directory %s is not a directory.",
                     cl_flags.prof_dir)
        sys.exit(1)
        
        




    # Learn distributions each time this script gets executed, but only
    # once for all profiling runs.
    
        
    
    learner_options = LearnerOptions()
    learner_options.data_dir = cl_flags.data_dir
    learner_options.pickle_file = cl_flags.pickle_file
    learner_options.allow_missing_files = True

    if not cl_flags.pickle_file:
        dist_holder = learn_distributions.learn_distributions(learner_options, 
                                                              logger)
    else:
        if not os.path.exists(cl_flags.pickle_file):
            logger.error("Cannot find the distributions file %s" \
                     % cl_flags.pickle_file)
            exit()
        try:
            logging.info("Starting to unpickle distribution")
            f = open(cl_flags.pickle_file, 'r')
            dist_holder = learn_distributions.unpickle(learner_options, 
                                                       logger, 
                                                       f)
            logging.info('Pickle sucessfully unpickled')
        except Exception as e:
            # Could be cPickle.UnpicklingError, AttributeError, EOFError,
            # ImportError, or IndexError.
            logging.exception("Could not open or unpickle file %s. "\
                              "Exception information follows" 
                              % cl_flags.pickle_file)
            exit()


    results_so_far = []

    for (name, row_count, schema_file_basename) in SCHEMA_FILES:
        schema_file = os.path.join(this_dir, 
                                   '../../scripts-config/ta1/config/query_schemas/',
                                   schema_file_basename)


        try:
            cs.check_format(open(schema_file, 'rU'), row_count)
        except AssertionError:
            logger.debug('Ill-formed query-schema. EXITING')
            exit()
        logger.debug("Query file looks okay")    

        with open(schema_file, 'Ur') as schema_file_handle:
            try:
                run_stats_str = do_profiling(dist_holder, 
                                             name, 
                                             schema_file_handle, 
                                             QUERY_SEED,
                                             row_count, 
                                             logger, 
                                             cl_flags.prof_dir,
                                             validated_addresses)
                results_so_far += run_stats_str
            except KeyboardInterrupt:
                raise
            except:
                logger.exception("Exception during %s, %s rows", 
                                 name, row_count)
    

    # Send the resulting message by email, and print it:
    msg = "".join(results_so_far)
    print msg

    if validated_addresses:
        subject = "Full profiling finished"
        send_string_by_email(validated_addresses, subject, msg)



if __name__ == "__main__":
    main()





