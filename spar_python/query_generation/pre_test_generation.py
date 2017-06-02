# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Top-level program for generating rows from the 
#                        distribution 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Sept 2012  jch            Original file
#  30 April 2013 jch            Factored workers & mothership out into
#                                   separate file.
# 10 Sept 2013   jch            Moved from aggregator-spec API to 
#                                  aggregator-api.     
# *****************************************************************

"""
This module contains the top-level 'main' function for data-generation, query 
generation and creating the baseline results for the results database. It will
parse and check command-line options, learn the distributions. With the 
distributions it will generate queries, which are then used to seed aggregators
that run during data generation to populate the results database.     
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

import logging
import datetime
from optparse import OptionParser, OptionGroup, SUPPRESS_HELP
import multiprocessing as mp

import spar_python.common.aggregators.line_raw_aggregator as lra
import spar_python.data_generation.generator_workers as gw
import spar_python.data_generation.learn_distributions as learn_distributions    
import spar_python.query_generation.query_generation as query_generation 
import spar_python.report_generation.ta1.ta1_database as ta1_database   
import spar_python.query_generation.check_schema as cs
import spar_python.common.spar_random as spar_random 




QUERY_RSS_COUNTS_FILENAME = 'query_rss_counts.txt'




def make_expanded_path(path):
    '''
    Return the new path expanding tildes and env variables 
    e.g. "~me/$foo/test1" -> "/home/me/aaa/bbb/test1" 
    '''
    if path:
        path = os.path.expanduser(os.path.expandvars(path))
    return path


# Note: the heavy lifting of this module is split out into the next three
# functions. Why these functions? So that we can get profiling results
# for each of them individually.


def generate_queries(schema_file, logger, dist_holder, options, query_seed):

    if schema_file:
        querysets = query_generation.query_generation(schema_file, 
                                                       logger, 
                                                       dist_holder,
                                                       options.num_rows,
                                                       options.row_width,
                                                       query_seed)
    else:
        querysets = []

    aggregators = [queryset.make_aggregator() for queryset in querysets]

    return (querysets, aggregators)


def generate_rows(options, queryset_aggregators, logger, dist_holder):


    # Note: so that the later zip() works, it is important that 
    # be put at the *start* of options.aggregators. Why? options.aggregators
    # may already contain aggregators, such as a line-raw aggregator. So the
    # worker will return results for our queryset_aggregators *and* more 
    # besides. So that the results line up with the queryset, we would like
    # the results to be at the beginning of the result list. This requires 
    # that queryset_aggregators be at the beginning of the options.aggregators
    # list.
    
    options.aggregators = queryset_aggregators + options.aggregators

    # Spawn a worker and start it
    
    worker = gw.Worker(options, logger, dist_holder)
    aggregator_results = worker.start()
    return aggregator_results

#will probably run into problems writing to the same query file, if so
#fork that out into another function call and just pool refinement
def _call_process_results(bob, agg_result, results_db, queries_file):
    bob.process_results(agg_result,results_db,queries_file)
    
def process_results(querysets, aggregator_results, results_db, queries_file, num_processes):   
    count = 0
    for queryset, agg_result in zip(querysets, aggregator_results):
        queryset.process_results(agg_result,results_db,queries_file)
        count += 1
        logging.info("Processed %d out of %d query_object" % (count,
                                                              len(querysets)))
                                                             
    return


def execute_generation(dist_holder, options, logger, cl_flags,
                       schema_file = None,
                       queries_file = None,
                       results_db = None):
    """
    The heavy lifting: generate the queries, generate the rows of data, 
    process of the results, and write the queries & ground-truth to the 
    database. Note: factored out from set_up_and_execute_run, below, so that
    it can be profiled separately from learning.
    """
    query_seed = cl_flags.query_seed
    
    # generate queries
    (querysets, aggregators) = generate_queries(schema_file, logger, 
                                                dist_holder, options,
                                                query_seed)
    for a in aggregators:
        a.set_process_limit(cl_flags.num_processes)

    
    # generate data
    agg_results = generate_rows(options, aggregators, logger, dist_holder)
    
    # process results - needs to be reseeded because it relies on the
    # overall random state to refine queries
    seed = int(query_seed)
    spar_random.seed(seed)
    process_results(querysets, agg_results, results_db, queries_file, cl_flags.num_processes)
    
    return

      




def set_up_and_execute_run(cl_flags, logger):
    """
    The heavy lifing, to be executed after the command-line flags have been
    parsed and verified.
    """
    
    dist_holder = learn_distributions.learn_distributions(cl_flags, logger)

    
    ##########################################################################
    #
    # Set up data-generation
    #
    #########################################################################
    batch_size = 10000 if cl_flags.num_rows >= 100000000 else 1000
    logger.info('BATCH SIZE: %d' % batch_size)
    options = gw.DataGeneratorOptions(cl_flags.random_seed,
                                      cl_flags.num_processes,
                                      cl_flags.num_rows,
                                      cl_flags.verbose,
                                      [],
                                      batch_size)

    if cl_flags.line_raw_file is not None:
        
        lra_options_dict = {
            'base_filename'    : cl_flags.line_raw_file,
            'schema_file' : cl_flags.schema_file}

        
        if cl_flags.named_pipes:
            lra_aggregator = lra.LineRawPipeAggregator(**lra_options_dict)
        else:
            lra_aggregator = lra.LineRawFileAggregator(**lra_options_dict)
            
        options.aggregators = [ lra_aggregator ]

    if cl_flags.gen_queries:
        queries_file = open(cl_flags.list_of_queries_file,'w')
        results_db = ta1_database.Ta1ResultsDB(cl_flags.result_database_file)
        schema_file = open(cl_flags.q_schema_file, 'rU')
    else:
        queries_file = None
        results_db = None
        schema_file = None

    options.row_width = cl_flags.row_width

    execute_generation(dist_holder, options, logger, cl_flags,
                       schema_file, queries_file, results_db)

    if cl_flags.gen_queries:
        queries_file.close()
        results_db.close()
        schema_file.close()
        


def main():
    parser = OptionParser()
    parser.add_option("-v", '--verbose', dest="verbose",
                      action="store_true", default=False,
                      help="Verbose output")

    
    learning_group = OptionGroup(parser, 'Options that control data-ingestion')
    learning_group.add_option("-d", "--data-dir", dest="data_dir",
                      default="./data",
                      help="Directory where data files can be found")
    learning_group.add_option('--allow-missing-files', dest='allow_missing_files',
            action='store_true', default=False,
            help = 'By default this will crash if any files necessary for '
            'data generation are missing. This flag will cause this '
            'program not to crash and to continue learning what it can. '
            'Generally, this is useful only for debugging')
    parser.add_option_group(learning_group)
    

    output_group = OptionGroup(parser, 'Options that control writing '
            'output to files or pipes')
    output_group.add_option('--line-raw-file', dest = 'line_raw_file',
            default = None, help = 'Write LineRaw formatted data between '
            'INSERT/ENDINSERT pairs to this file. Requires the presence of '
            'the --schema-file flag. Note: in '
            "multi-processor mode, will generate multiple files "
            "with names derived from this one.")
    
    output_group.add_option('--schema-file', dest = 'schema_file',
            default = None,
            help = 'Path to the schema file. This is used to ensure '
            'data is generated in the correct order. See '
            '--initial-release-order for more details.')
    output_group.add_option('--named-pipes', dest = 'named_pipes',
            action = 'store_true', default = False,
            help = 'If given in --line-raw-file, will create '
            'and write to named pipes rather than regular files.')
    parser.add_option_group(output_group)

    gen_group = OptionGroup(parser, 'Options that control data generation')
    gen_group.add_option("--seed", dest="random_seed", type='int', default=0,
                      help="Random seed for generation. Defaults to 0")
    gen_group.add_option('--num-processes', dest='num_processes',
            type = "int", default = 1,
            help = 'The number of processes to spawn when parallelization'\
                      ' is desired.')
    gen_group.add_option('--num-rows', help='the number of rows to create',
            dest='num_rows', type = 
            'int', default = 1000)
    gen_group.add_option('--row_width', help='the average width of rows in the database'\
                         ' , given in bytes',
                         dest='row_width', type = 'int', default = 100)
    parser.add_option_group(gen_group)
    
    query_group = OptionGroup(parser, 'Options that control query generation')
    query_group.add_option('--generate-queries', dest = 'gen_queries',
                           action='store_true', default = False,
                           help = 'Toggle switch to generate queries on '
                           'this run of data generation. Defaults to false.')
    query_group.add_option('--query-schema-file', dest = 'q_schema_file',
            default = None,
            help = 'Path to the schema file for queries, this is used'
            ' to determine which queries need to be generated')
    query_group.add_option('--query-generation-seed',
                           dest = 'query_seed',
                           default = 0, 
                           help = "The seed for query generation. Defaults to 0")
    query_group.add_option('--result-database-file', 
                           dest = 'result_database_file',
                           default = None,
                           help = 'Path to the file where the result database '
                           'will be generated')
    query_group.add_option('--list-of-queries-file', 
                           dest = 'list_of_queries_file',
                           default = None,
                           help = 'Path to the file which will be generated '
                           'containing the list of queries generated')
    parser.add_option_group(query_group)


    (cl_flags, _) = parser.parse_args()


    # How verbose does the user want us to be?
    # TODO allow operator to specify any debug level (debug, info, warning,
    # error, critical)
    if cl_flags.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(
            level = log_level, format = '%(levelname)s: %(message)s')

    logger = logging.getLogger("generate_data")
        
    # 
    # Expand all input files and paths
    #
    cl_flags.data_dir = make_expanded_path(cl_flags.data_dir)
    cl_flags.line_raw_file = make_expanded_path(cl_flags.line_raw_file)
    cl_flags.schema_file = make_expanded_path(cl_flags.schema_file)
    cl_flags.q_schema_file = make_expanded_path(cl_flags.q_schema_file)
    cl_flags.result_database_file = \
        make_expanded_path(cl_flags.result_database_file)
    cl_flags.list_of_queries_file = \
        make_expanded_path(cl_flags.list_of_queries_file)


    #
    # Sanity-check cl_flags
    #
    logger.info("Parsing and checking command-line flags.")

    if all([cl_flags.line_raw_file is None,
            not cl_flags.gen_queries]):
        logger.error("No output option is set. Specify --line-raw-file or --generate-queries")
        exit()

    if cl_flags.line_raw_file is not None:
        if cl_flags.schema_file is None:
            logger.error('--line-raw-file requires --schema-file')
            exit()
        if not os.path.exists(cl_flags.schema_file):
            logger.error('Schema file "%s" does not exist.', cl_flags.schema_file)
            exit()            

    if cl_flags.gen_queries:
        if cl_flags.result_database_file is None:
            logger.error('--result-database-file must be specified')
            exit()
        elif os.path.exists(cl_flags.result_database_file):
            logger.warning('--result-database-file already exists')
        if cl_flags.list_of_queries_file is None:
            logger.error('--list-of-queries-file must be specified')
            exit()
        elif os.path.exists(cl_flags.list_of_queries_file):
            logger.error('--list-of-queries-file already exists and it '
                         'should not exist')
            exit()

 
    logger.debug("Command-line flags look okay.")
    
    #check input
    if cl_flags.gen_queries:
        try:
            cs.check_format(open(cl_flags.q_schema_file, 'rU'), cl_flags.num_rows)
        except AssertionError:
            logger.debug('Ill-formed query-schema. EXITING')
            exit()
        logger.debug("Query file looks okay")    
    
    
    set_up_and_execute_run(cl_flags, logger)



if __name__ == "__main__":
    main()


