from common import parse_queries

import argparse
import logging
import sqlite3
import os
import re

LOGGER = logging.getLogger(__name__)
# This should contain all valid file prefixes for ground truth log files
FILE_PREFIXES = ['UnloadedQueryRunner']
DB_SIZE_PATTERN = \
    re.compile('.*(?P<size>(?:1G)|(?:10G)|(?:100G)|(?:500G)|(?:1T)|(?:10T)).*')

def main():
  log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                'CRITICAL': logging.CRITICAL}

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input_dir', dest = 'input_dir',
          type = str, required = True,
          help = 'Directory containing test results')
  parser.add_argument('-o', '--output_db', dest = 'output_db',
          type = str, required = True,
          help = 'sqlite *.db file that will store parsed ground truth')
  parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
          type = str, choices = log_levels.keys(),
          help = 'Only output log messages with the given severity or '
          'above')

  options = parser.parse_args()

  logging.basicConfig(
          level = log_levels[options.log_level],
          format = '%(levelname)s: %(message)s')

  # Obtain test DB size from input directory name.
  assert os.path.isdir(options.input_dir)
  m = DB_SIZE_PATTERN.match(options.input_dir)
  assert m, 'Could not determine database size from input directory'
  db_size = m.group('size')

  # Establish database connection
  db_conn = sqlite3.connect(options.output_db)
  db_curs = db_conn.cursor()
  # Create the ground_truth table if it doesn't exist yet
  sql_cmd = "CREATE TABLE IF NOT EXISTS ground_truth (" + \
      "query TEXT NOT NULL, cols TEXT NOT NULL, db_size TEXT NOT NULL," + \
      "command_times TEXT NOT NULL, results_times TEXT NOT NULL," + \
      "results TEXT NOT NULL, PRIMARY KEY(query, cols, db_size))"
  db_curs.execute(sql_cmd)
  db_conn.commit()

  # Function used to process each complete query record. Returns 0 if no new
  # rows are created, and returns 1 if a new row is created.
  def record_func(query_info):
    sql_cmd = 'INSERT INTO ground_truth VALUES (' + \
              '"%s", "%s", "%s", "%s", "%s", "%s")' % \
      (query_info['query'], query_info['cols'], db_size, 
       query_info['command_time'], query_info['results_time'],
       '|'.join([str(x).strip('()').replace(' ', '').replace("'", '') \
           for x in query_info['results']]))
    try:
      db_curs.execute(sql_cmd)
      db_conn.commit()
      return 1
    # If an IntegrityError occurs, we have likely hit a duplicate row
    except sqlite3.IntegrityError:
      where_clause = 'query = "%s" AND cols = "%s" AND db_size = "%s"' % \
                     (query_info['query'], query_info['cols'], db_size)
      sql_cmd = 'SELECT command_times, results_times, results ' + \
                'FROM ground_truth WHERE %s' % where_clause
      db_curs.execute(sql_cmd)
      row = db_curs.fetchone()
      # Should only be one row in results
      assert not db_curs.fetchone()
      # Check that the results in the existing row are the same as what we're
      # trying to insert. 
      new_results = \
       '|'.join([str(x).strip('()').replace(' ', '').replace("'", '') \
           for x in query_info['results']])
      if new_results != row[2]:
        LOGGER.warning('Mismatched results for query %s. ' + \
            'Deleting results; note that results will be ' + \
            're-introduced upon re-run.', query_info['query'])
        sql_cmd = 'DELETE FROM ground_truth WHERE %s' % where_clause
        db_curs.execute(sql_cmd)
        db_conn.commit()
      # If there are new command or results times, append the new times to the
      # existing times.
      elif query_info['command_time'] not in row[0].split('|') or \
           query_info['results_time'] not in row[1].split('|'):
        LOGGER.debug('Additional result found for query %s',
            query_info['query'])
        sql_cmd = 'UPDATE ground_truth SET ' + \
                  'command_times = "%s", results_times = "%s" WHERE %s' % \
                  ('%s|%s' % (row[0], query_info['command_time']),
                   '%s|%s' % (row[1], query_info['results_time']),
                   where_clause)
        db_curs.execute(sql_cmd)
        db_conn.commit()
      else:
        LOGGER.warning('Additional entry found for query %s, but no new ' + \
                       'timing information found', query_info['query'])
      return 0

  for path in os.listdir(options.input_dir):
    full_path = os.path.join(options.input_dir, path)
    # Skip directories or any unexpected file names
    if os.path.isdir(full_path):
      continue
    found_prefix = False
    for prefix in FILE_PREFIXES:
      if path.startswith(prefix):
        found_prefix = True
        break
    if not found_prefix:
      continue
    # Process the contents of this file
    LOGGER.info('Processing %s...', full_path)
    f = open(full_path, 'r')
    LOGGER.info('Inserted %d new rows into database', 
                parse_queries(f, record_func))
    f.close()
    print

if __name__ == '__main__':
    main()
