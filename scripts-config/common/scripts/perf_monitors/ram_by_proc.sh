#!/bin/bash

# Launches top and saves its 
# output to the specified file. Tailored for
# usage on the SPAR testbed.
#
# The ram_monitor.sh script is capable of measuring
# RAM usage at sub-second intervals.
#
# However, it measures total system memory usage
# and is not broken down by process.
# is capable of measuring sub-second intervals.
# 
# This script measures memory usage by process,
# but is not capable of sub-second intervals.
#
# This script should be used to determine the memory usage
# of other processes (the kernel, the test harness, etc), 
# all of which should have fairly constant memory usage.
# The usage of these processes can be subtracted from the 
# values gathered by ram_monitor.sh
#
# Arguments:
# $1 - Rate at which to poll the system, in seconds (10+ second intervals recommended)
# $2 - Output file
#
# TODO: Make this a proper script with help options, etc
#
# An explanation of the arguments:
# -b: batch mode
# -d: delay between measurements

top -b -d $1 > $2



