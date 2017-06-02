# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Given a list of result databases containing 
#                      ground truth generate the test scripts for 
#                      all requested performers
# *****************************************************************


import csv
import sys
import os
from optparse import OptionParser
import logging
import collections
import random
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.report_generation.ta1.ta1_database as ta1_database
import spar_python.query_generation.query_schema as qs
import spar_python.test_generation.query_file_handler as qfh
import spar_python.test_generation.test_utils as tu


# MDB mariaDB 
PERFORMERS = ['IBM1', 'IBM2', 'COL', 'MDB']

PERFORMER_TO_RDB_FIELD = { 'IBM1' : rdb.DBF_IBM1SUPPORTED, 
                           'IBM2' : rdb.DBF_IBM2SUPPORTED, 
                           'COL' : rdb.DBF_COLUMBIASUPPORTED, 
                           'MDB' : None }


def write_ts_readme(output_dir):
    '''
    Write out a readme explaining the naming convension for the .ts files
    '''
    filename = os.path.join(output_dir, "README")
    file_obj = open(filename, 'w')
    file_obj.write("Contains test scripts and the queries they call\n" 
                   "  \n" 
                   "Test script filenames: \n"
                   "  <performer>_"
                   "<database-num-records>_<database-record-size>_"
                   "<test-number>_"
                   "<category>_<subcategory>_"
                   "<throughput | latency | performance>_"
                   "<select-type>.ts \n"
                   "  \n"
                   "queries directory contains query files\n")
    file_obj.close()

def new_test_file(output_dir, db_record_size, db_num_records, 
                  performer, cat_subcat, id_generator, test_type):
    ''' make a filename for a new latency, throughput, or performance .ts file'''
    details = '_'.join([id_generator.get_id(), cat_subcat, test_type])
    name = '-'.join([performer,  
                     tu.get_dbsize_string(db_record_size, db_num_records), 
                                          details])  + '.ts'
    filename = os.path.join(output_dir, name)
    file_obj = open(filename, 'w')
    return file_obj

def write_end_test(tfile):
    '''write the final shutdown line to tfile.
    I left this separate in case we every wanted to combine several
    query files into one test. 
    '''
    tfile.write('RootModeMasterScript SHUTDOWN\n')

def write_latency_test(tfile, qfilename, num_times):
    ''' write the latency test to tfile'''
    # Query file path must be relative to the test script directory
    qfilename = os.path.relpath(qfilename, os.path.dirname(tfile.name))
    tfile.write('RootModeMasterScript CLEARCACHE\n')
    cmd = 'UnloadedQueryRunner ' + qfilename + ' ' +  str(num_times) + '\n'
    tfile.write(cmd)

def get_all_cats_and_subcats():
    '''
    Returns a list containing all possible combinations of category
    and subcategory. This list will be in order, with all the
    categories like P1 together before moving on to P2.
    The list contains tuples of category string and subcategory string
    '''
    cats_subcats = []
    for cat, cat_enum in zip(rdb.CATEGORIES.values_list(),
                             rdb.CATEGORIES.numbers_list()):
        if cat_enum in rdb.SUBCATEGORIES:
            subcats = rdb.SUBCATEGORIES[cat_enum].values_list()
            for subcat in subcats:
                cats_subcats.append((cat, subcat))
        else:
            subcat = ''
            cats_subcats.append((cat, subcat))
    return cats_subcats

def write_latency_throughput_queries(query_file_handler, resultdb, 
                                     lbound, ubound):
    '''
    Write query files for sub_subcat of queries with a match count between 
    lbound and ubound
    '''
    atomic_table_name = rdb.DBA_TABLENAME
    ftoa_table_name = rdb.F2A_TABLENAME
    cat = query_file_handler.get_cat()
    subcat = query_file_handler.get_subcat()
    doing_select_star = query_file_handler.get_doing_select_star()
    performer_clause = PERFORMER_TO_RDB_FIELD[query_file_handler.get_performer()]


    # DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM
    # DBF_P9MATCHINGRECORDCOUNTS (use last value as r)

    # Get all queries in full_query_table that match: 
    #   performer and 
    #   cat and
    #   subcat and
    #   num_matches in range of: lbound and ubound
    cmd = "select distinct a.aqid, a.num_matching_records, a.where_clause " +\
    "from atomic_queries a, full_to_atomic_junction f where a.aqid=" +\
    "f.atomic_row_id and not f.atomic_row_id = f.full_row_id"
    cmd = cmd + " AND a." + rdb.DBA_CAT + " = \'" + cat + "\'" + " AND "
    # Note: there is currently an issue with what should be in the 
    # result database for categories which do not have a subcat
    # so to get around this - just don't check subcat when it is
    # not relevant.
    if subcat:
        cmd = cmd + " a." + rdb.DBA_SUBCAT + " = \'" + subcat + "\'" \
        " AND "
    cmd = cmd + " a." + rdb.DBA_NUMMATCHINGRECORDS + " BETWEEN " + \
        str(lbound) + " AND " + str(ubound) 
    
    resultdb._execute(cmd)
    queries = resultdb._fetchall()

    for (qid, num_matches, query_clause) in queries:
        query_file_handler.write_query(qid, num_matches, query_clause, 
                                       '', 
                                       '',
                                       lbound, ubound)
            
    query_file_handler.finalize_latency_query_file()


def write_queries_for_cat_subcat(query_file_handler, resultdb):
    '''
    Write query files for this cat and subcat
    '''
    
    smoketest_query = None
    query_file_handler.initialize_throughput_query_file(1, 100000)
    # Do the latency & throughput queries by matching-record-sets
    for lbound, ubound in [(1,100000)]:
        write_latency_throughput_queries(query_file_handler, resultdb,
                                         lbound, ubound)

    return smoketest_query
    

def write_query_files(query_dir, resultdb, performer, 
                      db_record_size, db_num_records, doing_select_star,
                      max_time_in_minutes, timings, starting_test_id):
    '''
    Main method to write all queries files for the specified
    dbsize and performer. It also uses the doing_select_star bool to
    choose quieries for either select star or select id.
    '''
    total_latency_throughput_time_secs = 0.0

    # query_files is indexed by cat_subcat and contains the list of
    # query filenames for that type of query. It is used later to 
    # write the test scripts which point to these query files.
    query_files = collections.defaultdict(list)

    # process queries for each cat_subcat type
    all_cats_subcats = get_all_cats_and_subcats()
    for cat, subcat in all_cats_subcats:

        # Create a query file handler which does most of the heavy lifting
        query_file_handler = \
            qfh.QueryFileHandler(query_dir, db_record_size, 
                                 db_num_records, 
                                 tu.get_dbsize_string(db_record_size,
                                                      db_num_records),
                                 performer, cat, subcat, 
                                 doing_select_star,
                                 max_time_in_minutes,
                                 timings,
                                 starting_test_id)
        smoketest_query = \
            write_queries_for_cat_subcat(query_file_handler, resultdb)
        if subcat:
            cat_subcat = '_'.join([cat, subcat])
        else:
            cat_subcat = cat

        query_files[cat_subcat] = \
            query_file_handler.get_query_files()

        total_latency_throughput_time_secs = \
            total_latency_throughput_time_secs + \
            query_file_handler.get_total_time()
            
    # query_files is indexed by cat_subcat, smoketest_query_file is a single file
    return (query_files, 
            total_latency_throughput_time_secs)


def write_ts_file(qfilenames, test_type, select_type, delay_in_seconds,
                  output_dir, db_record_size, db_num_records, 
                  performer, cat_subcat, id_generator):
    '''
    Writes the testscript files for a cat_subcat and select_type (either 
    select id or select *) and for a specific test_type (either "latency", 
    "throughput" or "performance") 
    '''
    for qfilename in qfilenames[test_type]:
        test_type_name = test_type + select_type
        # create a new file and open it for writing
        tfile = new_test_file(output_dir, 
                              db_record_size, db_num_records, 
                              performer, cat_subcat, id_generator, 
                              test_type_name)
        #write a test for this file
        write_latency_test(tfile, qfilename, 1)
        write_end_test(tfile)
        tfile.close()

def write_ts_files(output_dir, query_files, smoketest_query_file, 
                   db_record_size, db_num_records, performer, id_generator, 
                   doing_select_star, delay_in_seconds):
    '''
    Main method to write all .ts files for the specified dbsize, performer,
    and either select star or select id.
    '''

    select_type = "_select_id"

    tests = []



    #
    # Write tests for atomics
    #
    for test_type in ['latency']:
        # Generate tests in the order of get_all_cats_and_subcats so that
        # we keep them numbered in the order we expect with EQ first and P11 last
        all_cats_subcats = get_all_cats_and_subcats()
        for cat, subcat in all_cats_subcats:
            cat_subcat = cat
            if subcat:
                cat_subcat = cat + '_' + subcat
            if cat_subcat not in query_files:
                continue
            qfilenames = query_files[cat_subcat]

            write_ts_file(qfilenames, test_type, select_type, delay_in_seconds,
                          output_dir, db_record_size, db_num_records,
                          performer, cat_subcat, id_generator)



def create_tests_scripts(output_dir, query_dir, resultdb, performer,
                         db_record_size, db_num_records, id_generator,
                         delay_in_seconds, max_time_in_minutes, 
                         timings, starting_test_id):
    '''
    Top level method to create all test scripts and query files for 
    the dbsize and performer specified.
    '''


    # query_files is a dictionary indexed by cat_subcat
    # containing a list of query filenames generated for that
    # category.
    #
    # smoketest_query_file is a single file containing one query of each
    # cat_subcat.

    # estimated time in seconds for all latency and throughput tests
    total_est_time = 0.0

    doing_select_star = False
    (select_id_query_files, \
     select_id_time) = \
        write_query_files(query_dir, resultdb, performer, 
                          db_record_size, db_num_records, 
                          doing_select_star, max_time_in_minutes,
                          timings, starting_test_id)
    total_est_time = select_id_time
    write_ts_readme(output_dir)
    doing_select_star = False
    write_ts_files(output_dir, select_id_query_files, 
                   None,
                   db_record_size, db_num_records, 
                   performer, id_generator, doing_select_star,
                   delay_in_seconds)

    return total_est_time


def main():
    '''
    Generate all the ta1 test scripts
    '''


    #
    # Specify options
    #

    parser = OptionParser()
    parser.add_option('-r', '--result_databases',
                      type='string',
                      action='callback',
                      callback=tu.callback_for_list_options,
                      help='List of paths to the result databases to process. '
                      'Syntax: --result_databases \"../10g/10gdb.db,'
                      '../1g/1gdb.db,../100g/100gdb.db\"')
    parser.add_option('-p', '--performers',
                      type='string',
                      action='callback',
                      callback=tu.callback_for_list_options,
                      help='List of performers to generate tests for. ' +
                      'Syntax: --performers \"' + ','.join(PERFORMERS) + '\"')
    parser.add_option("-v", '--verbose', dest="verbose",
                      action="store_true", default=False,
                      help="Verbose output")
    parser.add_option("-o", "--output_dir", dest="output_dir",
                      default="./Tests",
                      help="Base directory where test files will be generated")
    parser.add_option("-d", "--fixed_delay", dest='delay_in_seconds', 
                      type = 'int', default = 5,
                      help="Fixed delay in seconds for performance tests, "
                      "the default is 5 seconds")
    parser.add_option("-m", "--max_time", dest='max_time_in_minutes', 
                      type = 'int', default = 30,
                      help="Maximum time a single test should run "
                      "(in minutes), the default is 30 minutes")
    parser.add_option("-t", "--timings_file", dest="timings_file",
                      help="Timings csv file specifing values used to "
                      "determine how many seconds a query will take to "
                      "run")
    parser.add_option('--start_with_test_number', dest='start_with_test_number',
                      type = 'int', default = 1, 
                      help='Specifies an integer test number to start numbering '
                      'the tests with. The default is 1. This is useful if you '
                      'are creating batches of tests for the same database.')
    (options, args) = parser.parse_args()


    #
    # Create logger
    #

    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(
        level = log_level, format = '%(filename)s: %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    

    # 
    # Check options
    #

    # --performers
    if not options.performers:
        logger.error("No performers specified. Specify --performers")
        exit()
    for performer in options.performers:
        if performer not in PERFORMERS:
            logger.error("Unknown performer %s specified. " \
                         "Expecting only these performers: %s" %  \
                             (performer, ', '.join(PERFORMERS)))
            exit()

    # --output_dir
    if not options.output_dir:
        logger.error("No output directory specified. Specify --output_dir")
        exit()
    options.output_dir = tu.make_expanded_path(options.output_dir)
    # make the directory if it does not exist
    if not os.path.exists(options.output_dir):
        os.makedirs(options.output_dir)

    # -- result_databases
    if not options.result_databases:
        logger.error("No result databases specified. Specify --result_databases")
        exit()
    # expand the path of all the db files
    expanded_dbs = []
    for resultdb in options.result_databases:
        exp_path = tu.make_expanded_path(resultdb)
        if not os.path.isfile(exp_path):
            logger.error('result database ' + exp_path + ' does not exist')
            exit()
        expanded_dbs.append(exp_path)
    options.result_databases = expanded_dbs
    
    if options.timings_file:
        exp_path = tu.make_expanded_path(options.timings_file)
        if not os.path.isfile(exp_path):
            logger.error('timings_file specified  ' + exp_path + \
                             ' does not exist')
            exit()
        options.timings_file = exp_path
    else:
        logger.error('must supply --timings_file ')
        exit()


    # at this point the options look good

    ### Read in the timings file
    # timings will be a list where each element is a dictionary for that
    # row of the file.
    tfile = open(options.timings_file, 'rU')
    reader = csv.DictReader(tfile)
    timings = []
    for row in reader:
        timings.append(row)
    tfile.close()

    id_generator = tu.IDGenerator(options.start_with_test_number - 1)

    # The estimated time in seconds for the latency and throughput tests
    # Indexed by database size and performer
    total_test_times = {}

    # Generate test scripts
    for resultdb_name in options.result_databases:

        resultdb = ta1_database.Ta1ResultsDB(resultdb_name)

        # Determine the database size, we need this for filenames and to 
        # determine how long the queries will take.
        (db_record_size, db_num_records) = tu.get_db_size(resultdb)

        performer_total_times = {}
        for performer in options.performers:

            # Create directories

            # make a performer/dbsize directory under output_dir
            dbsize_str = tu.get_dbsize_string(db_record_size, db_num_records)
            perf_dbsize_dir = os.path.join(options.output_dir, performer, 
                                           dbsize_str)
            if not os.path.exists(perf_dbsize_dir):
                os.makedirs(perf_dbsize_dir)

            # make a queries directory under that
            query_dir = os.path.join(perf_dbsize_dir,"queries")
            if not os.path.exists(query_dir):
                os.makedirs(query_dir)

            total_time = \
                create_tests_scripts(perf_dbsize_dir, query_dir,
                                 resultdb, performer, 
                                 db_record_size, db_num_records, 
                                 id_generator, 
                                 options.delay_in_seconds, 
                                 options.max_time_in_minutes,
                                 timings,
                                 options.start_with_test_number)
            performer_total_times[performer] = total_time

        total_test_times[db_num_records] = performer_total_times 
        resultdb.close()

    display_total_test_times(logger, total_test_times)


def display_total_test_times(logger, total_test_times):
    # total_test_times is a dictionary mapped by db num rows which
    # contains a dictionary mapped by performer with the total number 
    # of seconds that all the latency tests are 
    # estimated to take.
    sum_times = 0.0
    logger.info("Estimated time for latency tests:")
    for database, perf_times in total_test_times.iteritems():
        database_sum = 0.0
        logger.info("  For Database with %d rows:" % database)
        for performer, time in perf_times.iteritems():
            time = float(time) / 60.0
            logger.info("    %s\t%f (minutes)" % (performer,time))
            database_sum = database_sum + time
        logger.info("    TOTAL\t%f (minutes)" % database_sum)
        sum_times = sum_times + database_sum
    logger.info("  TOTAL:%f (minutes)" % sum_times)

if __name__ == "__main__":
    main()
