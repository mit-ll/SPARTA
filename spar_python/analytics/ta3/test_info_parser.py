from dateutil import parser as dateparser
import argparse
import logging
import csv
import os
import re

LOGGER = logging.getLogger(__name__)
TESTGEN_LOG_PATT = re.compile('test\-gen.*\.txt')
TESTGEN_SH_PATT = re.compile('test\-gen.*\.sh')
GLOBAL_VAR_PATT = re.compile('(?P<key>[A-Z_]+) = (?P<value>.*)')
BASH_VAR_PATT = re.compile('(?P<key>[a-z_]+)=(?P<value>.*)')
TP_NAME_PATT = re.compile('tp.name = "third\-party\-(?P<entity>.*)"')
NUM_CORES_PATT = re.compile('(?P<entity>[a-z]+)\.num_cores = (?P<value>[0-9]+)')
RR_LOG_START_PATT = re.compile('Script started on (?P<start_time>.*)')
RR_LOG_END_PATT = re.compile('Script done on (?P<end_time>.*)')
NUM_PUBS_PATT = re.compile('[0-9]+ publications')

def _update_csv_row(csv_row, key, value):
  assert type(csv_row) is dict
  if key == 'test_script':
    key = 'testname'
  elif key == 'disjunction_ratio':
    key = 'disjunction_prob'
  elif key == 'match_rate':
    key = 'unique_matches'
  elif key == 'publication_timeout':
    key = 'pub_wait'
  if key in csv_row:
    curr_value = csv_row[key]
    if curr_value.startswith('~'):
      if curr_value[1:] != value.split()[1]:
        LOGGER.warning('Conflicting values for %s -> %s or %s?',
            key, curr_value, value)
        csv_row[key] = '%s?%s' % (curr_value, value)
      else:
        csv_row[key] = value
    elif value.startswith('~'):
      if value[1:] != curr_value.split()[1]:
        LOGGER.warning('Conflicting values for %s -> %s or %s?',
            key, curr_value, value)
        csv_row[key] = '%s?%s' % (curr_value, value)
    elif 'prob' in key:
      assert float(curr_value) == float(value)
    elif curr_value != value:
      LOGGER.warning('Conflicting values for %s -> %s or %s?',
          key, curr_value, value)
      csv_row[key] = '%s?%s' % (curr_value, value)
  else:
    csv_row[key] = value

def main():
  log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                'CRITICAL': logging.CRITICAL}

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input_dir', dest = 'input_dir',
          type = str, required = True,
          help = 'Directory containing test results.')
  parser.add_argument('-p', '--performer', dest = 'performer',
          type = str, required = True,
          help = 'Performer being processed.')
  parser.add_argument('-o', '--output_dir', dest = 'output_dir',
          type = str, required = True,
          help = 'Test results in CSV format will be written to this '
                 'directory.')
  parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
          type = str, choices = log_levels.keys(),
          help = 'Only output log messages with the given severity or '
          'above')

  options = parser.parse_args()

  logging.basicConfig(
          level = log_levels[options.log_level],
          format = '%(levelname)s: %(message)s')

  input_dir = options.input_dir.rstrip('/')
  output_dir = options.output_dir.rstrip('/')
  performer = options.performer
  assert os.path.isdir(input_dir), \
      '%s must be a directory' % input_dir
  assert os.path.isdir(output_dir)
  base_path = os.path.basename(input_dir)
  if '_' not in base_path:
    if '-' in base_path:
      test_name = base_path[:base_path.rfind('-')]
    else:
      test_name = base_path
  else:
    test_name = base_path[:base_path.find('_')]

  LOGGER.debug('Parsing files in %s', input_dir)

  csv_row = {}
  csv_row['performer'] = performer
  csv_row['testname'] = test_name
  csv_row['testdir'] = base_path
  file_prefixes = ['%s-%s_muddler.py' % (performer, test_name),
                   '%s_config.py' % performer,
                   'test-gen_%s_log.txt' % test_name,
                   'test-gen_%s.sh' % test_name,
                   'rr_log.txt', test_name]

  file_found = {}

  # Process each file in options.input_dir
  for path in os.listdir(input_dir): 
    full_path = os.path.join(input_dir, path)

    # Skip directories or any unexpected file names
    if os.path.isdir(full_path):
      if path == test_name or \
          (test_name.startswith('TC') and path.startswith('TC')):
        test_dir_full_path = None
        for test_dir_path in os.listdir(full_path):
          if path == test_name or \
              (test_name.startswith('TC') and test_dir_path.startswith('TC')):
            test_dir_full_path = os.path.join(full_path, test_dir_path)
        if not test_dir_full_path:
          continue
        else:
          full_path = test_dir_full_path

    filename = os.path.basename(full_path)
    found_prefix = False
    for prefix in file_prefixes:
      file_found[prefix] = False
    for prefix in file_prefixes:
      if filename.startswith(prefix):
        file_found[prefix] = found_prefix = True
        break
    if 'muddler' not in filename and 'test-gen' not in filename and \
        not (test_name.startswith('TC') and filename.startswith('TC')) and\
        not found_prefix:
      continue

    last_tp_name = None
    f = open(full_path, 'r')
    line = f.readline()
    while True:
      # EOF
      if len(line) == 0:
        break
      # readline() keeps the EOL char(s), so strip them off
      line = line.strip()
      # Skip blank lines
      if len(line) == 0:
        line = f.readline()
        continue
      if 'muddler' in filename:
        if line == "# These shouldn't need to change across tests" or \
           line == "# Load host information from HOST_INFO_FILE":
          break
        m = GLOBAL_VAR_PATT.match(line)
        if m:
          key = m.group('key').lower()
          value = m.group('value').replace('"', '')
          if key == 'payload_generation':
            parts = value.split(' ')
            _update_csv_row(csv_row, 'payload_seed', parts[0])
            _update_csv_row(csv_row, 'payload_size', parts[1])
          elif key == 'publication_delay':
            parts = value.split(' ')
            _update_csv_row(csv_row, 'publication_delay_type', parts[0])
            if 'NO_DELAY' not in line:
              _update_csv_row(csv_row, 'publication_delay_length', parts[1])
          elif key == 'payload_sizes':
            parts = value[1:-1].split(',')
            for i in range(len(parts)):
              parts[i] = parts[i][:parts[i].find('#')].strip().strip(']')
            _update_csv_row(csv_row, 'payload_size', '|'.join(parts))
          elif not key.endswith('_dir') and key != 'host_info_file' \
              and key != 'payload_seed':
            _update_csv_row(csv_row, key, value)
      elif 'config' in filename:
        m = TP_NAME_PATT.match(line)
        if m:
          last_tp_name = m.group('entity')
        else:
          m = NUM_CORES_PATT.match(line)
          if m:
            if m.group('entity') == 'tp':
              _update_csv_row(csv_row, '%s_cores' % last_tp_name, 
                              m.group('value'))
            else:
              _update_csv_row(csv_row, '%s_cores' % m.group('entity'), 
                              m.group('value'))
      elif 'rr_log' in filename:
        m = RR_LOG_START_PATT.match(line)
        if m:
          _update_csv_row(csv_row, 'start_time', 
              dateparser.parse(m.group('start_time')). \
                  strftime('%m/%d/%y %H:%M:%S'))
        else:
          m = RR_LOG_END_PATT.match(line)
          if m:
            _update_csv_row(csv_row, 'end_time', 
                dateparser.parse(m.group('end_time')). \
                    strftime('%m/%d/%y %H:%M:%S'))
          elif 'PAYLOAD_SEED' in line:
            _update_csv_row(csv_row, 'payload_seed', line.split()[1])
      elif TESTGEN_LOG_PATT.match(filename):
        if 'Random seed' in line:
          _update_csv_row(csv_row, 'datagen_seed', line.split()[4])
        elif 'possible fields' in line:
          _update_csv_row(csv_row, 'num_fields', line.split()[1])
        elif 'clients' in line:
          _update_csv_row(csv_row, 'num_clients', line.split()[1])
        elif 'subs per client' in line:
          if 'Average of' in line:
            _update_csv_row(csv_row, 'subs_per_client', '~' + line.split()[3])
          elif 'Average' in line:
            _update_csv_row(csv_row, 'subs_per_client', '~' + line.split()[2])
          else:
            _update_csv_row(csv_row, 'subs_per_client', line.split()[1])
        elif 'subs will be disjunctions' in line:
          _update_csv_row(csv_row, 'disjunction_prob',
              repr(float(line.split()[1].strip('~%'))/100))
        elif 'disjoined terms will be thresholds' in line:
          _update_csv_row(csv_row, 'threshold_prob',
              repr(float(line.split()[1].strip('~%'))/100))
        elif 'terms on number fields will be inequalities' in line:
          _update_csv_row(csv_row, 'inequality_prob',
              repr(float(line.split()[1].strip('~%'))/100))
        elif 'inequalities on number fields will be \'greater than\'' in line:
          _update_csv_row(csv_row, 'gt_prob',
              repr(float(line.split()[1].strip('~%'))/100))
        elif 'inequalities on number fields will be inclusive' in line:
          _update_csv_row(csv_row, 'inclusive_prob',
              repr(float(line.split()[1].strip('~%'))/100))
        elif 'conjunctions or disjunctions will be negated' in line:
          _update_csv_row(csv_row, 'negation_prob',
              repr(float(line.split()[1].strip('~%'))/100))
        elif 'terms in each conjunction' in line:
          if 'Average of' in line:
            _update_csv_row(csv_row, 'conjunction_size', '~' + line.split()[3])
          elif 'Average' in line:
            _update_csv_row(csv_row, 'conjunction_size', '~' + line.split()[2])
          else:
            _update_csv_row(csv_row, 'conjunction_size', line.split()[1])
        elif 'terms in each disjunction' in line:
          if 'Average of' in line:
            _update_csv_row(csv_row, 'disjunction_size', '~' + line.split()[3])
          elif 'Average' in line:
            _update_csv_row(csv_row, 'disjunction_size', '~' + line.split()[2])
          else:
            _update_csv_row(csv_row, 'disjunction_size', line.split()[1])
        elif NUM_PUBS_PATT.match(line[6:].strip()):
          _update_csv_row(csv_row, 'num_pubs', line.split()[1])
        elif 'conjunctions matched per publication' in line:
          if 'Average of' in line:
            _update_csv_row(csv_row, 'unique_matches', '~' + line.split()[3])
          else:
            _update_csv_row(csv_row, 'unique_matches', line.split()[1])
        elif 'replication factor' in line:
          _update_csv_row(csv_row, 'replication_factor', line.split()[-1])
        elif 'overgeneration factor' in line:
          _update_csv_row(csv_row, 'overgeneration_factor', line.split()[-1])
        elif 'conjunctive subscriptions' in line:
          _update_csv_row(csv_row, 'generated_conj', line.split()[2])
        elif 'Wasted' in line:
          _update_csv_row(csv_row, 'wasted_conj', line.split()[2])
      elif TESTGEN_SH_PATT.match(filename):
        m = BASH_VAR_PATT.match(line)
        if m:
          key = m.group('key').lower()
          if key != 'rand_seed' and not key.endswith('_dir') and \
             not key.endswith('_path') and key != 'generator_cmd':
            value = m.group('value')
            if value.find('#') >= 0:
              value = value[:value.find('#')].strip().strip("'\"")
            else:
              value = value.strip().strip("'\"")
            if key == 'performer':
              value = value.lower()
            _update_csv_row(csv_row, key, value)
      elif filename == test_name or \
          (filename.startswith('TC') and test_name.startswith('TC')):
        if line.startswith('PublishScript') or \
            line.startswith('PublishAndModifySubscriptionsScript'):
          parts = line.split()
          if parts[2] == 'EXPONENTIAL_DELAY':
            _update_csv_row(csv_row, 'publication_delay_type', parts[2])
            _update_csv_row(csv_row, 'publication_delay_length', parts[3])
            _update_csv_row(csv_row, 'payload_seed', parts[4])
            if 'payload_size' not in csv_row:
              _update_csv_row(csv_row, 'payload_size', parts[5])
          elif parts[2] == 'NO_DELAY':
            _update_csv_row(csv_row, 'publication_delay_type', parts[2])
            _update_csv_row(csv_row, 'payload_seed', parts[3])
            if 'payload_size' not in csv_row:
              _update_csv_row(csv_row, 'payload_size', parts[4])
      line = f.readline()

  for prefix in file_found:
    if not file_found[prefix]:
      LOGGER.debug('%s missing from input directory', prefix)

  csv_cols = ['testname', 'testdir', 'performer', 'start_time', 'end_time', 
              'debug_enabled', 'core_pin', 'server_cores', 'client_cores', 
              'num_fields', 'num_clients', 'num_pubs', 
              'publication_delay_type', 'publication_delay_length', 
              'payload_seed', 'payload_size', 'subs_per_client', 
              'unique_matches', 'loaded_subs', 'test_unsubs', 
              'percent_background_subs', 'num_update_sets', 
              'num_pubs_per_conj', 'loaded_payload_size', 'background_wait', 
              'pre_modify_wait', 'modify_wait', 'datagen_seed', 
              'conjunction_size', 'disjunction_size', 'disjunction_prob', 
              'negation_prob', 'inequality_prob', 'gt_prob', 'inclusive_prob', 
              'threshold_prob', 'keep_exhausted_fields', 'replication_factor', 
              'overgeneration_factor', 'generated_conj', 'wasted_conj', 
              'timestamp_period', 'client_host_model', 'client_targeter', 
              'create_new_scripts', 'end_wait', 'pub_wait', 'rs_cores',
              'ts_cores', 'ds_cores', 'ara_cores']
  csv_path = os.path.join(output_dir, 'test_info.csv')
  if not os.path.isfile(csv_path):
    csv_f = open(csv_path, 'w')
    csv_file = csv.DictWriter(csv_f, csv_cols)
    csv_file.writeheader()
  else:
    csv_f = open(csv_path, 'a')
    csv_file = csv.DictWriter(csv_f, csv_cols)
  csv_file.writerow(csv_row)

if __name__ == '__main__':
    main()
