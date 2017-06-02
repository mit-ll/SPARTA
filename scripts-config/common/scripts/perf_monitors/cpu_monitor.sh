#!/bin/bash

# Launches collectl to monitor CPU usage and saves its 
# output to the specified file. Tailored for
# usage on the SPAR testbed.
# 
# Arguments:
# $1 - Rate at which to poll the system, in seconds (.001 for milliseconds, etc)
# $2 - Output file
#
# TODO: Make this a proper script with help options, etc
#
# An explanation of the arguments:
# -sC: subsys=cpu, detailed form
# -i $1: interval
# --filename $2: filename to write to
# -P plot mode (roughly csv mode)
# -om2z: options=
# 	m: report milliseconds in output
#	2: 2 decimal places in output
# 	z: don't compress output
# --sep ,: use comma as delimeter


# note that there is a --nice options that can be used if necessary

collectl -sC -i $1 --filename $2 -P -om2z --sep ,


