import datetime
import argparse
import logging
import getpass
import csv
import sys
import os

LOGGER = logging.getLogger(__name__)

def parse_args(extra_args, ssh_user):
  if not ssh_user:
    LOGGER.warning('--user was not defined; using current user for default '
                   'remote destinations')
    ssh_user = getpass.getuser()
  parser = argparse.ArgumentParser('TA1 test execution remote-runner options')
  parser.add_argument('-p', '--performer', dest = 'performer',
      required = True, help = 'Name of performer under test')
  parser.add_argument('-t', '--test_case', dest = 'test_case',
      required = True, help = 'Name of test case being exected. In SPAR, test '
                              'script files are typically named '
                              '<performer>-<database>-<test_case>; this should '
                              'only define test_case, with performer and '
                              'database being defined by other command line '
                              'options.')

  parser.add_argument('--hosts-file', dest = 'hosts_file',
      required = True,
      help = 'Location of hosts file with available remote hosts')
  parser.add_argument('--client-host-th', dest = 'client_host_th',
      required = True, help = 'IP address or host name of client host; must '
                              'match an entry in the hosts file')
  parser.add_argument('--client-host-perf', dest = 'client_host_perf',
      required = True, help = 'IP address or host name of client host; must '
                              'match an entry in the hosts file')
  parser.add_argument('--server-host-th', dest = 'server_host_th',
      required = True, help = 'IP address or host name of server host; must '
                              'match an entry in the hosts file')
  parser.add_argument('--server-host-perf', dest = 'server_host_perf',
      required = True, help = 'IP address or host name of server host; must '
                              'match an entry in the hosts file')
  parser.add_argument('--tp-hosts', dest = 'tp_hosts',
      help = 'Comma separated list of IP addresses or host names of third '
             'party hosts, *without any spaces*; must match an entry in the '
             'hosts file. Hosts will be used in the order that they are '
             'provided.')
  parser.add_argument('--enable-eventmsg', dest = 'eventmsg', default = False,
      action='store_true', help = 'Enables event message reporting in SUT')

  parser.add_argument('-D', '--database', dest = 'database',
      required = True, help = 'MariaDB database under test')
  parser.add_argument('--db-user', dest = 'db_user',
      help = 'User for accessing MariaDB')
  parser.add_argument('--db-password', dest = 'db_password',
      help = 'Password for accessing MariaDB')
  parser.add_argument('--db-schema-file', dest = 'db_schema_file',
      help = 'Location of database schema file')
  parser.add_argument('--stopwords-file', dest = 'stopwords_file',
      help = 'Location of database schema file')

  parser.add_argument('--local-trunk-dir', dest = 'local_trunk_dir',
      help = 'Location of SPAR trunk checkout on local host; note all binaries '
             'should be compiled and in the trunk\'s bin directory')
  parser.add_argument('--remote-bin-dir', dest = 'remote_bin_dir',
      default = '/home/%s/spar-testing/rr_bin' % ssh_user,
      help = 'Location where binaries will be executed from on remote hosts')
  parser.add_argument('--remote-config-dir', dest = 'remote_config_dir',
      default = '/home/%s/spar-testing/rr_config' % ssh_user,
      help = 'Location where config files will be stored on remote hosts')
  parser.add_argument('--local-test-dir', dest = 'local_test_dir',
      default = os.path.expanduser('~/spar-testing/tests'),
      help = 'Location where test scripts are stored on local host')
  parser.add_argument('--remote-test-dir', dest = 'remote_test_dir',
      default = '/home/%s/spar-testing/tests' % ssh_user,
      help = 'Location where test scripts will be stored on remote host')
  parser.add_argument('--local-results-dir', dest = 'local_results_dir',
      default = os.path.expanduser('~/spar-testing/results'),
      help = 'Location where results will be generated on local host')
  parser.add_argument('--remote-results-dir', dest = 'remote_results_dir',
      default = '/home/%s/spar-testing/results' % ssh_user,
      help = 'Location where results will be generated on remote host')
  parser.add_argument('--local-debug-dir', dest = 'local_debug_dir',
      default = os.path.expanduser('~/spar-testing/debug'),
      help = 'Location where debug data will be generated on local host')
  parser.add_argument('--remote-debug-dir', dest = 'remote_debug_dir',
      default = '/home/%s/spar-testing/debug' % ssh_user,
      help = 'Location where debug data will be generated on remote host')

  parser.add_argument('-d', '--debug', dest = 'debug', default = False,
      action='store_true', help = 'Runs test in debug mode with extra output')

  extra_args_list = extra_args.split()
  extra_options = parser.parse_args(extra_args_list)

  # Validate/ensure the existence of required directories
  # TODO expand paths?
  assert os.path.isdir(extra_options.local_trunk_dir)
  assert os.path.isdir(extra_options.local_test_dir)
  assert os.path.isdir(extra_options.local_results_dir)
  assert os.path.isdir(extra_options.local_debug_dir)
  assert os.path.isfile(extra_options.hosts_file)
  assert os.path.isfile(extra_options.db_schema_file)
  assert os.path.isfile(extra_options.stopwords_file)

  # Update options as needed for convenience
  extra_options.test_name = '%s-%s-%s' % (extra_options.performer,
                                          extra_options.database,
                                          extra_options.test_case)
  extra_options.local_test_dir = os.path.join(extra_options.local_test_dir,
                                              extra_options.performer,
                                              extra_options.database)
  extra_options.remote_test_dir = os.path.join(extra_options.remote_test_dir,
                                               extra_options.performer,
                                               extra_options.database)
  current_time = datetime.datetime.today().strftime("%y%m%d_%H%M%S")
  extra_options.local_results_dir = \
    os.path.join(extra_options.local_results_dir,  
                 extra_options.performer,
                 extra_options.database,
                 "%s-%s" % (extra_options.test_case, current_time))
  os.makedirs(extra_options.local_results_dir)
  LOGGER.info('Local results will be stored in %s', 
              extra_options.local_results_dir)
  extra_options.remote_results_dir = \
    os.path.join(extra_options.remote_results_dir,  
                 extra_options.performer,
                 extra_options.database,
                 "%s-%s" % (extra_options.test_case, current_time))
  LOGGER.info('Remote results will be stored in %s', 
              extra_options.remote_results_dir)

  # Parse hosts file and update client and server host names/IP addresses
  csv_r = csv.DictReader(open(extra_options.hosts_file))
  ip_to_host_map = {}
  host_to_ip_map = {}
  for d in csv_r:
    ip_to_host_map[d['ip']] = d['host']
    host_to_ip_map[d['host']] = d['ip']

  # Determine client host name
  if extra_options.client_host_th in ip_to_host_map:
    extra_options.client_ip_th = extra_options.client_host_th
    extra_options.client_host_th = ip_to_host_map[extra_options.client_ip_th]
  elif extra_options.client_host_th in host_to_ip_map:
    extra_options.client_ip_th = host_to_ip_map[extra_options.client_host_th]
  else:
    LOGGER.error('Could not find information in %s on %s.',
                 extra_options.hosts_file,
                 extra_options.client_host_th) 
    sys.exit(1)
  if extra_options.client_host_perf in ip_to_host_map:
    extra_options.client_ip_perf = extra_options.client_host_perf
    extra_options.client_host_perf = ip_to_host_map[extra_options.client_ip_perf]
  elif extra_options.client_host_perf in host_to_ip_map:
    extra_options.client_ip_perf = host_to_ip_map[extra_options.client_host_perf]
  else:
    LOGGER.error('Could not find information in %s on %s.',
                 extra_options.hosts_file,
                 extra_options.client_host_perf) 
    sys.exit(1)

  # Determine server host name
  if extra_options.server_host_th in ip_to_host_map:
    extra_options.server_ip_th = extra_options.server_host_th
    extra_options.server_host_th = ip_to_host_map[extra_options.server_ip_th]
  elif extra_options.server_host_th in host_to_ip_map:
    extra_options.server_ip = host_to_ip_map[extra_options.server_host_th]
  else:
    LOGGER.error('Could not find information in %s on %s.',
                 extra_options.hosts_file,
                 extra_options.server_host_th) 
    sys.exit(1)
  if extra_options.server_host_perf in ip_to_host_map:
    extra_options.server_ip_perf = extra_options.server_host_perf
    extra_options.server_host_perf = ip_to_host_map[extra_options.server_ip_perf]
  elif extra_options.server_host_perf in host_to_ip_map:
    extra_options.server_ip_perf = host_to_ip_map[extra_options.server_host_perf]
  else:
    LOGGER.error('Could not find information in %s on %s.',
                 extra_options.hosts_file,
                 extra_options.server_host_perf) 
    sys.exit(1)

  # Determine third party host names
  # TODO make sure this is being handled robustly...havent tested a lot,
  # esepcially with exec_ta1_test.sh
  if extra_options.tp_hosts and len(extra_options.tp_hosts) > 0:
    extra_options.tp_hosts = extra_options.tp_hosts.split(',')
    new_tp_hosts = []
    extra_options.tp_ips = []
    for tp in extra_options.tp_hosts:
      if tp in ip_to_host_map:
        extra_options.tp_ips.append(tp)
        new_tp_hosts.append(ip_to_host_map[tp])
      elif tp in host_to_ip_map:
        extra_options.tp_ips.append(host_to_ip_map[tp])
        new_tp_hosts.append(tp)
      else:
        LOGGER.error('Could not find information in %s on %s.',
                     extra_options.hosts_file, tp)
        sys.exit(1)
    extra_options.tp_hosts = new_tp_hosts

  return extra_options
