import os.path
import copy
import os

# =============================================================================
# Base component
# NOTE: Put any component settings here that will be common to all components.
base_component = Component()
base_component.start_index = 1
base_component.args = []
base_component.files = {}
base_component.wait = True
# =============================================================================

# =============================================================================
# Client SUT
client = copy.deepcopy(base_component)
client.name = 'client'
client.host = extra_options.client_host_th
client.args.extend([ \
  '--host', extra_options.server_host_perf, 
  '--password', extra_options.db_password,
  '--database', extra_options.database])
if extra_options.eventmsg:
  client.args.extend(['-e'])
if client.host == 'localhost' or client.host == '127.0.0.1':
  client.executable = os.path.join(extra_options.local_trunk_dir,
                                   'bin/ta1-baseline-client')
else:
  client.executable = 'ta1-baseline-client'
  client.base_dir = extra_options.remote_bin_dir
  client.files[os.path.join(extra_options.local_trunk_dir, 
                            'bin/ta1-baseline-client')] = \
    'ta1-baseline-client'
# =============================================================================
config.add_component(client)

# =============================================================================
# Server SUT
server = copy.deepcopy(base_component)
server.name = 'server'
server.host = extra_options.server_host_th
db_schema_base = os.path.basename(extra_options.db_schema_file)
stopwords_base = os.path.basename(extra_options.stopwords_file)
server.args.extend([ \
  '--host', extra_options.server_host_perf, 
  '--password', extra_options.db_password,
  '--database', extra_options.database])
if extra_options.eventmsg:
  server.args.extend(['-e'])
if server.host == 'localhost' or server.host == '127.0.0.1':
  server.executable = os.path.join(extra_options.local_trunk_dir,
                                   'bin/ta1-baseline-server')
  server.args.extend([ \
    '--schema-file', extra_options.db_schema_file,
    '--stop-words', extra_options.stopwords_file])
else:
  server.executable = 'ta1-baseline-server'
  server.base_dir = extra_options.remote_bin_dir
  server.files[os.path.join(extra_options.local_trunk_dir,
                            'bin/ta1-baseline-server')] = \
    'ta1-baseline-server'
  db_schema_dest = os.path.join(extra_options.remote_config_dir, 
                                db_schema_base)
  stopwords_dest = os.path.join(extra_options.remote_config_dir, 
                                stopwords_base)
  server.files[extra_options.db_schema_file] = db_schema_dest
  server.files[extra_options.stopwords_file] = stopwords_dest
  server.args.extend([ \
    '--schema-file', db_schema_dest,
    '--stop-words', stopwords_dest])
# =============================================================================
config.add_component(server)
