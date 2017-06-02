# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Script to check the correctness of query responses. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  02 Dec 2012   omd            Original Version
# *****************************************************************

import argparse
import logging

import result_set as rs
import sys

logger = logging.getLogger(__name__)

def main():
    log_levels = {'DEBUG': logging.DEBUG,
            'INFO': logging.INFO, 'WARNING': logging.WARNING,
            'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--truth', dest = 'truth_files',
            type = argparse.FileType('r'), nargs = '+', required = True,
            help = 'One or more files containing "correct" output. '
            'The files given in --score will be compared to these.')
    parser.add_argument('-s', '--score', dest = 'score_files',
            type = argparse.FileType('r'), nargs = '+', required = True,
            help = 'One or more files to be compared against --truth '
            'for correctness')
    parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
            type = str, choices = log_levels.keys(),
            help = 'Only output log messages with the given severity or '
            'above')

    options = parser.parse_args()

    logging.basicConfig(
            level = log_levels[options.log_level],
            format = '%(levelname)s: %(message)s')

    truth_set = rs.ResultSet()
    for f in options.truth_files:
        logger.info('Processing truth file: %s', f.name)
        truth_set.add(f)

    truth_queries = truth_set.get_query_results()
    num_matched = 0
    num_failed = 0
    for f in options.score_files:
        score_set = rs.ResultSet()
        logger.info('Scoring file: %s', f.name)
        score_set.add(f)

        # Now check each query
        score_queries = score_set.get_query_results()
        for q in score_queries.iterkeys():
            if not (q in score_queries):
                logging.critial('Query "%s" not in the truth set.', q)
                sys.exit(1)

            score_rows = score_queries[q]
            truth_rows = truth_queries[q]
            if score_rows == truth_rows:
                num_matched += 1
            else:
                num_failed += 1
                print 'Error. Results for "%s" did not match' % q
                missing_rows = truth_rows.viewkeys() - score_rows.viewkeys()
                if len(missing_rows) > 0:
                    print 'Missing row ids:', missing_rows
                
                extra_rows = score_rows.viewkeys() - truth_rows.viewkeys()
                if len(extra_rows) > 0:
                    print 'Rows that should not have been returned:', extra_rows

                for k, v in score_rows.iteritems():
                    if k in truth_rows:
                        if v != truth_rows[k]:
                            print ('Incorrect data for row with id %s. '
                                'Expected %s but got %s' %
                                (k, truth_rows[k], v))

    print 'Scoring complete. Correct queries: %s. Incorrect: %s' % (num_matched,
            num_failed)


if __name__ == '__main__':
    main()
