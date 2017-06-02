import argparse
from datetime import datetime
import logging
import csv
import re
import os

LOGGER = logging.getLogger(__name__)
FILE_PREFIXES = ['CallRemoteScript', 'server-harness']
TIME_PATTERN = re.compile('\[(?P<time>[0-9]+\.[0-9]+)\] (?P<data>.*)')
CRS_PATTERN = re.compile('\[[0-9]+\.[0-9]\] CallRemoteScript (?P<script>.*)')

def main():
  log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                'CRITICAL': logging.CRITICAL}

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input_dir', dest = 'input_dir',
          type = str, required = True,
          help = 'Directory containing test results.')
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

  assert os.path.isdir(options.input_dir)
  assert os.path.isdir(options.output_dir)

  csv_output = []
  output_file = 'CallRemoteScripts-parsed-%s' % \
                datetime.today().strftime('%Y%m%d_%H%M%S')

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

    LOGGER.info('Processing file %s...', full_path)
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
      m = TIME_PATTERN.match(line)
      if not m:
        line = f.readline()
        continue
      csv_output.append({'time' : m.group('time'),
                         'data' : m.group('data')})
      line = f.readline()

    full_path = os.path.join(options.output_dir, output_file + '.csv')
    csv_f = open(full_path, 'w')
    csv_file = csv.DictWriter(csv_f, ['time', 'data'], extrasaction='ignore')
    csv_file.writeheader()
    csv_file.writerows(csv_output)

if __name__ == '__main__':
    main()
