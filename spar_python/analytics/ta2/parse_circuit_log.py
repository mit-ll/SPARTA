# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Tim Meunier
#  Description:        Parser for the performer encrypted circuit
#                      log file.  Results are stored in a DB.
#                      
# *****************************************************************

import argparse
import logging
import re
import collections
import sqlite3

import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta2.ta2_database as ta2_database
import spar_python.report_generation.ta2.ta2_schema as ta2_schema
import spar_python.analytics.common.log_parser_util as log_parser_util

class CircuitParser(log_parser_util.LogParserUtil):
    '''Class for parsing encrypted circuit logs'''

    file_rex = '.+'
    test_rex = 'TEST: (?P<testname>[^ ]+) (.+)'
    perf_rex = 'PERFORMER: (?P<performer>.+)'
    test_file_rex = '(?P<file_type>(KEYPARAMS)|(CIRCUIT)|(INPUT)): (?P<file_path>.+)'
    time_rex = 'TIME: (?P<date>[0-9-]{10}) (?P<time>[0-9:]{8})'
    recovery_rex = 'RECOVERY'
    data_rex = '(?P<token>[A-Z ]+): (?P<value>.+)'
    tokens = {ta2_schema.PERKEYGEN_TABLENAME :
                  ['KEYGEN', 'KEYTRANSMIT', 'KEYSIZE'],
              ta2_schema.PERINGESTION_TABLENAME :
                  ['INGESTION', 'CIRCUITTRANSMIT'],
              ta2_schema.PEREVALUATION_TABLENAME :
                  ['ENCRYPT', 'INPUTTRANSMIT', 'INPUTSIZE', 'EVAL', \
                   'OUTPUTTRANSMIT', 'OUTPUTSIZE', 'DECRYPTED RESULT', \
                   'DECRYPT']}
    # This is mostly for looking up a column name that corresponds to a token
    # but it is useful for the other columns as well since the data is the same
    # but column names might be different across tables.
    column_map = {ta2_schema.PERKEYGEN_TABLENAME :
                      {'KEYGEN' : ta2_schema.PERKEYGEN_LATENCY,
                       'KEYTRANSMIT' : ta2_schema.PERKEYGEN_TRANSMITLATENCY,
                       'KEYSIZE' : ta2_schema.PERKEYGEN_KEYSIZE,
                       'performer' : ta2_schema.PERKEYGEN_PERFORMERNAME,
                       'testname' : ta2_schema.PERKEYGEN_TESTNAME,
                       'timestamp' : ta2_schema.PERKEYGEN_TIMESTAMP,
                       'pid' : ta2_schema.PERKEYGEN_PID,
                       'status' : ta2_schema.PERKEYGEN_STATUS,
                       'recovery' : ta2_schema.PERKEYGEN_RECOVERY},
                  ta2_schema.PERINGESTION_TABLENAME :
                      {'INGESTION' : ta2_schema.PERINGESTION_LATENCY,
                       'CIRCUITTRANSMIT' : ta2_schema.PERINGESTION_TRANSMITLATENCY,
                       'performer' : ta2_schema.PERINGESTION_PERFORMERNAME,
                       'testname' : ta2_schema.PERINGESTION_TESTNAME,
                       'timestamp' : ta2_schema.PERINGESTION_TIMESTAMP,
                       'cid' : ta2_schema.PERINGESTION_CID,
                       'status' : ta2_schema.PERINGESTION_STATUS,
                       'recovery' : ta2_schema.PERINGESTION_RECOVERY},
                  ta2_schema.PEREVALUATION_TABLENAME :
                      {'ENCRYPT' : ta2_schema.PEREVALUATION_ENCRYPTIONLATENCY,
                       'INPUTTRANSMIT': ta2_schema.PEREVALUATION_INPUTTRANSMITLATENCY,
                       'INPUTSIZE' : ta2_schema.PEREVALUATION_INPUTSIZE,
                       'EVAL' : ta2_schema.PEREVALUATION_EVALUATIONLATENCY,
                       'OUTPUTTRANSMIT' : ta2_schema.PEREVALUATION_OUTPUTTRANSMITLATENCY,
                       'OUTPUTSIZE' : ta2_schema.PEREVALUATION_OUTPUTSIZE,
                       'DECRYPTED RESULT': ta2_schema.PEREVALUATION_OUTPUT,
                       'DECRYPT' : ta2_schema.PEREVALUATION_DECRYPTIONLATENCY,
                       'performer' : ta2_schema.PEREVALUATION_PERFORMERNAME,
                       'testname' : ta2_schema.PEREVALUATION_TESTNAME,
                       'timestamp' : ta2_schema.PEREVALUATION_TIMESTAMP,
                       'iid' : ta2_schema.PEREVALUATION_IID,
                       'correctness' : ta2_schema.PEREVALUATION_CORRECTNESS,
                       'status' : ta2_schema.PEREVALUATION_STATUS,
                       'recovery' : ta2_schema.PEREVALUATION_RECOVERY}}


    def __init__(self, output_db):
        '''Setup variables used my many class memeber functions.'''
        self.logger = logging.getLogger(__name__)
        self.file_pattern = re.compile(self.file_rex)
        self.output_db = output_db
        self.results = collections.defaultdict(list)
        self.table_name = 'UNKNOWN'

    def parse_log(self, log):
        '''Parse data from log files and populate results dict.'''

        test_pattern = re.compile(self.test_rex)
        perf_pattern = re.compile(self.perf_rex)
        test_file_pattern = re.compile(self.test_file_rex)
        time_pattern = re.compile(self.time_rex)
        recovery_pattern = re.compile(self.recovery_rex)
        data_pattern = re.compile(self.data_rex)

        self.results.clear()
        self.table_name = 'UNKNOWN'
        recovery = False
        data_row = {}
        timestamp = '0000-00-00 00:00:00'
        performer =  'UNKNOWN'
        testname = 'UNKNOWN'

        for line in log:
            # Strip EOL
            line = line.strip()
            # Skip blank lines
            if len(line) == 0:
                continue
            self.logger.debug(line)

            test_match = test_pattern.match(line)
            perf_match = perf_pattern.match(line)
            test_file_match = test_file_pattern.match(line)
            time_match = time_pattern.match(line)
            recovery_match = recovery_pattern.match(line)
            data_match = data_pattern.match(line)
            if (test_match):
                # Found a testcase line
                self.logger.debug('Matched a testcase line')
                testname = test_match.group('testname')
            if (perf_match):
                # Found a performer name
                self.logger.debug('Matched a performer line')
                performer = perf_match.group('performer')
            elif (test_file_match):
                # Found a file line
                file_type = test_file_match.group('file_type')
                file_path = test_file_match.group('file_path')
                # Get id
                file_id = self.get_id_from_filename(file_path)
                # Write row to results
                if (self.table_name != 'UNKNOWN'):
                    # Make sure all the required tokens were found
                    self.check_tokens(data_row)
                    data_row[self.column_map[self.table_name]['timestamp']] = \
                        timestamp
                    data_row[self.column_map[self.table_name]['performer']] = \
                        performer
                    data_row[self.column_map[self.table_name]['testname']] = \
                        testname
                    #print "ROW ", data_row
                    self.results[self.table_name].append(data_row)
                # Start a new row
                data_row = {}
                if (file_type == 'KEYPARAMS'):
                    # Found a params line
                    self.logger.debug('Matched a keyparams line')
                    self.table_name = ta2_schema.PERKEYGEN_TABLENAME
                    data_row[self.column_map[self.table_name]['pid']] = file_id
                elif (file_type == 'CIRCUIT'):
                    # Found a circuit line
                    self.logger.debug('Matched a circuit line')
                    self.table_name = ta2_schema.PERINGESTION_TABLENAME
                    data_row[self.column_map[self.table_name]['cid']] = file_id
                elif (file_type == 'INPUT'):
                    # Found an input line
                    self.logger.debug('Matched an input line')
                    self.table_name = ta2_schema.PEREVALUATION_TABLENAME
                    data_row[self.column_map[self.table_name]['iid']] = file_id
                # If this is a recovery log, write to DB and clear flag
                if recovery:
                    data_row['recovery'] = 1
                    recovery = False
            elif (time_match):
                # Found timestamp
                self.logger.debug('Matched a timestamp line')
                date = time_match.group('date')
                time = time_match.group('time')
                ### TODO: Format how we want it
                timestamp = date + ' ' + time
            elif (recovery_match):
                # Set recovery to true for next line
                recovery = True
            elif (data_match):
                # Found data
                self.logger.debug('Matched a data line')
                # Get token and value
                token = data_match.group('token')
                value = data_match.group('value')
                if (self.table_name == 'UNKNOWN'):
                    self.logger.warning('Found token %s before finding a '\
                                        'valid file.  Skipping token.', token)
                # Is the token expected?
                elif self.is_token_valid(token):
                    # Store for the DB
                    self.logger.debug('Found valid token %s, with value %s', \
                                      token, value)
                    data_row[self.column_map[self.table_name][token]] = value
                else:
                    self.logger.warning('Found an unexpected token: %s', token)
            else:
                # Found an unrecognized line
                self.logger.warning('Skipping unrecognized pattern: %s', line)

        # Write last row to results
        if (self.table_name != 'UNKNOWN'):
            # Make sure all the required tokens were found
            self.check_tokens(data_row)
            data_row[self.column_map[self.table_name]['timestamp']] = \
                timestamp
            data_row[self.column_map[self.table_name]['performer']] = \
                performer
            data_row[self.column_map[self.table_name]['testname']] = \
                testname
            self.results[self.table_name].append(data_row)

    def process_results(self):
        '''Push results dict contents into the database.'''
        # Establish database connection
        circuit_db = ta2_database.Ta2ResultsDB(self.output_db)
        self.logger.info('Established database connection')

        for table in self.results:
            self.logger.info('Writing results to %s table', table)
            for row in self.results[table]:
                try:
                    circuit_db.add_row(table, row)
                except sqlite3.IntegrityError, error:
                    self.logger.warning('Could not insert row into %s ' +\
                                        'table:  %s.\nSkipping row:  %s', \
                                        table, error, str(row))
        circuit_db.close()

    def get_id_from_filename(self, filename):
        '''Pull the file name from a full path.'''
        return int(os.path.splitext(os.path.basename(filename))[0])

    def is_token_valid(self, token):
        '''Determin if the token found is expected for this table.'''
        token_list = self.tokens[self.table_name]
        for item in token_list:
            if item == token:
                return True
        self.logger.debug('Token %s not found in table %s', token, \
                          self.table_name)
        return False

    def check_tokens(self, data_row):
        '''Checks for missing tokens in row. We write to the DB anyway, it's
        just a check so we can log a warning and set the status.'''
        token_list = self.tokens[self.table_name]
        for token in token_list:
            if not self.column_map[self.table_name][token] in data_row:
                self.logger.warning('Found incomplete row, missing token %s', \
                                    token)
                # Required fields cannot be NULL
                data_row[self.column_map[self.table_name][token]] = ''
                data_row[self.column_map[self.table_name]['status']] = \
                    'FAILED'


def main():
    '''Using the CircuitParser class, parse logs and populate the database.'''
    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                  'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                  'CRITICAL': logging.CRITICAL}

    parser = argparse.ArgumentParser()
    ### Options should be log file directory for input
    ### DB info for output
    ### Log levels
    parser.add_argument('-i', '--input_dir', dest = 'input_dir',
           type = str, required = True,
           help = 'Directory containing test result log files')
    parser.add_argument('-o', '--output_db', dest = 'output_db',
           type = str, required = True,
           help = 'sqlite db name to store parsed performer queries')
    parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
           type = str, choices = log_levels.keys(),
           help = 'Only output log messages with the given severity or '
           'above')


    options = parser.parse_args()

    logging.basicConfig(
            level = log_levels[options.log_level],
            format = '%(levelname)s: %(message)s')

    circuit_parser = CircuitParser(options.output_db)

    try:
        log_list = circuit_parser.find_logs(options.input_dir, \
                                            circuit_parser.file_pattern)
    except Exception, error:
        circuit_parser.logger.error('Could not find log files in %s: %s', \
                     options.input_dir, error)
        del circuit_parser
        sys.exit(0)
    for log in log_list: 
        # Process the contents of this file
        circuit_parser.logger.info('Processing %s...', log)
        try:
            infile = open(log, 'r')
        except IOError:
            circuit_parser.logger.error('Could not open log file %s, ' +\
                                        'skipping.', infile)
            continue
        circuit_parser.parse_log(infile)
        circuit_parser.process_results()
        infile.close()
        print

    del circuit_parser

if __name__ == "__main__":
    main()
