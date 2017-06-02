import logging
import re
import os

LOGGER = logging.getLogger(__name__)
TIME_PATTERN    = re.compile('\[[0-9]+\.[0-9]+\].+')
SENT_PATTERN    = re.compile('Command (?P<cmd_id>[0-9]+) sent')
COMMAND_PATTERN = re.compile('Command: \[\[SELECT (?P<cols>.+) FROM main '
                             'WHERE (?P<query>.*)\]\], '
                             'command id: (?P<cmd_id>[0-9]+)')
RESULTS_PATTERN = re.compile('Command (?P<cmd_id>[0-9]+) complete\. Results:')

# Returns a pair containing a long line's time stamp and message. Will fail if
# the expected timestamp format is not found.
def _split_timestamp(line):
  parts = line.split(' ', 1)
  if LOGGER.getEffectiveLevel() >= logging.DEBUG:
    assert len(parts) == 2, 'Not a valid timestamped line'
    assert parts[0].startswith('[') and parts[0].endswith(']'), \
      'Not a valid timestamped line'
  return (parts[0].strip('[]'), parts[1])

# Updates a dict that has dicts as values. If the key does not exist, a new dict
# value is created, otherwise the existing dict is updated.
def _update_dict_in_dict(d, key, value):
  if d.has_key(key):
    d[key].update(value)
  else:
    d[key] = value

# Main function that parses a log file, and applies record_func to each complete
# record of query information. record_func can be used to do any number of
# things, including updating a sqlite database, or writing out results to a
# *.csv file. Returns the number of *new* records processed.
def parse_queries(f, record_func):
  num_records = 0

  temp_query_dict = {}
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
    LOGGER.debug('Parsing %s...', line)
    # Should be a timestamped line
    (ts, res) = _split_timestamp(line)

    # Look for sent pattern
    m = SENT_PATTERN.match(res)
    if m:
      cmd_id = m.group('cmd_id')
      _update_dict_in_dict(temp_query_dict, cmd_id, 
          {'command_id' : cmd_id, 
           'command_time' : ts})
      line = f.readline()
      continue

    # Else, look for command pattern
    m = COMMAND_PATTERN.match(res)
    if m:
      cmd_id = m.group('cmd_id')
      _update_dict_in_dict(temp_query_dict, cmd_id, 
        {'command_id' : cmd_id,
         'cols' : m.group('cols'),
         'query' : m.group('query')})
      # Some tests did not have a 'sent' message, and this timestamp must
      # suffice
      if 'command_time' not in temp_query_dict[cmd_id]:
        _update_dict_in_dict(temp_query_dict, cmd_id, 
          {'command_time' : ts})
      line = f.readline()
      continue

    # Else, look for results pattern
    m = RESULTS_PATTERN.match(res)
    if m:
      cmd_id = m.group('cmd_id')
      matches = []
      # Read lines until all matches have been captured
      while True:
        line = f.readline().strip()
        # Results are done if we reach EOF or have an empty line
        if len(line) == 0 or len(line.strip()) == 0:
          line = f.readline()
          break
        # If the line is timestamped, we want to keep the line for the next
        # iteration of the parser
        elif TIME_PATTERN.match(line):
          break
        parts = line.split(' ')
        if LOGGER.getEffectiveLevel() >= logging.DEBUG:
          assert len(parts) <= 2
        # If results indicate failure, read rest of failure message before
        # breaking
        if parts[0] == 'FAILED':
          LOGGER.warning('Command %s had FAILED results', cmd_id)
          while True:
            line = f.readline().strip()
            if line == 'ENDFAILED':
              break
          matches.append('FAILED')
        # Else, add relevant data if there is both a row and a hash
        elif len(parts) == 2:
          matches.append((int(parts[0]), parts[1]))
        # Else, add only row
        else:
          matches.append(int(parts[0]))
      # Numerically sort matches by row
      matches = sorted(matches)
      _update_dict_in_dict(temp_query_dict, cmd_id, 
          {'command_id' : cmd_id,
           'results_time' : ts, 
           'results' : matches})
      query_info = temp_query_dict[cmd_id]
      # Attempt inserting a new row into the ground_truth table
      if 'query' not in query_info:
        LOGGER.warning('No evidence of command %s ever being sent',
            query_info['command_id'])
        print query_info
        del temp_query_dict[cmd_id]
        continue
      # Apply record_func to the complete results, and update num_records based
      # on whether record_func processes the results as new
      num_records += record_func(query_info)
      # Conserve memory by deleting the unneeded entry in temp_query_dict
      del temp_query_dict[cmd_id]
      continue
    # If no pattern was matched, just read another line
    line = f.readline()

  if len(temp_query_dict) > 0:
    LOGGER.warning('Not all queries returned results!')
  return num_records

