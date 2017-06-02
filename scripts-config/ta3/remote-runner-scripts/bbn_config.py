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
BASE_DIR   = HOME_DIR + "spar-testing/"
# =============================================================================

# =============================================================================
# Base component
# NOTE Put any component settings here that will be common to all components.
base_component = Component()
# TODO(njhwang) seems like this doesn't work for large # of files...taking too
# long to hash files and diff them
#base_component.files.update(util.recursive_files_dict(HOME_DIR + "test", HOME_DIR + "test"))
#base_component.files.update(util.recursive_files_dict(HOME_DIR + "extern", HOME_DIR + "extern"))
#base_component.files.update(util.recursive_files_dict(HOME_DIR + "jmiracl", HOME_DIR + "jmiracl"))
#base_component.files.update(util.recursive_files_dict(HOME_DIR + "p3s-1.0", HOME_DIR + "p3s-1.0"))
#base_component.files.update(util.recursive_files_dict(HOME_DIR + "includedir", HOME_DIR + "includedir"))
#base_component.files.update(util.recursive_files_dict(HOME_DIR + "libdir", HOME_DIR + "libdir"))
#base_component.files.update(util.recursive_files_dict(HOME_DIR + ".m2", HOME_DIR + ".m2"))
# =============================================================================

# =============================================================================
# Third party component
# NOTE Include as many third party components as needed. The configuration for
# each one should look like the following. The name must start with
# 'third-party-'.
tp = copy.deepcopy(base_component)
tp.name = "third-party-ds"
tp.host = "10.10.99.218"
tp.start_index = 1
tp.executable = "./run-DS.sh"
tp.files[HOME_DIR + "run-DS.sh"] = "run-DS.sh"
# TODO these shouldn't be core-pinned at all
tp.num_cores = 10
config.add_component(tp)

tp = copy.deepcopy(base_component)
tp.name = "third-party-rs"
tp.host = "10.10.99.221"
tp.start_index = 2
tp.executable = "./run-RS.sh"
tp.files[HOME_DIR + "run-RS.sh"] = "run-RS.sh"
# TODO these shouldn't be core-pinned at all
tp.num_cores = 10
config.add_component(tp)

tp = copy.deepcopy(base_component)
tp.name = "third-party-ts"
tp.host = "10.10.99.214"
tp.start_index = 3
tp.executable = "./run-TS.sh"
tp.files[HOME_DIR + "run-TS.sh"] = "run-TS.sh"
# TODO these shouldn't be core-pinned at all
tp.num_cores = 5
config.add_component(tp)

tp = copy.deepcopy(base_component)
tp.name = "third-party-ara"
tp.host = "10.10.99.214"
tp.start_index = 4
tp.executable = "./run-ARA.sh"
tp.files[HOME_DIR + "run-ARA.sh"] = "run-ARA.sh"
# TODO these shouldn't be core-pinned at all
tp.num_cores = 5
config.add_component(tp)

# =============================================================================

# =============================================================================
# Publisher component
server = copy.deepcopy(base_component)
server.name = "server"
# NOTE Everything below should be updates as needed per SUT requirements.
#
# server.host should be updated as desired as the testing environment
# dictates. The muddler file that is run with this config file will reference a
# particular 'host info' file located in scripts-config/common/config/. The host
# info file will contain a list of all workstations in the environment with the
# following space-separated information:
# IP address, number of cores, model name, whether the system is hyperthreaded
#
# server.host should be set to one of the IP addresses in the host info file
# that will be used.
server.host = "10.10.99.219"
server.start_index = 5
server.executable = "./run-producer.sh"
server.files["/home/lincoln/extern/ta3/bin/run-producer.sh"] = "run-producer.sh"
server.num_cores = 2
# =============================================================================
config.add_component(server)

# =============================================================================
# Subscriber component
client = copy.deepcopy(base_component)
client.name = "client"
# NOTE client.host will be automatically populated by muddler. Whatever you set
# this to won't matter. client.host will eventually be set based on
# client.num_cores, how many clients are specified in the muddler, and which
# model names from the host info file are allowed to run client SUTs.
client.start_index = 6
client.host = "TBD"
client.executable = "./run-SUB-lincoln.sh"
# NOTE Everything below should be updates as needed per SUT requirements.
#
# If "%n" is present anywhere in client.args, it will be replaced with a
# unique integer representing the client SUT's ID. Take advantage of this when a
# SUT needs a unique argument of some sort. Otherwise, each SUT will receive the
# same arguments. client.args should NOT contain any semi-colons or double
# quotes.
client.files[HOME_DIR + "run-SUB-lincoln.sh"] = "run-SUB-lincoln.sh"
client.args = ["%n"]
client.num_cores = 1
# =============================================================================
config.add_component(client)
