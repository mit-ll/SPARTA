#!/bin/bash

# Note that this script name could not have the word 'java' in it, as the pkill
# command would attempt to kill this script as well...
# Also note that this will generate hs_err_pid*.log files whereever the Java
# executables were invoked from.
pkill -11 java
