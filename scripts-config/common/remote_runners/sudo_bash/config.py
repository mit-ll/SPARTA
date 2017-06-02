#*****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ni24039
#  Description:        Runs a set of apt-get installs locally and remotely.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  10 Jan 2013   ni24039        Original Version
# *****************************************************************

import copy

# TODO make sure current user is lincoln
LOCALHOST  = "localhost"
HOST_INFO_FILE = "../../config/host_info.txt"

HOSTS = []
for line in open(HOST_INFO_FILE):
  items = line.strip().split(' ')
  HOSTS.append(items[0])

# Base component
base_component = Component()
base_component.name = "sudo-bash-task-runner"
base_component.start_index = 1
base_component.executable = "sudo-bash-task.sh"
base_component.base_dir = "/home/lincoln/spar-config/"
base_component.args = [options.ssh_pass]

HOSTS.append(LOCALHOST)
for host in HOSTS:
  c = copy.deepcopy(base_component)
  c.host = host
  if host != LOCALHOST:
    c.files = {c.executable : c.executable}
  config.add_component(c)
