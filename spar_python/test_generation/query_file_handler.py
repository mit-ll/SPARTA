# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Used to create query files for a specific
#                      performer, database, category and subcategory
# *****************************************************************

import logging
import csv
import collections
import sys
import os
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta1.ta1_schema as rdb


logger = logging.getLogger(__name__)
TIMING = collections.namedtuple('Timing',
                                ['fixed_cost_per_query',
                                 'cost_per_match'])

LATENCY = 'latency'
THROUGHPUT = 'throughput'
PERFORMANCE = 'performance'


class QueryFileHandler(object):
    '''
    Use one instance for each cat-subcat set of queries.
    Manages the query files for that set of queries.
    Used for latency, throughput and performancy tests.
    For latency tests, it breaks up the queries, based on estimated
    time they will take, into many query files. For throughput tests,
    it creates one query file for each cat_subcat for each result size
    bin. For performance tests, it creates one file for cat_subcat.
    '''

    def __init__(self, query_dir, db_record_size, db_num_records, 
                 dbsize_string, performer, cat, subcat, doing_select_star,
                 max_time_in_minutes, timings, starting_test_id):
        '''
        The argument 'timings' is the entire timings csv file read in
        as a list where each element is a dictionary for that row of
        the file. Note that timings is for all db sizes and all
        performers and all categories. This class reduces it down to the
        rows that are relevant for this particular query file handler.
        '''
        self.__query_dir = query_dir
        self.__db_record_size = db_record_size
        self.__db_num_records = db_num_records
        self.__dbsize_string = dbsize_string
        self.__performer = performer
        self.__cat = cat
        self.__subcat = subcat
        self.__starting_test_id = starting_test_id
        # __max_time in seconds, used to split up latency query files
        self.__max_time = max_time_in_minutes * 60
        self.__doing_select_star = doing_select_star
        if (doing_select_star):
            self.__select_type = "select_star"
            self.__select_phrase = ' SELECT * FROM main WHERE '
        else:
            self.__select_type = "select_id"            
            self.__select_phrase = ' SELECT id FROM main WHERE '
        self.__file_num = 0
        self.__lqfile = None  # current latency query file

        # The throughput file name might exist but the file might not.
        # This is to avoid empty files, it doesn't open the file unless
        # it has something to write to it.
        self.__tqfile_name = None  # name for the throughput query file
        self.__tqfile = None  # current throughput query file

        # remember the range that the existing latency file is for
        self.__matches_lbound = None
        self.__matches_ubound = None

        self.__cum_time = 0  # in seconds of latency queries

        # Time in seconds for all latency query files written
        self.__total_time = 0.0 

        self.__query_files = { LATENCY : [],
                               THROUGHPUT : [],
                               PERFORMANCE : [] }
        self._create_timings(timings)

        if query_dir != "UNITTESTSPECIAL": # skip for the unit test
            self.write_readme()

    def _get_available_dbs(self, timings):
        '''
        Return all db_num_rows found for this performer in a sorted list
        '''
        # This assumes that the timings csv file will be completely
        #  filled out for a performer with rows for all cats and select
        #  *, etc.
        sizes = set([])
        for row in timings:
            if row['performer'] == self.__performer:
                sizes.add(int(row['db_num_rows']))
        sorted_sizes = sorted(sizes)
        return sorted_sizes

    def _create_timings(self, timings):

        # Find the section of the csv file that corresponds to
        # self.__db_record_size. The table might not have entries for
        # the exact record size so choose the next largest one.
        sorted_db_sizes = self._get_available_dbs(timings)
        # initialize to the largest size
        use_db_rows = sorted_db_sizes[-1]
        for db_rows in sorted_db_sizes:
            if self.__db_num_records <= db_rows:
                use_db_rows = db_rows
                break;

        times = []
        for row in timings:
            if row['cat'] == self.__cat and \
                    row['performer'] == self.__performer and \
                    int(row['doing_select_star']) == \
                      int(self.__doing_select_star) and \
                    int(row['db_num_rows']) == use_db_rows:
                times.append(row)

        # should only be one row found
        if len(times) != 1:
            logger.error("cannot create query timings for performer: %s, "
                         "cat: %s, doing_select_star: %d, db_num_rows: %d "
                         "- check the timings file to make sure this row is "
                         "specified. Found %d rows contaning this "
                         "information" % (self.__performer, self.__cat, 
                                          self.__doing_select_star, 
                                          self.__db_num_records, len(times)))
            sys.exit(1)
            
        self.__timings = times[0]

    def get_cat(self):
        return self.__cat
        
    def get_subcat(self):
        return self.__subcat
    
    def get_doing_select_star(self):
        return self.__doing_select_star

    def get_performer(self):
        return self.__performer
    
    def get_query_files(self):
        return self.__query_files

    def get_total_time(self):
        ''' estimated time for all latency query tests '''
        return self.__total_time

    def _estimate_time(self, num_matches, p1_num_match_first_term, 
                       p9_matching_record_counts):
        '''
        Estimate how long this query will take in seconds
        '''
        if self.__timings['fixed_cost_per_query'] == 'NA':
          fixed_cost_per_query = 1.0
        else:
          fixed_cost_per_query = float(self.__timings['fixed_cost_per_query'])
        if self.__timings['cost_per_match'] == 'NA':
          cost_per_match = 1.0
        else:
          cost_per_match = float(self.__timings['cost_per_match'])
        if self.__timings['r_term'] == 'NA':
          r_term = 'full'
        else:
          r_term = self.__timings['r_term']

        r_val = float(num_matches)    
        if r_term == 'first_term' and self.__subcat=='eqand':
            r_val = float(p1_num_match_first_term)
        elif r_term == 'm_of_n_ibm':
            ''' 
            Ideally, to get the perfect estimate for IBM1 P8 queries 
            we would use the max of the number of matching records for the 
            first n-m+1 terms. Since we do not have that stored in the 
            result database, instead use the largest number from 
            p9_matching_record_counts number. 

            The p9_matching_record_counts contains one element for each 
            number of terms. 
            For example: 

            2 of 3 (fname=jill, lname=poland, group=59)
            
            if 53 records match exactly one of those, 12 match two of those, 
            and 1 matches all three, then that field will be 1|12|53

            The reason why the smallest numbers are first is because it shows 
            the "most relevant" records first where:
              most relevant = matching all the terms
            '''
            if not p9_matching_record_counts:
              r_val = 1.0
            else:
              r_val = float(p9_matching_record_counts[-1])

        if not r_val:
            logger.error("for performer: %s, "
                         "cat: %s, doing_select_star: %d, db_num_rows: %d "
                         "- Expected a value for %s but the corresponding "
                         "field from the full table of the result database "
                         "had a value of None" \
                             % (self.__performer, self.__cat, 
                                self.__doing_select_star, 
                                self.__db_num_records, r_term))
            exit(1)

        estimate = 0.0
        estimate = fixed_cost_per_query + (cost_per_match * r_val)
        return estimate

    def _write_query_helper(self, qid, query_clause, qfile):
        query_clause = query_clause.replace("''", "'")
        query_str = str(qid) + self.__select_phrase + \
            query_clause + '\n'
        qfile.write(query_str) 

    def write_readme(self):
        filename = os.path.join(self.__query_dir, "README")
        file_obj = open(filename, 'w')
        file_obj.write("Contains query files\n"
                   "  \n" 
                   "Query filenames for latency and throughput: \n"
                   "  <performer>_<database-num-records>_"
                   "<database-record-size>_<category>_<subcategory>_"
                   "<matching-record-set-lbound>_"
                   "<matching-record-set-ubound>_"
                   "<latency | throughput | performance>_"
                   "<select_star | select_id>_"
                   "<unique-num-or-desciption-for-queries-of-this-type>"
                   "\n")
        file_obj.close()

    def _make_query_filename(self, matches_lbound, matches_ubound, type, 
                             description):
        '''
        Create a filename from the information passed in.
        type - is either LATENCY or THROUGHPUT or PERFORMANCE
        description - is a string that can be anything but typically is
        a unique number
        '''
        # create the filename
        filename = \
            os.path.join(self.__query_dir, 
                         '_'.join([self.__performer, 
                                   self.__dbsize_string,
                                   str(self.__starting_test_id),
                                   self.__cat]))
        if self.__subcat:
            filename = '_'.join([filename, self.__subcat])
        if matches_lbound:
            filename = '_'.join([filename, str(matches_lbound), 
                                 str(matches_ubound)])
        filename = '_'.join([filename, type, self.__select_type, description]) \
            + ".q"
        return filename        

    def _new_query_file(self, matches_lbound, matches_ubound, type):
        '''
        type is either: LATENCY or THROUGHPUT
        '''
        self.__file_num = self.__file_num + 1
        filename = self._make_query_filename(matches_lbound, matches_ubound,
                                             type,
                                             str(self.__file_num))

        # Open the file and do some bookeeping
        if type == LATENCY:
            self.__lqfile = open(filename, 'w')
            self.__matches_lbound = matches_lbound
            self.__matches_ubound = matches_ubound
            self.__query_files[type].append(filename)
        elif type == THROUGHPUT:
            # don't open until the first query (to prevent empty files)
            self.__tqfile_name = filename


    def _close_latency_file(self):
        if self.__lqfile and not self.__lqfile.closed:
            self.__lqfile.close()
            self.__lqfile = None
            self.__cum_time = 0

    def write_query(self, qid, num_matches, query_clause, 
                    p1_num_match_first_term, 
                    p9_matching_record_counts,
                    matches_lbound,
                    matches_ubound):
        q_time_est = self._estimate_time(num_matches, p1_num_match_first_term, 
                                         p9_matching_record_counts)
        self.__total_time = self.__total_time + q_time_est

        # Determine if we need to open a new latency query file
        if not self.__lqfile or \
                self.__matches_lbound != matches_lbound or \
                self.__matches_ubound != matches_ubound or \
                self.__cum_time + q_time_est > (self.__max_time):
            self._close_latency_file()
            self._new_query_file(matches_lbound, matches_ubound, LATENCY)
                
        self.__cum_time = self.__cum_time + q_time_est
        self._write_query_helper(qid, query_clause, self.__lqfile)

        # Determine if we need to open the throughput file
        if not self.__tqfile:
            # this is the first query so open the file
            if not self.__tqfile_name:
                logger.error("Must call QueryFileHandler.initialize_"
                             "query_files() before calling "
                             "QueryFileHandler.write_query()")
                sys.exit(1)
            self.__tqfile = open(self.__tqfile_name, 'w')
            self.__query_files[THROUGHPUT].append(self.__tqfile_name)
        self._write_query_helper(qid, query_clause, self.__tqfile)

    def initialize_throughput_query_file(self, matches_lbound, matches_ubound):
        '''
        User must call this method before calling write_query to set
        up a file for the thoughput queries for this cat_subcat
        lbound-ubound result range.
        '''
        self._new_query_file(matches_lbound, matches_ubound, THROUGHPUT)
        
    def finalize_latency_query_file(self):
        '''
        User must call this method after calling write_query for all 
        the latency queries of this cat_subcat lbound-ubound result range.
        '''
        self._close_latency_file()

    def finalize_throughput_query_file(self):
        '''
        User must call this method after calling write_query for all 
        the throughput queries of this cat_subcat (all lbound-ubound ranges 
        go into one throughput file).
        '''
        if self.__tqfile:
            self.__tqfile.close()
            self.__tqfile = None
        self.__tqfile_name = None

    def write_performance_queries(self, perf_queries):
        '''
        Create a new performance query file and put all queries 
        from perf_queries into it.
        '''
        if len(perf_queries) == 0:
            return

        filename = self._make_query_filename(None, None,
                                             PERFORMANCE, "1")
        pfile = open(filename, 'w')
        self.__query_files[PERFORMANCE].append(filename)

        for (qid, num_matches, query_clause) in perf_queries:
            self._write_query_helper(qid, query_clause, pfile)

        pfile.close()

