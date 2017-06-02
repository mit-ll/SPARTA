import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import spar_python.data_generation.spar_variables as sparvars

from common import parse_queries
import argparse
import logging
import sqlite3
import csv
import re

LOGGER = logging.getLogger(__name__)
FILE_PREFIXES = ['VariableDelayQueryRunner', 'UnloadedQueryRunner']
DB_SIZE_PATTERN_STR = '(?:(?:1G)|(?:10G)|(?:100G)|(?:500G)|(?:1T)|(?:10T))'
FILE_NAME_PATTERN_STR = ('(?:(?:UnloadedQueryLatency)|'
                         '(?:UnloadedQueryThroughput)|'
                         '(?:VariableDelayUnloadedQueryLatency))')
QUERY_TYPE_PATTERN = re.compile( \
    '%s\-%s\-(?P<type>[0-9a-z]+)\-(?P<details>[0-9a-z-]+)' % \
    (FILE_NAME_PATTERN_STR, DB_SIZE_PATTERN_STR))
NOTES_PATTERN = re.compile('.*notes(?P<size>[1-4]).*')
P3_P4_PATTERN = re.compile( \
    '(?:(?:CONTAINED_IN)|(?:contained_in)|(?:CONTAINS_STEM)|(?:contains_stem))'
    '\(notes[1-4], \'(?P<search_str>.*)\'\)')
P7_PATTERN = re.compile('(?P<col>.*) (?:(?:LIKE)|(?:like)) '
    '\'(?P<search_str>.*)\'')
NOTES_SIZES = [20, 100, 500, 5000]
UNQUOTED_DOB_PATTERN = re.compile('dob (?P<op>[=<>]*) '
                                  '(?P<date>[0-9]{4}\-[0-9]{2}\-[0-9]{2})')
AND_NOT_PATTERN = re.compile('(?P<noneg>[a-z0-9_]* =[ ]+[a-zA-Z0-9\' -]*) AND[ ]+'
                             'NOT (?P<neg>[a-z0-9_]* =[ ]+[a-zA-Z0-9\' -]*)')
AND_DOB_NOT_CITY_PATTERN = re.compile('(?P<noneg>dob = .*) AND[ ]+'
                                      'NOT (?P<neg>city = .*)')
NOT_SSN_NOT_HWPW_PATTERN = re.compile('(?P<noneg>ssn = .*) AND '
                                      'NOT (?P<neg>hours_worked_per_week = .*)')
# TODO: patterns
# col <=/>=/</> value
# col BETWEEN value and value
# TODO: extrema
#INTEGER_EXTREMA = {'income' : {'min' : 0, 'max' : TBD},
#                   'hours_worked_per_week' : {'min' : 0, 'max' : 167},
#                   'weeks_worked_last_year' : {'min' : 0, 'max' : 52}}
#DOB_EXTREMA = {'min' : TBD, 'max': TBD}

def main():
  log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                'CRITICAL': logging.CRITICAL}

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input_dir', dest = 'input_dir',
          type = str, required = True,
          help = 'Directory containing test results.')
  parser.add_argument('-t', '--truth_db', dest = 'truth_db',
          type = str, required = True,
          help = 'Database containing ground truth.')
  parser.add_argument('-o', '--output_dir', dest = 'output_dir',
          type = str, required = True,
          help = 'Test results in CSV format will be written to this '
                 'directory.')
  parser.add_argument('-p', '--performer', dest = 'performer',
          type = str, required = True,
          help = 'Performer being processed.')
  parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
          type = str, choices = log_levels.keys(),
          help = 'Only output log messages with the given severity or '
          'above')
  parser.add_argument('--disable_correctness', dest = 'dis_correct', 
          default = False, action = 'store_true',
          help = 'Disable correctness checking')

  options = parser.parse_args()

  logging.basicConfig(
          level = log_levels[options.log_level],
          format = '%(levelname)s: %(message)s')

  uqr_patt = re.compile(   '\[[0-9]+\.[0-9]+\] UnloadedQueryRunner '
    '.+/(?P<query_file>.+)\.sql [0-9]+')
  vdqr_patt = re.compile(  '\[[0-9]+\.[0-9]+\] VariableDelayQueryRunner '
    '.+/(?P<query_file>.+)\.sql [0-9]+ '
    'EXPONENTIAL_DELAY (?P<delay>[0-9]+)')
  vdqrnd_patt = re.compile('\[[0-9]+\.[0-9]+\] VariableDelayQueryRunner '
    '.+/(?P<query_file>.+)\.sql [0-9]+ NO_DELAY')
  no_matches_patt = re.compile('^\|*$')

  assert os.path.isdir(options.input_dir)
  assert os.path.isfile(options.truth_db)
  assert os.path.isdir(options.output_dir)

  # Establish database connection
  db_conn = sqlite3.connect(options.truth_db)
  db_curs = db_conn.cursor()

  # Process each file in input_dir
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

    # Determine test database size from file path
    db_size = full_path.split('/')[-3]

    LOGGER.info('Processing file %s...', full_path)
    f = open(full_path, 'r')
    line = f.readline()

    # Confirm file is not empty and has a valid header line
    if len(line) == 0 or len(line.strip()) == 0:
      LOGGER.warning('File %s is empty', full_path)
      continue
    if ' ' not in line:
      LOGGER.warning('First line is not timestamped. Skipping file.')
      continue

    # Determine the name of the output *.csv file based on the header line and
    # performer
    output_file = ''
    match_funcs = [ \
        lambda x: 'UnloadedQueryLatency-%s-%s' % \
          (db_size, x.group('query_file')),
        lambda x: 'VariableDelayUnloadedQueryLatency-%s-%s-%sus' % \
          (db_size, x.group('query_file'), x.group('delay')),
        lambda x: 'UnloadedQueryThroughput-%s-%s' % \
          (db_size, x.group('query_file'))]
    for patt, func in zip([uqr_patt, vdqr_patt, vdqrnd_patt], match_funcs):
      m = patt.match(line)
      if m:
        output_file = func(m)
        break
    if len(output_file) == 0:
      LOGGER.warning('Header does not match any acceptable syntax. Skipping '
          'file. Header: %s', line)
      continue
    if options.performer == 'acs':
      output_file = output_file.replace('-id-', '-star-')

    # Determine what columns to keep based on the type of file parsed 
    csv_cols = []
    if output_file.startswith('UnloadedQueryLatency'):
      csv_cols = ['performer', 'where_clause', 'query_type', 'db_size', 'cols', 
                  'perf_latency', 'base_latencies', 'return_row_cnt', 
                  'ground_truth_cnt', 'incorrect_cnt', 'false_pos_cnt', 
                  'false_neg_cnt', 'conj1_row_cnt', 'conj2_row_cnt', 
                  'or_fan_in', 'max_and_fan_in', 'range_coverage', 'search_col',
                  'search_str_len', 'notes_size', 'substr_type']
    else:
      assert output_file.startswith('UnloadedQueryThroughput') or \
             output_file.startswith('VariableDelayUnloadedQueryLatency')
      csv_cols = ['performer', 'cmd_id', 'where_clause', 'query_type', 
                  'db_size', 'cols', 'perf_command_time', 'perf_results_time', 
                  'return_row_cnt', 'ground_truth_cnt', 'incorrect_cnt', 
                  'false_pos_cnt', 'false_neg_cnt', 'conj1_row_cnt', 
                  'conj2_row_cnt', 'or_fan_in', 'max_and_fan_in', 
                  'range_coverage', 'search_col', 'search_str_len', 'notes_size', 
                  'substr_type']

    # Determine whether output file needs a unique suffix appended
    if os.path.isfile(os.path.join(options.output_dir, output_file + '.csv')) and \
       not output_file.startswith('UnloadedQueryLatency'):
      suffix = 1
      while True:
        if os.path.isfile(os.path.join(options.output_dir, 
                          output_file + '-' + str(suffix) + '.csv')):
          suffix += 1
        else:
          output_file += '-' + str(suffix)
          break

    # Characterize query type based on output_file
    m = QUERY_TYPE_PATTERN.match(output_file)
    query_type = ''
    query_type_details = ''
    if 'one-of-each' not in output_file:
      assert m, 'Could not determine query type for %s' % output_file
      query_type = m.group('type')
      query_type_details = m.group('details')
    if query_type == 'p1' and query_type_details.startswith('p2'):
      query_type = 'p1-p2'
      query_type_details = query_type_details[len('p2'):]
    if query_type == 'p1' and query_type_details.startswith('complex'):
      query_type = 'p1-complex'
    if query_type == 'p1' and query_type_details.startswith('dnf'):
      query_type = 'p1-dnf'

    # Create csv writer
    csv_file = None
    full_path = os.path.join(options.output_dir, output_file + '.csv')
    csv_f = None
    if output_file.startswith('UnloadedQueryLatency') and \
       os.path.isfile(full_path):
      csv_f = open(full_path, 'a')
      csv_file = csv.DictWriter(csv_f, csv_cols, extrasaction='ignore')
    else:
      csv_f = open(full_path, 'w')
      csv_file = csv.DictWriter(csv_f, csv_cols, extrasaction='ignore')
      csv_file.writeheader()

    def record_func(query_info):
      csv_dict = {}
      # Update csv_dict with performer information from query_info
      if options.performer == 'stealth':
        query_info['query'] = query_info['query'].rstrip(';')
      elif options.performer == 'ibm':
        if 'dob' in query_info['query']:
          num_matches = 0
          tmp_query = ''
          last_end = 0
          for match in UNQUOTED_DOB_PATTERN.finditer(query_info['query']):
            tmp_query += query_info['query'][last_end:match.start()]
            tmp_query += "dob %s '%s'" % (match.group('op'),
                                          match.group('date'))
            last_end = match.end()
            num_matches += 1
          tmp_query += query_info['query'][last_end:]
          assert num_matches > 0
          query_info['query'] = tmp_query
      csv_dict['performer'] = options.performer
      csv_dict['cmd_id'] = query_info['command_id']
      csv_dict['where_clause'] = query_info['query']
      csv_dict['cols'] = query_info['cols']
      csv_dict['perf_command_time'] = query_info['command_time']
      csv_dict['perf_results_time'] = query_info['results_time']
      csv_dict['perf_latency'] = \
         repr(float(csv_dict['perf_results_time']) - \
              float(csv_dict['perf_command_time']))
      
      # Update db_size to be the number of rows in the database
      if db_size == '1G':
        csv_dict['db_size'] = 10000
      elif db_size == '10G':
        csv_dict['db_size'] = 100000
      elif db_size == '100G':
        csv_dict['db_size'] = 1000000
      elif db_size == '500G':
        csv_dict['db_size'] = 5000000
      elif db_size == '1T':
        csv_dict['db_size'] = 10000000
      elif db_size == '10T':
        csv_dict['db_size'] = 100000000

      # Update csv_dict with any additional characterization of where_clause
      csv_dict['query_type'] = query_type
      if query_type == 'p1' or query_type == 'p1-dnf':
        if query_type_details.startswith('dnf'):
          dnf_struct = []
          conjs = csv_dict['where_clause'].upper().split(' OR ')
          for conj in conjs:
            dnf_struct.append(len(conj.split(' AND ')))
          csv_dict['dnf_struct'] = '-'.join([str(x) for x in dnf_struct])
          csv_dict['or_fan_in'] = len(dnf_struct)
          csv_dict['max_and_fan_in'] = max(dnf_struct)
        elif query_type_details.startswith('and') or query_type == 'p1-p2':
          parts = query_type_details.split('-')
          csv_dict['conj1_row_cnt'] = parts[1]
          csv_dict['conj2_row_cnt'] = parts[2]
      elif query_type == 'p1-p2':
          parts = query_type_details.split('-')
          csv_dict['conj1_row_cnt'] = parts[2]
          csv_dict['conj2_row_cnt'] = parts[3]
      elif query_type == 'p3' or query_type == 'p4':
        m = P3_P4_PATTERN.match(csv_dict['where_clause'])
        assert m
        csv_dict['search_str_len'] = len(m.group('search_str'))
        m = NOTES_PATTERN.match(csv_dict['where_clause']) 
        assert m
        csv_dict['search_col'] = 'notes%s' % m.group('size')
        csv_dict['notes_size'] = \
            NOTES_SIZES[len(NOTES_SIZES) - int(m.group('size'))]
      elif query_type == 'p7':
        m = P7_PATTERN.match(csv_dict['where_clause'])  
        assert m
        csv_dict['search_col'] = m.group('col')
        csv_dict['search_str_len'] = len(m.group('search_str'))
        init = m.group('search_str').startswith('%')
        term = m.group('search_str').endswith('%')
        if init and term:
          csv_dict['substr_type'] = 'M'
        elif init:
          csv_dict['substr_type'] = 'I'
        elif term:
          csv_dict['substr_type'] = 'T'
        else:
          csv_dict['substr_type'] = 'N'

      # Determine row/hash match info
      row_matches = []
      hash_matches = []
      for result in query_info['results']:
        if type(result) is tuple:
          assert len(result) == 2
          row_matches.append(str(result[0]))
          hash_matches.append(result[1])
        else:
          assert type(result) is int or type(result) is str
          row_matches.append(str(result))
          hash_matches.append('')
      assert len(row_matches) == len(hash_matches)
      csv_dict['return_row_cnt'] = len(row_matches)
      if len(row_matches) > 0 and len(row_matches[0]) == 0:
        row_matches = []
      csv_dict['actual_rows'] = row_matches 
      if len(hash_matches) > 0 and len(hash_matches[0]) == 0:
        hash_matches = []
      csv_dict['actual_hashes'] = hash_matches

      # Search for baseline info that matches query_info
      where_clause = 'query = "%s" AND cols = "%s" AND db_size = "%s"' % \
                     (query_info['query'], query_info['cols'], db_size)
      sql_cmd = 'SELECT command_times, results_times, results ' + \
                'FROM ground_truth WHERE %s' % where_clause
      db_curs.execute(sql_cmd)
      row = db_curs.fetchone()
      # Should only be one row in results
      assert not db_curs.fetchone()

      if not row and options.performer == 'ibm':
        parts = query_info['query'].split(' OR ')
        num_matches = 0
        tmp_query = ''
        for i in range(len(parts)):
          last_end = 0
          for match in AND_NOT_PATTERN.finditer(parts[i]):
            tmp_query += parts[i][last_end:match.start()]
            tmp_query += 'NOT %s AND %s' % (match.group('neg'),
                                            match.group('noneg'))
            last_end = match.end()
            num_matches += 1
          tmp_query += parts[i][last_end:]
          if len(parts) > 1 and i < len(parts) - 1:
            tmp_query += ' OR '
        if num_matches > 0:
          query_info['query'] = csv_dict['where_clause'] = tmp_query
          where_clause = 'query = "%s" AND cols = "%s" AND db_size = "%s"' % \
                         (query_info['query'], query_info['cols'], db_size)
          sql_cmd = 'SELECT command_times, results_times, results ' + \
                    'FROM ground_truth WHERE %s' % where_clause
          db_curs.execute(sql_cmd)
          row = db_curs.fetchone()
          # Should only be one row in results
          assert not db_curs.fetchone()

      # If query of interest is 'SELECT *' but there is no ground truth for
      # that, check to see if there is a 'SELECT id' ground truth result
      col_mismatch = False
      if not row and query_info['cols'] == '*':
        where_clause = 'query = "%s" AND cols = "id" AND db_size = "%s"' % \
                       (query_info['query'], db_size)
        sql_cmd = 'SELECT command_times, results_times, results ' + \
                  'FROM ground_truth WHERE %s' % where_clause
        db_curs.execute(sql_cmd)
        row = db_curs.fetchone()
        # Should only be one row in results
        assert not db_curs.fetchone()
        col_mismatch = True

      # If baseline info exists, update csv_dict appropriately
      if row:
        # Only calculate latencies if the queries were on the same columns
        if not col_mismatch:
          command_times = row[0].split('|')
          results_times = row[1].split('|')
          latencies = [repr(float(x[1]) - float(x[0])) for x in \
              zip(command_times, results_times)]
          csv_dict['base_command_times'] = str(row[0])
          csv_dict['base_results_times'] = str(row[1])
          csv_dict['base_latencies'] = '|'.join(latencies)

        if not options.dis_correct:
          # Determine row/hash match info
          row_matches = []
          hash_matches = []
          for result in str(row[2]).split('|'):
            items = result.split(',')
            if len(items) == 2:
              row_matches.append(items[0].strip())
              hash_matches.append(items[1].strip())
            else:
              assert len(items) == 1
              row_matches.append(items[0].strip())
              hash_matches.append('')
          assert len(row_matches) == len(hash_matches)
          if len(row_matches) == 1 and len(row_matches[0]) == 0:
            csv_dict['ground_truth_cnt'] = 0
          else:
            csv_dict['ground_truth_cnt'] = len(row_matches)
          if len(row_matches) > 0 and len(row_matches[0]) == 0:
            row_matches = []
          csv_dict['expect_rows'] = row_matches 
          if len(hash_matches) > 0 and len(hash_matches[0]) == 0:
            hash_matches = []
          csv_dict['expect_hashes'] = hash_matches
          csv_dict['false_neg'] = ''
          csv_dict['false_pos'] = ''
          csv_dict['incorrect'] = ''
          if csv_dict['expect_rows'] != csv_dict['actual_rows']:
            csv_dict['false_neg'] = \
                [v for v in csv_dict['expect_rows'] if \
                  'FAILED' not in csv_dict['actual_rows'] and \
                  v not in csv_dict['actual_rows']]
            csv_dict['false_pos'] = \
                [v for v in csv_dict['actual_rows'] if v not in \
                  csv_dict['expect_rows'] and v != 'FAILED']
          if len(csv_dict['actual_hashes']) > 0 and \
             len(csv_dict['expect_hashes']) > 0:
            actual_hash_dict = {}
            expect_hash_dict = {}
            incorrect_rows = []
            for k, v in zip(csv_dict['expect_rows'], csv_dict['expect_hashes']):
              expect_hash_dict[k] = v
            for k, v in zip(csv_dict['actual_rows'], csv_dict['actual_hashes']):
              actual_hash_dict[k] = v
            for k in expect_hash_dict:
              if k not in actual_hash_dict:
                continue
              elif expect_hash_dict[k] != actual_hash_dict[k]:
                incorrect_rows.append(k)
            csv_dict['incorrect'] = incorrect_rows
          if len(csv_dict['false_neg']) > 0:
            LOGGER.warning(('%d false negatives for query %s on %s and %s rows '
                            '(%d ground truth results)'),
                len(csv_dict['false_neg']), csv_dict['where_clause'], 
                csv_dict['cols'], csv_dict['db_size'],
                len(csv_dict['expect_rows']))
            csv_dict['false_neg_cnt'] = len(csv_dict['false_neg'])
          if len(csv_dict['false_pos']) > 0:
            LOGGER.warning(('%d false positives for query %s on %s and %s rows '
                            '(%d ground truth results)'),
                len(csv_dict['false_pos']), csv_dict['where_clause'], 
                csv_dict['cols'], csv_dict['db_size'],
                len(csv_dict['expect_rows']))
            csv_dict['false_pos_cnt'] = len(csv_dict['false_pos'])
          if len(csv_dict['incorrect']) > 0 :
            LOGGER.warning(('%d incorrect hashes for query %s on %s and %s rows '
                            '(%d ground truth results)'),
                len(csv_dict['incorrect']), csv_dict['where_clause'], 
                csv_dict['cols'], csv_dict['db_size'],
                len(csv_dict['expect_rows']))
            csv_dict['incorrect_cnt'] = len(csv_dict['incorrect'])
          csv_dict['actual_rows'] = '|'.join(csv_dict['actual_rows'])
          csv_dict['expect_rows'] = '|'.join(csv_dict['expect_rows'])
          csv_dict['actual_hashes'] = '|'.join(csv_dict['actual_hashes'])
          csv_dict['expect_hashes'] = '|'.join(csv_dict['expect_hashes'])
          csv_dict['false_neg'] = '|'.join(csv_dict['false_neg'])
          csv_dict['false_pos'] = '|'.join(csv_dict['false_pos'])
          csv_dict['incorrect'] = '|'.join(csv_dict['incorrect'])
      else:
        LOGGER.warning('No ground truth for query %s', csv_dict['where_clause'])
      csv_file.writerow(csv_dict)
      return 1

    # Parse each complete record with record_func, which will update csv_dicts
    LOGGER.info('Processed %d test results', parse_queries(f, record_func))
    f.close()
    csv_f.close()
    LOGGER.info('Wrote results to %s', full_path) 
    print

if __name__ == '__main__':
    main()
