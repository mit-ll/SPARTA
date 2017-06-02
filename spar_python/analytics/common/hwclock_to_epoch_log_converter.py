# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Tim Meunier
#  Description:        Script to normalize timestamps in log files.
# *****************************************************************
import argparse
import logging

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.analytics.common.log_parser_util as log_parser_util

LOGGER = logging.getLogger(__name__)

def main():
    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                  'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                  'CRITICAL': logging.CRITICAL}

    parser = argparse.ArgumentParser('Create copy of a log file with '
        'all relative time stamps mapped to global system time.')
    parser.add_argument('-i', '--input_file', dest = 'input_file',
        required = True, help = 'Location of the input file')
    parser.add_argument('-o', '--output_file', dest = 'output_file',
        required = True, help = 'Location of the output file')
    parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
        type = str, choices = log_levels.keys(),
        help = 'Only output log messages with the given severity or '
        'above')
    options = parser.parse_args()

    logging.basicConfig(
        level = log_levels[options.log_level],
        format = '%(levelname)s: %(message)s')

    read_f = open(options.input_file)
    write_f = open(options.output_file, 'w')

    log_parser = log_parser_util.LogParserUtil()
    log_parser.hwclock_to_epoch_log_converter(read_f, write_f)

    write_f.close()
    read_f.close()

if __name__ == '__main__':
    main()
