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
# =============================================================================

# =============================================================================
# Base component
# NOTE Put any component settings here that will be common to all components.
base_component = Component()
base_component.start_index = 1
base_component.executable = "/usr/bin/java"
base_component.args = ["-jar"]
# =============================================================================

# =============================================================================
# Third party component
# NOTE Include as many third party components as needed. The configuration for
# each one should look like the following. The name must start with
# 'third-party-'.
#  tp = copy.deepcopy(base_component)
#  tp.name = "third-party-X"
#  tp.host = 
#  tp.args.extend()
#  tp.files[] =
#  tp.num_cpus = 
#  config.add_component(tp)
# =============================================================================

# =============================================================================
# Publisher component
server = copy.deepcopy(base_component)
server.name = "server"
# NOTE Everything below should be updated as needed per SUT requirements.
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
server.host = "localhost"
server.args.extend(["PublishingBroker.jar",
                    "-f", "../../config/metadata_schema.csv",
                    "-h", "127.0.0.1"])
server.num_cores = 1
# =============================================================================
config.add_component(server)

# =============================================================================
# Subscriber component
client = copy.deepcopy(base_component)
client.name = "client"
# NOTE client.host will be automatically populated by muddler. Whatever you set
# this to won't matter. client.host will eventually be set based on
# client.num_cpus, how many clients are specified in the muddler, and which
# model names from the host info file are allowed to run client SUTs.
client.host = "TBD"
# NOTE Everything below should be updates as needed per SUT requirements.
#
# If "%n" is present anywhere in client.args, it will be replaced with a
# unique integer representing the client SUT's ID. Take advantage of this when a
# SUT needs a unique argument of some sort. Otherwise, each SUT will receive the
# same arguments. client.args should NOT contain any semi-colons or double
# quotes.
client.args.extend(["SubscribingClient.jar", "-n", "%n",
                    "-h", "127.0.0.1"])
client.num_cores = 1
# =============================================================================
config.add_component(client)
