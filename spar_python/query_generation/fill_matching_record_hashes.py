# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            MJR
#  Description:        Given a 'hashes' table and a 
#                      matching_record_ids column, this fills out
#                      the matching_record_hashes column
# *****************************************************************

import argparse
import logging
import os.path
import MySQLdb
import sqlite3
import string
import sys

LOGGER = logging.getLogger(__name__)

def make_expanded_path(file_name):
    ''' Helper function to expand file/directory paths.'''
    if file_name:
        file_name = os.path.realpath( \
                    os.path.normpath( \
                    os.path.expanduser( \
                    os.path.expandvars(file_name))))
    return file_name

def get_database_connection(db_host, db_user, db_pass, db_name):
    '''Helper function to establish database connection.'''
    return MySQLdb.connect(host = db_host, 
                           user = db_user, 
                           passwd = db_pass,
                           db = db_name)

def fill_hashes_column(mariadb_conn, sqlite_conn, separator='|'):
    '''Fills the matching_record_hashes column of the full_queries table in the
    sqlite3 results database, assuming that the row_hashes table exists in the
    MariaDB database, and the matching_record_ids columns already exist and have
    been filled in the sqlite3 results database.
    
    Inputs:
    mariadb_conn: connection to the MariaDB database
    sqlite_conn: connection to the sqlite3 database
    separator (optional): separator in matching_record_ids/hashes table
        default='|'
    
    Returns: nothing
    '''

    # Validate input options
    assert mariadb_conn
    assert sqlite_conn

    # Obtain MariaDB cursor
    mariadb_curs = mariadb_conn.cursor(MySQLdb.cursors.DictCursor)

    # For each row of the fqt:
    fqt_query = "SELECT qid, matching_record_ids FROM full_queries;"
    qid_count = 0
    row_hash_map = {}
    for row in sqlite_conn.execute(fqt_query):
        qid_count += 1
        # Get the matching ids
        qid = row[0]
        LOGGER.debug('Processing QID %s (#%s)', qid, qid_count)
        matching_ids = string.split(row[1], sep=separator)
        # Convert IDs to hashes
        matching_hashes = []
        for matching_id in matching_ids:
            # account for possiblity of no maching IDs (sqlite will return
            # an empty string)
            if not len(matching_id):
              continue
            if matching_id in row_hash_map:
                thishash = row_hash_map[matching_id]
            else:
                num_results = mariadb_curs.execute( \
                    "SELECT hash FROM row_hashes WHERE id = %s",
                     (matching_id,))
                assert num_results == 1, 'Multiple row hashes found for %s' % \
                                         matching_id
                thishash = mariadb_curs.fetchone()['hash']
                row_hash_map[matching_id] = thishash
            matching_hashes.append(thishash)
        # make a single pipe-delimeted row
        table_entry = separator.join(matching_hashes)
        # update fqt
        fqt_update =  "UPDATE full_queries SET matching_record_hashes = ? " + \
            "WHERE qid = ?"
        sqlite_conn.execute(fqt_update, (table_entry, qid))
    # commit the updates
    sqlite_conn.commit()
        
def main():
    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                  'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                  'CRITICAL': logging.CRITICAL}

    # Define command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--row-database', dest = 'row_database',
        type = str, required = True, help = 'Name of MariaDB database; '
        'must contain a \'row_hashes\' table with columns (id, hash)')
    parser.add_argument('--row-host', dest = 'row_host',
        type = str, default = 'localhost', help = 'MariaDB database host')
    parser.add_argument('-u', '--row-user', dest = 'row_user',
        type = str, default = 'root', help = 'MariaDB database user')
    # TODO(njhwang) What if there isn't a password to database? Will this work?
    parser.add_argument('-p', '--row-password', '--row-passwd', 
         dest = 'row_password', default = 'SPARtest', type = str, 
         help = 'MariaDB database password')
    parser.add_argument('-r', '--results-database', dest = 'results_database',
        type = str, required = True, help = 'Name of sqlite3 database; '
        ':memory: can be used as a magic value for an in-memory only database')
    parser.add_argument('--log-level', dest = 'log_level', default = 'INFO',
        type = str, choices = log_levels.keys(),
        help = 'Only output log messages with the given severity or '
               'above')

    options = parser.parse_args()

    # Update input options that may require path expansion
    options.results_database = make_expanded_path(options.results_database)

    # Validate input options
    assert os.path.isfile(options.results_database)

    # Update logging level
    logging.basicConfig(level = log_levels[options.log_level],
                        format = '%(levelname)s: %(message)s')

    # Establish database connections
    mariadb_conn = get_database_connection(options.row_host,
                                           options.row_user,
                                           options.row_password,
                                           options.row_database)
    sqlite_conn = sqlite3.connect(options.results_database)
    fill_hashes_column(mariadb_conn, sqlite_conn)
    mariadb_conn.close()
    sqlite_conn.close()
    
if __name__ == "__main__":
    main()
