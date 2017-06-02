# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ni24039
#  Description:        Config file to be used with remote_runner.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  10 Jan 2013   ni24039        Original Version
# *****************************************************************

import copy

# =============================================================================
# NOTE Put any convenience variables you may need in this area.
HOME_DIR = "/home/" + options.ssh_user + "/"
# =============================================================================

# =============================================================================
# Base component
# NOTE Put any component settings here that will be common to all components.
base_component = Component()
# =============================================================================

tp = copy.deepcopy(base_component)
tp.name = "server-cleanup"
tp.host = "10.10.99.219"
tp.start_index = 1
tp.executable = "clean-producer.sh"
tp.base_dir = HOME_DIR
tp.files[HOME_DIR + tp.executable] = tp.executable
tp.num_cores = 1
config.add_component(tp)

HOST_INFO_FILE = "../../common/config/host_info_R210_only.txt"

HOSTS = []
for line in open(HOST_INFO_FILE):
  items = line.strip().split(' ')
  HOSTS.append(items[0])

for host in HOSTS:
  c = copy.deepcopy(base_component)
  c.name = "client-cleanup"
  c.executable = "clean-consumer.sh"
  c.base_dir = HOME_DIR
  c.start_index = 1
  c.host = host
  c.files = {HOME_DIR + c.executable : c.executable}
  c.num_cores = 1
  config.add_component(c)
