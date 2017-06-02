import datetime
import argparse
import logging
import os.path
import copy
import sys
import os

LOGGER= logging.getLogger(__name__)

def muddle(config):

  # Base component
  base_component = Component()
  base_component.args = []

  new_comps = []

  for comp in config.all_components():

    if comp.name == 'client':
      # Muddle client component
      client_harness = copy.deepcopy(base_component)
      client_harness.name = "client-harness"
      client_harness.host = extra_options.client_host_th
      client_harness.args.extend([ \
       "-p", comp.executable,
       "-a", ' '.join(comp.args),
       "--listen_addr", extra_options.client_ip_th,
       "-n", extra_options.test_name])
      if extra_options.debug:
        client_harness.args.extend([ \
         "-u",
         "-v"])
      client_harness.start_index = comp.start_index
      client_harness.base_dir = comp.base_dir
      client_harness.wait = comp.wait
      if comp.host == 'localhost' or comp.host == '127.0.0.1':
        client_harness.executable = os.path.join(extra_options.local_trunk_dir,
                                                 "bin/ta1-client-harness")
        client_harness.args.extend([ \
          "-t", os.path.join(extra_options.local_test_dir, 
                             '%s.ts' % extra_options.test_name),
          "--test_log_dir", extra_options.local_results_dir])
        if extra_options.debug:
          client_harness.args.extend([ \
           "-d", extra_options.local_debug_dir])
      else:
        client_harness.executable = "ta1-client-harness"
        remote_test_script_path = os.path.join(extra_options.remote_test_dir, 
                                               '%s.ts' % extra_options.test_name)
        remote_test_queries_path = os.path.join(extra_options.remote_test_dir,
                                                'queries')
        remote_test_mods_path = os.path.join(extra_options.remote_test_dir,
                                             'mods')
        local_test_script_path = os.path.join(extra_options.local_test_dir, 
                                              '%s.ts' % extra_options.test_name)
        local_test_queries_path = os.path.join(extra_options.local_test_dir,
                                               'queries')
        local_test_mods_path = os.path.join(extra_options.local_test_dir,
                                            'mods')
        client_harness.args.extend([ \
          "-t", remote_test_script_path,
          "--test_log_dir", extra_options.remote_results_dir])
        if extra_options.debug:
          client_harness.args.extend([ \
           "-d", extra_options.remote_debug_dir])
        client_harness.files = copy.deepcopy(comp.files)
        client_harness.files[os.path.join(extra_options.local_trunk_dir, 
                                          "bin/ta1-client-harness")] = \
          "ta1-client-harness"
        client_harness.files[local_test_script_path] = \
            remote_test_script_path
        client_harness.files.update( \
          util.recursive_files_dict(local_test_queries_path, 
                                    remote_test_queries_path))
        client_harness.files.update( \
          util.recursive_files_dict(local_test_mods_path, 
                                    remote_test_mods_path))
        client_harness.files[extra_options.local_results_dir] = \
            extra_options.remote_results_dir
      new_comps.append(client_harness)
      LOGGER.debug('Processed client component.')
      LOGGER.debug('Executable: %s', client_harness.executable)
      LOGGER.debug('Arguments: %s', client_harness.args)
     
    elif comp.name == 'server':
      # Muddle server component
      server_harness = copy.deepcopy(base_component)
      server_harness.name = "server-harness"
      server_harness.host = extra_options.server_host_th
      server_harness.args.extend([ \
        "-p", comp.executable, \
        "-a", ' '.join(comp.args),
        "--connect_addr", extra_options.client_ip_th,
        "-n", extra_options.test_name])
      if extra_options.debug:
        server_harness.args.extend([ \
         "-u",
         "-v"])
      server_harness.start_index = comp.start_index
      server_harness.base_dir = comp.base_dir
      server_harness.wait = comp.wait
      if comp.host == 'localhost' or comp.host == '127.0.0.1':
        server_harness.executable = os.path.join(extra_options.local_trunk_dir,
                                                 "bin/ta1-server-harness")
        server_harness.args.extend([ \
          "--test_log", os.path.join(extra_options.local_results_dir, 
                                     "server-harness.log")])
        if extra_options.debug:
          server_harness.args.extend([ \
           "-d", extra_options.local_debug_dir])
      else:
        server_harness.executable = "ta1-server-harness"
        server_harness.args.extend([ \
          "--test_log", os.path.join(extra_options.remote_results_dir, 
                                     "server-harness.log")])
        if extra_options.debug:
          server_harness.args.extend([ \
           "-d", extra_options.remote_debug_dir])
        server_harness.files = copy.deepcopy(comp.files)
        server_harness.files[os.path.join(extra_options.local_trunk_dir, 
                                          "bin/ta1-server-harness")] = \
          "ta1-server-harness"
        server_harness.files[extra_options.local_results_dir] = \
            extra_options.remote_results_dir
      new_comps.append(server_harness)
      LOGGER.debug('Processed server component.')
      LOGGER.debug('Executable: %s', server_harness.executable)
      LOGGER.debug('Arguments: %s', server_harness.args)

    else:
      # Muddle third party components
      assert comp.name.startswith('third-party')
      new_comps.append(comp)

  config.clear_components()
  for comp in new_comps:
    # TODO(njhwang) could not get the addition of a 'script' command working.
    # The below works fine if comp.wait = False, but that precludes us from
    # using this to queue up many tests and also capture the stderr of the test
    # harness and SUTs. If comp.wait = True, a Bash script is created that
    # exeutes the component and waits on the PID after writing the PID to a file
    # that remote_runner can poll for remotely. But the combination of 1) using
    # a screen session to 2) execute this Bash script which 3) executes the
    # 'script' command in the background causes nothing to happen, even though
    # executing the script outside of a screen session works fine. The best
    # thing I can think of right now is to just invoke remote_runner with unique
    # screen names for each test case, so these will be kept around for us to
    # investigate after tests are run.
    #if '/' not in comp.executable:
    #  comp.executable = './%s' % comp.executable
    #arg_index = comp.args.index('-a') + 1
    #assert "'" not in comp.args[arg_index]
    #comp.args[arg_index] = "'%s'" % comp.args[arg_index]
    #comp.args = ['-c', '%s %s' % (comp.executable, ' '.join(comp.args))]
    #if comp.host == 'localhost' or comp.host == '127.0.0.1':
    #  comp.args.extend([ \
    #        os.path.join(extra_options.local_results_dir, 
    #                 '%s.script' % comp.name)])
    #else:
    #  comp.args.extend([ \
    #        os.path.join(extra_options.remote_results_dir, 
    #                 '%s.script' % comp.name)])
    #comp.executable = '/usr/bin/script'
    config.add_component(comp)
