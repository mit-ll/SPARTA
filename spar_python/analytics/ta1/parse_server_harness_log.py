# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill Poland
#  Description:        Parser for the server harness log file
# *****************************************************************

import argparse
import logging
import re
import sqlite3
import collections

import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta1.ta1_database as ta1_database
import spar_python.report_generation.ta1.ta1_schema as ta1_schema
import spar_python.analytics.common.log_parser_util as log_parser_util

LOGGER = logging.getLogger(__name__)

# constants
FILE_PATTERN = re.compile('^server-harness.log$')

TC_PATTERN = re.compile('.*[0-9-]{10} [0-9:]{8} (?P<performer>[^-]+)-[^-]+-'
                        '(?P<test_case_id>[^_]+)_.+')
ID_PATTERN = re.compile('\[(?P<timestamp>[0-9.]+)\] ID (?P<gid>[0-9]+-[0-9]+) '
                        '(?P<msg>.+)')
MID_PATTERN = re.compile('MID (?P<mid>[0-9]+): (?P<command>[A-Z]+) ' + \
                         '(?P<record_id>.+)')
RES_PATTERN = re.compile('results: (?P<result>.+)')
EVENT_PATTERN = re.compile('event (?P<event_id>[0-9]+)( with value '
                           '(?P<event_val>[\d]+))? occurred')


def convert_to_verification(ver):
    ''' Convert the column names from the mods table names to the
    verification table names and remove columns not related to a
    verification query. '''
    converted = {}
    converted[ta1_schema.PVER_PERFORMER] = ver[ta1_schema.PMODS_PERFORMER]
    converted[ta1_schema.PVER_TESTCASEID] = ver[ta1_schema.PMODS_TESTCASEID]
    converted[ta1_schema.PVER_RECORDID] = ver['record_id']
    if not ('verification' in ver):
        # If query execution failed, verification won't be set, make it null
        converted[ta1_schema.PVER_VERIFICATION] = '' 
    else:
        converted[ta1_schema.PVER_VERIFICATION] = ver['verification']
    converted[ta1_schema.PVER_SENDTIME] = ver[ta1_schema.PMODS_SENDTIME]
    converted[ta1_schema.PVER_RESULTSTIME] = ver[ta1_schema.PMODS_RESULTSTIME]
    converted[ta1_schema.PVER_VERIFICATIONLATENCY] = \
        ver[ta1_schema.PMODS_MODLATENCY]
    if ta1_schema.PMODS_EVENTMSGTIMES in ver:
        converted[ta1_schema.PVER_EVENTMSGTIMES] = \
            ver[ta1_schema.PMODS_EVENTMSGTIMES]
        converted[ta1_schema.PVER_EVENTMSGIDS] = \
            ver[ta1_schema.PMODS_EVENTMSGIDS]
        converted[ta1_schema.PVER_EVENTMSGVALS] = \
            ver[ta1_schema.PMODS_EVENTMSGVALS]
    converted[ta1_schema.PVER_STATUS] = ver[ta1_schema.PMODS_STATUS]
    return converted

def process_results_data(log_parser, results, output_db):
    ''' For all complete modifications, add the data to the
    'performer_mods' table in the results database; otherwise log a
    warning and skip the incomplete modification 
    Always return True'''

    # Check for all data, if not log warning
    modlist = []
    verificationlist = []
    for gid in results:
        if (results[gid].get('command') == 'VERIFY'):
            # Use PMODS and literal strings here because we haven't converted
            # to the PVER constants yet.
            if not log_parser.verify_result(results[gid], \
                                            [ta1_schema.PMODS_SENDTIME,
                                             'record_id', 
                                             ta1_schema.PMODS_RESULTSTIME]):
                LOGGER.warning('WARNING: skipping insertion of verification ' \
                               'results for gid = %s: Test logs were not ' \
                                'complete', gid)
            else:
                verificationlist.append(convert_to_verification(results[gid]))
        else: 
            if not log_parser.verify_result(results[gid], \
                                            [ta1_schema.PMODS_SENDTIME,
                                             ta1_schema.PMODS_MID,
                                             ta1_schema.PMODS_RESULTSTIME]):
                LOGGER.warning('WARNING: skipping insertion of modification ' \
                               'results for gid = %s: Test logs were not ' \
                               'complete', gid)
            else:
                modlist.append(results[gid])


    # Establish database connection
    server_db = ta1_database.Ta1ResultsDB(output_db)

    for row in modlist:
        try:
            # Insert modification row into database
            server_db.add_row(ta1_schema.PMODS_TABLENAME, row)
        except sqlite3.IntegrityError, error:
            LOGGER.warning('Failed to insert row into modifications table:  ' + \
                           '%s.\nSkipping row:  %s', error, str(row))
    for row in verificationlist:
        try:
            # Insert verifications into database
            server_db.add_row(ta1_schema.PVER_TABLENAME, row)
        except sqlite3.IntegrityError, error:
            LOGGER.warning('Failed to insert row into verifications table:  ' + \
                           '%s.\nSkipping row:  %s', error, str(row))
    server_db.close()

def parse_file(log_parser, input_file):
    ''' parse the file. Expect file in the format specified by
    the wiki document Test Harness Log Formats.
    For example:
    [2936548.490002438] 2013-05-30 13:34:43 TC001
    [2936548.490002438] Invoked from /home/lincoln/spar-testing/bin/
    [2936548.490002438] NOTE: ID x MID y = x-globalID, y-resultsDBModificationID
    [3305997.437652770] EPOCH TIME: 1365108319.361063719
    [3305997.438331404] ID 0 sent
    [3305997.438567347] ID 0 MID 53: INSERT 4927728924000000000
    [3305997.545109896] ID 0 results: DONE
    [3305997.438331404] ID 1 sent
    [3305997.437652770] EPOCH TIME: 1365108319.361063719
    [3305997.438567347] ID 1 MID 682: UPDATE 1026497184236
    [3305997.545109896] ID 1 results: DONE
    [3305997.438331404] ID 2 sent
    [3305997.438567347] ID 2 MID 53: DELETE 4927728924000000000
    [3305997.545109896] ID 2 results: DONE

    Expect a sent, command, and results line for each ID before
    seeing a sent for the next ID. A given ID may not have all three 
    rows.

    ID is the global ID (gid)
    MID is the modification ID
    '''

    performer = "UNKNOWN"
    test_case_id = "UNKNOWN"
 
    # Collect the test data
    results = collections.defaultdict(dict)
    events_dict = collections.defaultdict(dict)
    for line in input_file:
        tc_match = TC_PATTERN.match(line)
        id_match = ID_PATTERN.match(line)
        if tc_match:
            # Found a Performer and Testcase ID
            performer = tc_match.group('performer')
            test_case_id = tc_match.group('test_case_id')
            continue
        elif id_match:
            # Found an ID line
            timestamp = repr(float(id_match.group('timestamp')))
            gid = id_match.group('gid')
            msg = id_match.group('msg')
            mid_match = MID_PATTERN.match(msg)
            res_match = RES_PATTERN.match(msg)
            event_match = EVENT_PATTERN.match(msg)
            if (msg == 'sent'):
                results[gid].update({ta1_schema.PMODS_TESTCASEID : \
                                           test_case_id,
                                     ta1_schema.PMODS_PERFORMER : \
                                           performer,
                                     ta1_schema.PMODS_SENDTIME : \
                                           repr(float(timestamp))})
            elif mid_match:
                results[gid].update({ta1_schema.PMODS_MID : \
                                           mid_match.group('mid')})
                cmd = mid_match.group('command')
                if (cmd == 'VERIFY'):
                    # Found a verification query
                    LOGGER.debug('Found verification query with gid: %s', gid)
                    results[gid].update({'command' : cmd,
                                         'record_id' : \
                                         mid_match.group('record_id')})
            elif res_match:
                res = res_match.group('result')
                if (res == 'FAILED'):
                    fail_list = ['FAILED'] 
                    for line in input_file:
                        line = line.strip()
                        if line == 'ENDFAILED':
                            break
                        
                        id_match = ID_PATTERN.match(line)
                        if id_match:
                            # Found a timestamped line
                            new_timestamp = repr(float(id_match.group('timestamp')))
                            gid = id_match.group('gid')
                            msg = id_match.group('msg')
                            event_match = EVENT_PATTERN.match(msg)
                            if event_match:
                                # Found an event within the results
                                event_id = event_match.group('event_id')
                                event_val = event_match.group('event_val')
                                LOGGER.debug('Found an event message with ' +\
                                             'id %s', event_id)
                                if (gid not in results.keys()) or \
                                   (ta1_schema.PMODS_SENDTIME not in results[gid]) or \
                                   (ta1_schema.PMODS_RESULTSTIME in results[gid]):
                                    # Event is for an invalid command, one that
                                    # was not sent yet, or one that finished;
                                    # it's not valid.
                                    LOGGER.warning('Found an invalid event ' +\
                                                   'for gid = %s ', gid)
                                else:
                                    # Capture dict of events and times
                                    events_dict[gid].update({new_timestamp : \
                                                       [event_id, event_val]})
                            else:
                                # Found new command before ENDFAILED
                                # TODO: Can we handle this?
                                LOGGER.error('Found a timestamped line ' +\
                                             'after a FAIL but before ' +\
                                             'an ENDFAILED:  %s.  The ' +\
                                             'log needs to be corrected ' +\
                                             'to be processed!', line)
                                sys.exit(0)
                        else:
                            fail_list.append(line)
                    # Check for verification result
                    if (fail_list[1] == 'VERIFY FALSE'):
                        LOGGER.debug('Found verification result of FALSE ' +\
                                     'for gid: %s', gid)
                        results[gid].update({'verification' : 0,
                                             ta1_schema.PMODS_STATUS : ['']})
                    else:
                        LOGGER.debug('Found result of FAILED for gid: %s', gid)
                        # On a real failure, don't set 'verification'
                        results[gid].update({ta1_schema.PMODS_STATUS : \
                                                 fail_list})
                elif (res == 'DONE'):
                    if (ta1_schema.PMODS_MID not in results[gid]):
                        LOGGER.warning('Found a result for gid = %s before ' \
                                       'finding a mid', gid)
                    elif (results[gid].get('command') == 'VERIFY'):
                        # If it's a verification query, DONE means that the
                        # verification was true.
                        LOGGER.debug('Found verification result of true ' \
                                     'with gid: %s', gid)
                        results[gid].update({ta1_schema.PMODS_STATUS : [''],
                                             'verification' : 1})
                    else:
                        LOGGER.debug('Found result of DONE for gid: %s', gid)
                        results[gid].update({ta1_schema.PMODS_STATUS : ['']})
                else:
                    LOGGER.warning('Command with gid = %s had an unexpected ' \
                                   'command result: %s', gid, res)
                results[gid].update({ta1_schema.PMODS_RESULTSTIME : \
                                           repr(float(timestamp))})
                if ta1_schema.PMODS_SENDTIME in results[gid]:
                    # Compute latency
                    latency = log_parser.compute_latency( \
                        results[gid][ta1_schema.PMODS_SENDTIME], \
                        results[gid][ta1_schema.PMODS_RESULTSTIME])
                    results[gid].update({ta1_schema.PMODS_MODLATENCY : \
                                         repr(latency)})
                else:
                    LOGGER.warning('Could not find send time for command ' \
                                   'with gid = %s', gid)
            elif event_match:
                # Found an event message
                event_id = event_match.group('event_id')
                event_val = event_match.group('event_val')
                LOGGER.debug('Found an event message with id %s', event_id)
                if (gid not in results.keys()) or \
                   (ta1_schema.PMODS_SENDTIME not in results[gid]) or \
                   (ta1_schema.PMODS_RESULTSTIME in results[gid]):
                    # Event is for an invalid command, one that was not
                    # sent yet, or one that finished; it's not valid.
                    LOGGER.warning('Found an invalid event for gid = ' +\
                                   '%s ', gid)
                else:
                    # Capture dict of events and times
                    events_dict[gid].update({timestamp : [event_id, event_val]})
        else:
            if not log_parser.ignorable_line(line):
                LOGGER.warning("Skipping unrecognized line pattern: %s", line)

    # Process all the events and store them in the results dict
    for gid in events_dict.keys():
        (event_ts, event_ids, event_vals) = log_parser.process_events(events_dict[gid])
        results[gid].update({ta1_schema.PMODS_EVENTMSGTIMES : event_ts,
                             ta1_schema.PMODS_EVENTMSGIDS : event_ids,
                             ta1_schema.PMODS_EVENTMSGVALS : event_vals})

    return results
                

def main():
    ''' main program to parse the server harness log file and add the 
    data to the database '''

    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                  'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                  'CRITICAL': logging.CRITICAL}

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_dir', dest = 'input_dir',
                        type = str, required = True,
                        help = 'Directory containing the server logs.')
    parser.add_argument('-o', '--output_db', dest = 'output_db',
           type = str, required = True,
           help = 'Sqlite db name to store parsed server results.')
    parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
                        type = str, choices = log_levels.keys(),
                        help = 'Only output log messages with the given '
                        'severity or above')

    options = parser.parse_args()

    logging.basicConfig(
        level = log_levels[options.log_level],
        format = '%(levelname)s: %(message)s')

    log_parser = log_parser_util.LogParserUtil()

    try:
        log_list = log_parser.find_logs(options.input_dir, FILE_PATTERN)
    except Exception, error:
        LOGGER.error('Could not find log files in %s: %s', \
                     options.input_dir, error)
        sys.exit(0)
    for log in log_list: 
        LOGGER.info('Processing %s...', log)
        # Resolve timestamps on server harness log file
        sh_log_file = log_parser.resolve_ts_to_temp(log)
        if sh_log_file:
            # Parse the timestamp modified file
            res = collections.defaultdict(dict)
            res = parse_file(log_parser, sh_log_file)
            process_results_data(log_parser, res, options.output_db)
                       
            sh_log_file.close()
        else:
            LOGGER.error('Could not update timestamps in %s!' + \
                         '  Cannot continue parsing file.', log)


if __name__ == '__main__':
    main()
