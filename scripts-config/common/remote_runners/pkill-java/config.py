# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ni24039
#  Description:        Runs a script to kill all Java instances on remote
#                      machines
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  10 Jan 2013   ni24039        Original Version
# *****************************************************************

import copy

# TODO make sure current user is lincoln
# TODO make sure archive directory exists?
HOST_INFO_FILE = "../../config/host_info.txt"

HOSTS = []
for line in open(HOST_INFO_FILE):
  items = line.strip().split(' ')
  HOSTS.append(items[0])

# Base component
base_component = Component()
base_component.name = "pkill-jvm"
base_component.start_index = 1
base_component.executable = "pkill-jvm.sh"
base_component.base_dir = "/home/lincoln/spar-config/"

for host in HOSTS:
  c = copy.deepcopy(base_component)
  c.host = host
  c.files = {c.executable : c.executable}
  config.add_component(c)
