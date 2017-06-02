from datetime import datetime
import argparse
import logging
import csv
import os
import re

# Parses tcpdump output in a variety of ways. Relies on tcpdump being called as
# such (excludes router status and SSH traffic):
#   tcpdump -nneSvvvtttts 0 not arp and not stp and not ether proto 0x88cc
#   and not ether[20:2] == 0x2000 and not port 22 -l ... > output_file
# In other words, the actual stdout of tcpdump is an input to this file, and
# relies on the above level of verbosity and filtering.

LOGGER = logging.getLogger(__name__)
# Regex strings and patterns
TIMESTAMP_PATT_STR = '(?:[0-9]{2,4}?\-?){3} (?:[0-9]{2}:?){3}\.[0-9]{6}'
MAC_ADDRESS_PATT_STR = '(?:[0-9a-f]{2}:?){6}'
IP_ADDRESS_PATT_STR = '(?:[0-9]{2,3}?\.?){4}\.[0-9]+'
# TODO(njhwang) currently only handles TCP and UDP
# TODO(njhwang) research other parts of TCP packets to make sure nothing else
# important
TCPDUMP_IP_LINE_1_PATT = re.compile( \
    ('^(?P<time>%s) %s > %s, ethertype IPv4 \(0x0800\), '
     'length (?P<len>[0-9]+): \(tos 0x[0-9a-f]+, ttl [0-9]+, id [0-9]+, '
     'offset [0-9]+, flags \[.*\], '
     'proto (?P<proto>(?:TCP)|(?:UDP)) \([0-9]+\), length [0-9]+\)$') % \
    (TIMESTAMP_PATT_STR, MAC_ADDRESS_PATT_STR, MAC_ADDRESS_PATT_STR))
TCPDUMP_TCP_LINE_2_PATT = re.compile( \
    ('^\s*(?P<src>%s) > (?P<dst>%s): Flags \[.*\], '
     'cksum 0x[0-9a-f]{4} \(.*\), seq (?:[0-9]+:?)+, (?:ack [0-9]+, )?'
     'win [0-9]+, (?:options \[.*\], )?length [0-9]+$') % \
    (IP_ADDRESS_PATT_STR, IP_ADDRESS_PATT_STR))
TCPDUMP_UDP_LINE_2_PATT = re.compile( \
    ('^\s*(?P<src>%s) > (?P<dst>%s): \[.*\] UDP, length [0-9]+$') % \
    (IP_ADDRESS_PATT_STR, IP_ADDRESS_PATT_STR))

# Converts the tcpdump output file to a *.csv with the following columns:
#  ts: timestamp (UNIX epoch)
#  len: byte length of packet
#  src: source IP and port
#  dst: destination IP and port
# TODO(njhwang) currently not really used, but could be useful in some other
# application
def file_to_dict(input_file, output_dir):
  assert os.path.isfile(input_file)
  assert os.path.isdir(output_dir)

  # Create csv writer
  output_file = 'parsed_tcpdump'
  full_path = os.path.join(output_dir, output_file + '.csv')
  csv_f = open(full_path, 'w')
  csv_cols = ['ts', 'len', 'src', 'dst']
  csv_file = csv.DictWriter(csv_f, csv_cols, extrasaction='ignore')
  csv_file.writeheader()

  f = open(input_file, 'r')
  line = f.readline()
  while len(line) > 0:
    if len(line.strip()) == 0:
      line = f.readline()
      continue
    m = TCPDUMP_IP_LINE_1_PATT.match(line)
    assert m, 'Could not match tcpdump output for IP info: ' + line
    timestamp = float(datetime.strptime(m.group('time'),
                                        '%Y-%m-%d %H:%M:%S.%f'). \
                      strftime('%s.%f'))
    results = {'ts': timestamp, 
              'len' : int(m.group('len'))}
    line = f.readline()
    m = TCPDUMP_TCP_LINE_2_PATT.match(line)
    assert m, line
    results.update({'src' : m.group('src'),
                    'dst' : m.group('dst')})
    csv_file.writerow(results)
    line = f.readline()
  f.close()
  csv_f.close()

# Converts the tcpdump output file to a *.csv file that only contains
# 'quantiles' that summarize when a sequence of packets began and end. A
# quantile is defined by the query_delay amount provided; in other words,
# quantiles must be separated by at least query_delay microseconds. The source
# and destination in the tcpdump output must match either client_ip or
# server_ip, or else parsing will fail. The *.csv file will have the following
# columns:
#  start: start timestamp (UNIX epoch)
#  end: end timestamp (UNIX epoch)
#  sent: # of sent bytes (from the perspective of client_ip)
#  recv: # of received bytes (from the perspective of client_ip)
def quantize_file(input_file, output_dir, query_delay, client_ip, server_ip):
  assert os.path.isfile(input_file)
  assert os.path.isdir(output_dir)
  assert query_delay > 0

  # Create csv writer
  output_file = 'quantized_tcpdump'
  full_path = os.path.join(output_dir, output_file + '.csv')
  csv_f = open(full_path, 'w')
  csv_cols = ['start', 'end', 'sent', 'recv']
  csv_file = csv.DictWriter(csv_f, csv_cols, extrasaction='ignore')
  csv_file.writeheader()

  f = open(input_file, 'r')
  line = f.readline()
  last_ts = None
  start_ts = None
  written = False
  curr_sent_bytes = 0
  curr_recv_bytes = 0
  while len(line) > 0:
    if len(line.strip()) == 0:
      line = f.readline()
      continue
    m = TCPDUMP_IP_LINE_1_PATT.match(line)
    assert m, 'Could not match tcpdump output for IP info: ' + line
    timestamp = float(datetime.strptime(m.group('time'),
                                        '%Y-%m-%d %H:%M:%S.%f'). \
                      strftime('%s.%f'))
    if not last_ts:
      last_ts = start_ts = timestamp
      written = False
    elif (timestamp - last_ts)*1000000 >= query_delay:
      csv_file.writerow({'start' : start_ts,
                         'end' : last_ts,
                         'sent' : curr_sent_bytes,
                         'recv' : curr_recv_bytes})
      written = True
      last_ts = start_ts = timestamp
      curr_sent_bytes = curr_recv_bytes = 0
    else:
      last_ts = timestamp
      written = False
    length = int(m.group('len'))
    line = f.readline()
    m = TCPDUMP_TCP_LINE_2_PATT.match(line)
    assert m, 'Could not match tcpdump output for TCP info: ' + line
    src_str = m.group('src')
    src_ip = src_str[:src_str.rfind('.')]
    if src_ip == client_ip:
      curr_sent_bytes += length
    elif src_ip == server_ip:
      curr_recv_bytes += length
    else:
      LOGGER.error('Source %s did not match given client or server IP', src_ip)
      sys.exit(1)
    dst_str = m.group('dst')
    dst_ip = dst_str[:dst_str.rfind('.')]
    assert dst_ip == client_ip or dst_ip == server_ip
    line = f.readline()
  if not written:
    csv_file.writerow({'start' : start_ts,
                       'end' : last_ts,
                       'sent' : curr_sent_bytes,
                       'recv' : curr_recv_bytes})
  f.close()
  csv_f.close()

def main():
  log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                'CRITICAL': logging.CRITICAL}

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input_file', dest = 'input_file',
          type = str, required = True,
          help = 'tcpdump output file')
  parser.add_argument('-o', '--output_dir', dest = 'output_dir',
          type = str, required = False,
          help = 'output directory for *.csv file')
  parser.add_argument('-q', '--query_delay', dest = 'query_delay',
          type = int, required = True,
          help = 'delay between queries in microseconds; note you will likely '
                 'want to make this slightly less than the actual delay in '
                 'used in test scripts to properly isolate any network '
                 'traffic used to perform set up tasks before the first query')
  parser.add_argument('-c', '--client_ip', dest = 'client_ip',
          type = str, required = True,
          help = 'IP address of client workstation (where tcpdump should '
                 'have been run from)')
  parser.add_argument('-s', '--server_ip', dest = 'server_ip',
          type = str, required = True,
          help = 'IP address of server workstation')
  parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
          type = str, choices = log_levels.keys(),
          help = 'only output log messages with the given severity or '
          'above')

  options = parser.parse_args()

  logging.basicConfig(
          level = log_levels[options.log_level],
          format = '%(levelname)s: %(message)s')

  assert os.path.isfile(options.input_file)
  assert options.query_delay > 0

  quantize_file(options.input_file, options.output_dir, options.query_delay, 
                options.client_ip, options.server_ip)

if __name__ == '__main__':
    main()
