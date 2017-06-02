# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Python version of the silly throughput test 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  29 May 2012   omd            Original Version
# *****************************************************************

import asyncproc
import datetime
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-e', '--executable', dest='executable',
        help = 'Path to the client program')
parser.add_option('-a', '--args', dest='args',
        help = 'Command line arguments to pass to --executable')
parser.add_option('-n', '--num_trials', type='int', default=10000,
        dest='num_trials', help='The number of iterations to run')
(options, args) = parser.parse_args()

process_args = [options.executable,]
process_args.extend(options.args.split(' '))
process = asyncproc.Process(process_args)

line = ''
while not line.strip() == 'READY':
    line = process.read()
line = ''

start = datetime.datetime.now()
for i in xrange(options.num_trials):
    process.write('GO\n')
    found_ready = False
    while not found_ready:
        data = process.read()
        # Note: This isn't very robust. If a read returns part of the READY
        # token (e.g. REA) we don't buffer it and won't notice when the rest of
        # the token appears next time.
        lines = data.split('\n')
        for l in lines:
            if l == 'READY':
                found_ready = True
                break

end = datetime.datetime.now()
NUM_MICROS_PER_SECOND = 1000000.0
elapsed = end - start
elapsed_sec = (elapsed.seconds + 
        float(elapsed.microseconds) / NUM_MICROS_PER_SECOND)

print ('Ran %s trials in %s seconds. Throughput: %s per second' %
        (options.num_trials, elapsed_sec,
            float(options.num_trials) / elapsed_sec))


