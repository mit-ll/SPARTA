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

import subprocess
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

popen_args = [options.executable,]
popen_args.extend(options.args.split(' '))
process = subprocess.Popen(
        popen_args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)

line = process.stdout.readline()
assert line == 'READY\n'

start = datetime.datetime.now()
for i in xrange(options.num_trials):
    process.stdin.write('GO\n')
    process.stdin.flush()
    line = ''
    while line != 'READY\n':
        line = process.stdout.readline()

end = datetime.datetime.now()
NUM_MICROS_PER_SECOND = 1000000.0
elapsed = end - start
elapsed_sec = (elapsed.seconds + 
        float(elapsed.microseconds) / NUM_MICROS_PER_SECOND)

print ('Ran %s trials in %s seconds. Throughput: %s per second' %
        (options.num_trials, elapsed_sec,
            float(options.num_trials) / elapsed_sec))


