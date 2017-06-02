#!/bin/bash

# Launches collectl to monitor RAM usage and saves its 
# output to the specified file. Tailored for
# usage on the SPAR testbed.
# 
# This script provides detailed memory usage of the entire system
# and is *not* broken down by process.
# 
# ram_by_proc.sh will break down memory used by process, 
# but in less detail, and is not capable of sub-second measurements.
#
# This script should be run frequently to measure memory usage over time,
# and ram_by_proc.sh should be run occasionally, so that memory usage of
# non-performer processes can be subtracted.  ram_by_proc.sh does not need
# to be run as frequently because memory usage of non-performer processes
# should be fairly constant.
#
# Arguments:
# $1 - Rate at which to poll the system, in seconds (.001 for milliseconds, etc)
# $2 - Output file
#
# TODO: Make this a proper script with help options, etc
#
# An explanation of the arguments:
# -sm: subsys=memory
# -i $1: interval
# --filename $2: filename to write to
# -P plot mode (roughly csv mode)
# -om2z: options=
# 	m: report milliseconds in output
# 	z: don't compress output
# --sep ,: use comma as delimeter


# note that there is a --nice option that can be used if necessary

collectl -sm -i $1 --filename $2 -P -omz --sep ,


