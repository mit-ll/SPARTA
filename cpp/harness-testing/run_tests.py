# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Run the Python and C++ tests with a variety of different
#                      parameters.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  30 May 2012   omd            Original Version
# *****************************************************************

import re
import subprocess
import copy

bytes = [0, 10, 100, 1000, 10000, 100000]
TEST_REPEATS = 10
CPP_THROUGHPUT = 'harness-testing/opt/silly-throughput'
C_API_THROUGHPUT = 'harness-testing/opt/c-style-throughput'
PYTHON_THROUGHPUT = 'harness-testing/silly-throughput.py'
ASYNC_PY_THROUGHPUT = 'harness-testing/silly-async-throughput.py'
EVENT_LOOP_THROUGHPUT = 'harness-testing/opt/event-loop-throughput'
CPP_CLIENT = 'harness-testing/opt/silly-client'

CPP_RESULTS_FILE = 'cpp_results.csv'
PY_RESULTS_FILE = 'py_results.csv'
ASYNC_PY_RESULTS_FILE = 'async_py_results.csv'

def do_run(command, data_re, output_file, title):
    print '=====================\n'
    print title
    f = open(output_file, 'w+')
    f.write('bytes,time,throughput\n')
    print 'bytes,time,throughput'
    for b in bytes:
        command_with_args = copy.copy(command)
        command_with_args.extend(['-a', '-b' + str(b)])
        for i in xrange(TEST_REPEATS):
            result = subprocess.Popen(command_with_args,
                    stdout = subprocess.PIPE).communicate()[0]
            m = data_re.match(result)
            if m != None:
                result_str = '%s,%s,%s' % (b, m.group(1), m.group(2))
                print 'Result:', result_str
                f.write(result_str)
                f.write('\n')
    f.close()
    
# async_cmd = ['python', ASYNC_PY_THROUGHPUT, '-e', CPP_CLIENT]
# async_re = re.compile(r'^.* in ([\d.]+) seconds.*: ([\d.]+) per second')
# do_run(async_cmd, async_re, ASYNC_PY_RESULTS_FILE, "Async Python")

re_event = re.compile(r'^.* in ([\d.]+) seconds.*: ([\d.]+) per second.')
event_cmd = [EVENT_LOOP_THROUGHPUT, '-e', CPP_CLIENT]
do_run(event_cmd, re_event, "event_loop_results.csv",
       "Event Loop")

re_c_api = re.compile(r'^.* in ([\d.]+) seconds.*: ([\d.]+) per second.')
c_api_cmd = [C_API_THROUGHPUT, '-e', CPP_CLIENT]
do_run(c_api_cmd, re_c_api, "c_api_results.csv", "C API")

re_cpp = re.compile(r'^.* in ([\d.]+) seconds.*: ([\d.]+) per second.')
cpp_cmd = [CPP_THROUGHPUT, '-e', CPP_CLIENT]
do_run(cpp_cmd, re_cpp, "cpp_stdout_buffer_results.csv", "C++")

re_py = re.compile(r'^.* in ([\d.]+) seconds.*: ([\d.]+) per second')
py_cmd = ['python', PYTHON_THROUGHPUT, '-e', CPP_CLIENT]
do_run(py_cmd, re_py, PY_RESULTS_FILE, "Python")
