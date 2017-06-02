# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Tim Meunier
#  Description:        Parser for the perfomer queries log file.
#                      Results are stored in a DB.
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
import spar_python.report_generation.ta1.ta1_database as ta1_database
import spar_python.report_generation.ta1.ta1_schema as ta1_schema
import spar_python.analytics.common.log_parser_util as log_parser_util
from spar_python.perf_monitoring.create_perf_graphs import PerfGraphGenerator

LOGGER = logging.getLogger(__name__)
FILE_PATTERN    = re.compile('^(Unloaded|VariableDelay)QueryRunner-\w+')

TIME_PATTERN    = re.compile('\[(?P<timestamp>[0-9]+\.[0-9]+)\] '
                             '(?P<message>.*)')
TC_PATTERN      = re.compile('[0-9-]{10} [0-9:]{8} (?P<performer>[^-]+)-[^-]+-'
                             '(?P<tc_id>[^_]+)_.+')
SENT_PATTERN    = re.compile('ID (?P<cmd_id>[0-9]+-[0-9]+) sent')
COMMAND_PATTERN = re.compile('ID (?P<cmd_id>[0-9]+-[0-9]+) '
                             'QID (?P<qid>[0-9]+): '
                             '\[\[SELECT (?P<cols>.+) FROM main '
                             'WHERE (?P<query>.*)\]\]')
RESULTS_PATTERN = re.compile('ID (?P<cmd_id>[0-9]+-[0-9]+) results:')
FAIL_PATTERN    = re.compile('FAILED.*')
HASH_PATTERN    = re.compile('(?P<result_id>[0-9]+) (?P<result_hash>[0-9a-f]+)')
EVENT_PATTERN	= re.compile('ID (?P<cmd_id>[0-9]+-[0-9]+) event '
                             '(?P<event_id>[0-9]+)( with value \[\['
                             '(?P<event_val>[\d]+)\]\])? occurred')
ENDLOG_PATTERN  = re.compile('END_OF_LOG')


class Rex:
    """Class to run a regular expression and store the groups for
       later retrieval.  Allows for clean if blocks of multiple regular
       expression patterns with different defined groups.

       if rex_obj.pmatch(REGEX, line):
         match = regex_obj.m.group('match1')
       elif rex_obj.pmatch(REGEX2, line):
         match = rex_obj.m.group('match2')
    """
    def __init__(self):
        self.m = None

    def pmatch(self, regex, line):
        """Execute regular expression match on <line>.  Return True
           on a match and store the MatchObject, False otherwise."""
        self.m = regex.match(line)
        if self.m:
            return True
        else:
            return False

def get_global_id(cmd_id):
    ids = cmd_id.split('-')
    assert ids[0]
    return ids[0]

def process_matches(matches):
    """Sort and separate the list of matches and optional hash pairs.
       Returns a list of ids and a list of hashes sorted by id."""
    id_list = []
    hash_list = []
    for row_id in sorted(matches, key=long):
        id_list.append(str(row_id))
        if (matches[row_id] != ''):
            hash_list.append(matches[row_id])
    return (id_list, hash_list)

def process_query(log_parser, query, cmd_id, matches, events, results_db, record_func, flags):
    """Process the query results, and push to DB."""

    # Attempt inserting a new row into the performer_queries table
    if (not log_parser.verify_result(query, [ta1_schema.DBP_SELECTIONCOLS, \
                                             ta1_schema.DBP_SENDTIME])):
        LOGGER.error('No evidence of command %s ever being sent',
                       cmd_id)
        return False
    else:
        (result_ids, result_hashes) = process_matches(matches)
        (event_ts, event_ids, event_vals) = log_parser.process_events(events)
        query.update(
            {ta1_schema.DBP_RETURNEDRECORDHASHES : result_hashes,
             ta1_schema.DBP_RETURNEDRECORDIDS : result_ids,
             ta1_schema.DBP_EVENTMSGTIMES : event_ts,
             ta1_schema.DBP_EVENTMSGIDS : event_ids,
             ta1_schema.DBP_EVENTMSGVALS : event_vals})
        if flags['mod']:
            query.update({ta1_schema.DBP_ISMODIFICATIONQUERY : 1})
        else:
            query.update({ta1_schema.DBP_ISMODIFICATIONQUERY : 0})
        if flags['throughput']:
            query.update({ta1_schema.DBP_ISTHROUGHPUTQUERY : 1})
        else:
            query.update({ta1_schema.DBP_ISTHROUGHPUTQUERY : 0})
    # Apply record_func to the complete query, and return the result
    return (record_func(query, cmd_id, results_db))

def append_baseline_matches(qid, cmd_id, matches, baseline_matches):
    '''
    Will add (qid, cmd_id, matches) to baseline_matches.

    baseline_matches is a dictionary indexed by qid which contains
    a list of dictionaries. The inner dictionary contains a field for
    'cmd_id' and 'matches'.

    When all the log files are parsed, there should be an entry for
    each modification id which will contain a list of size 2. One
    entry for the pre query results and another for the post query
    results. The "pre" value will be the one with the lower cmd_id.
    The "post" value will be the one with the larger cmd_id.
    '''
    new_entry = { 'global_id': get_global_id(cmd_id), 'matches': matches }
    baseline_matches[qid].append(new_entry)
    
def process_baseline_matches(all_baseline_matches, results_db):
    '''
    Fill in the mod to mod queries join table matching records and hash fields
    '''
    for qid, data in all_baseline_matches.iteritems():
        if len(data) != 2:
            LOGGER.warning("QID %d does not have 2 modification logs. "
                           "Instead it has %d logs. It should have a "
                           "pre modification log and a post modification "
                           "log. Skipping it", qid, len(data))
            continue

        # pre should be the entry with the lowest cmd_id
        pre_index = 0
        post_index = 1
        if data[pre_index][0]['global_id'] > data[post_index][0]['global_id']:
            pre_index = 1
            post_index = 0
        (pre_ids, pre_hashes) = process_matches(data[pre_index][0]['matches'])
        (post_ids, post_hashes) = process_matches(data[post_index][0]['matches'])
        
        # modify result database row with qid to add values
        '''
        M2MQ_TABLENAME = "mods_to_modqueries"
        M2MQ_QID = "qid"
        M2MQ_MID = "mid"
        M2MQ_PREIDS = "pre_matching_record_ids"
        M2MQ_PREHASHES = "pre_matching_record_hashes"
        M2MQ_POSTIDS = "post_matching_record_ids"
        M2MQ_POSTHASHES = "post_matching_record_hashes"
        '''
        cmd = 'UPDATE ' + ta1_schema.M2MQ_TABLENAME + ' SET ' + \
            ta1_schema.M2MQ_PREIDS + '=' + \
            '\'' + '|'.join(pre_ids) + '\'' + \
            ', ' + \
            ta1_schema.M2MQ_PREHASHES + '=' + \
            '\'' + '|'.join(pre_hashes) + '\'' + \
            ', ' + \
            ta1_schema.M2MQ_POSTIDS + '=' + \
            '\'' + '|'.join(post_ids) + '\'' + \
            ', ' + \
            ta1_schema.M2MQ_POSTHASHES + '=' + \
            '\'' + '|'.join(post_hashes) + '\'' + \
            ' WHERE ' + ta1_schema.M2MQ_QID + '=' + str(qid) 
        results_db._execute(cmd)


def parse_queries(log_parser, in_file, record_func, results_db, flags):
    """Main function that parses a log file, and applies record_func to each
       complete record of query information. record_func can be used to do any
       number of things, including updating a sqlite database, or writing out
       results to a *.csv file. Returns the number of *new* records processed.
    """

    num_records = 0
    rex_obj = Rex()
    temp_query_dict = collections.defaultdict(dict)
    tc_id = '000'
    performer = 'PERF'
    results = {'flag' : False, 'cmd_id' : ''}
    matches = {} 
    events_dict = collections.defaultdict(dict)
    cmd_id = ''
    baseline_matches = collections.defaultdict(list)

    for line in in_file:
        # Strip EOL
        line = line.strip()
        # Skip blank lines
        if len(line) == 0:
            continue

        LOGGER.debug('Parsing %s...', line)

        if (rex_obj.pmatch(TIME_PATTERN, line)):
            # Found a timestamped line
            timestamp = repr(float(rex_obj.m.group('timestamp')))
            res = rex_obj.m.group('message')
            if results['flag']:
                if (rex_obj.pmatch(EVENT_PATTERN, res)):
                    # Found an event
                    cmd_id = rex_obj.m.group('cmd_id')
                    event_id = rex_obj.m.group('event_id')
                    event_val = rex_obj.m.group('event_val')
                    if (cmd_id not in temp_query_dict.keys()) or \
                       (ta1_schema.DBP_SENDTIME not in temp_query_dict[cmd_id]):
                        # Event is for an invalid command, one that was not
                        # sent yet, or one that finished; it's not valid.
                        LOGGER.warning('Found an invalid event for ' +\
                                       'command id = %s ', cmd_id)
                    else:
                        # Event is for another valid command
                        events_dict[cmd_id].update({timestamp : [event_id, \
                                                    event_val]})
                    continue
                else: # The END_OF_LOG case will **not** hit here
                    # The line has a timestamp and it's not an event so the
                    # results are done.
                    results_cmd_id = results['cmd_id']
                    if flags['baseline']:
                        # special for baseline mods; save all query data
                        qid = temp_query_dict[results_cmd_id][ta1_schema.DBP_FQID]
                        append_baseline_matches(qid,
                                                results_cmd_id, matches, 
                                                baseline_matches)
                    else:
                        if process_query(log_parser, \
                                         temp_query_dict[results_cmd_id], \
                                         results_cmd_id, matches, \
                                         events_dict[results_cmd_id], \
                                         results_db, \
                                         record_func, flags):
                            num_records += 1
                        # Conserve memory by deleting the unneeded entry in
                        # temp_query_dict.  This is also necessary to keep track of
                        # valid cmd_id's for eventmsg collecting.
                        del temp_query_dict[results_cmd_id]
                    #clear results flag keep going
                    results['flag'] = False
                    results['cmd_id'] = ''
        else:
            if results['flag']:
                # Grab results
                if (rex_obj.pmatch(FAIL_PATTERN, line)):
                    LOGGER.warning('Command %s had FAILED results',
                                   results['cmd_id'])
                    # If we had a previous failure in this query, add the new
                    # failure message to the existing message
                    prev_fail_msg = temp_query_dict[results['cmd_id']] \
                                               [ta1_schema.DBP_STATUS] 
                    fail_msgs = []
                    if (prev_fail_msg):
                        fail_msgs = prev_fail_msg
                    fail_msgs.append('FAILED')
                    for line in in_file:
                        line = line.strip()
                        if line == 'ENDFAILED':
                            break
                        if (rex_obj.pmatch(TIME_PATTERN, line)):
                            timestamp = repr(float(rex_obj.m.group('timestamp')))
                            res = rex_obj.m.group('message')
                            if (rex_obj.pmatch(EVENT_PATTERN, res)):
                                # Found an event
                                cmd_id = rex_obj.m.group('cmd_id')
                                event_id = rex_obj.m.group('event_id')
                                event_val = rex_obj.m.group('event_val')
                                if (cmd_id not in temp_query_dict.keys()) or \
                                   (ta1_schema.DBP_SENDTIME not in \
                                       temp_query_dict[cmd_id]):
                                    # Event is for an invalid command, one that
                                    # was not sent yet, or one that finished;
                                    # it's not valid.
                                    LOGGER.warning('Found an invalid event ' +\
                                                   'for command id = %s ', \
                                                   cmd_id)
                                else:
                                    # Event is for another valid command
                                    events_dict[cmd_id].update({timestamp : \
                                                        [event_id, event_val]})
                            else: 
                                # Found timestamped line before ENDFAILED
                                LOGGER.warning('Found a timestamped line ' +\
                                               'before ENDFAILED for command ' +\
                                               'id = %s ', results[cmd_id])
                        else:
                            fail_msgs.append(line)
                    temp_query_dict[results['cmd_id']].update(
                        {ta1_schema.DBP_STATUS : fail_msgs})
                elif (rex_obj.pmatch(HASH_PATTERN, line)):
                    # Else, add relevant data if there is both a row and a hash
                    matches[long(rex_obj.m.group('result_id'))] = \
                        rex_obj.m.group('result_hash') 
                else:
                    # Else, add only row
                    matches[line] = ''
            else:
                # Skip it
                LOGGER.warning("Skipping line without timestamp: %s", line)
            continue

        # Continue to parse the timestamped line
        if (rex_obj.pmatch(TC_PATTERN, res)):
            # Found test case pattern
            LOGGER.debug('Found testcase')
            tc_id = rex_obj.m.group('tc_id')
            performer = rex_obj.m.group('performer')
        elif (rex_obj.pmatch(SENT_PATTERN, res)):
            # Found sent pattern
            LOGGER.debug('Found sent statement')
            cmd_id = rex_obj.m.group('cmd_id')
            temp_query_dict[cmd_id].update(
                 {ta1_schema.DBP_PERFORMERNAME : performer,
                  ta1_schema.DBP_TESTCASEID : tc_id,
                  ta1_schema.DBP_SENDTIME : timestamp})
        elif (rex_obj.pmatch(COMMAND_PATTERN, res)):
            # Found command pattern
            LOGGER.debug('Found command statement')
            cmd_id = rex_obj.m.group('cmd_id')
            temp_query_dict[cmd_id].update(
                {ta1_schema.DBP_PERFORMERNAME : performer,
                 ta1_schema.DBP_TESTCASEID : tc_id,
                 ta1_schema.DBP_FQID : long(rex_obj.m.group('qid')),
                 ta1_schema.DBP_SELECTIONCOLS : rex_obj.m.group('cols')})
        elif (rex_obj.pmatch(RESULTS_PATTERN, res)):
            # Found results pattern
            LOGGER.debug('Found results statement')
            cmd_id = rex_obj.m.group('cmd_id')
            temp_query_dict[cmd_id].update(
                    {ta1_schema.DBP_RESULTSTIME : timestamp,
                     ta1_schema.DBP_STATUS : []})
            # Calculate elapsed time
            if ta1_schema.DBP_SENDTIME in temp_query_dict[cmd_id]:
                latency = \
                    log_parser.compute_latency( \
                       temp_query_dict[cmd_id][ta1_schema.DBP_SENDTIME],
                       timestamp)
                temp_query_dict[cmd_id].update(
                    {ta1_schema.DBP_QUERYLATENCY : repr(latency)})
            else:
                LOGGER.warning('Found results for command %s but the ' +\
                               'command was never sent.  The command will ' +\
                               'not be written to the database.', cmd_id)
            results = {'flag' : True,
                       'cmd_id' : cmd_id}
            matches = {}
        elif (rex_obj.pmatch(EVENT_PATTERN, res)):
            # Found an event
            LOGGER.debug('Found event statement')
            cmd_id = rex_obj.m.group('cmd_id')
            event_id = rex_obj.m.group('event_id')
            event_val = rex_obj.m.group('event_val')
            if (cmd_id not in temp_query_dict.keys()) or \
               (ta1_schema.DBP_SENDTIME not in temp_query_dict[cmd_id]):
                # Event is for an invalid command, one that was not
                # sent yet, or one that finished; it's not valid.
                LOGGER.warning('Found an invalid event for command id = ' +\
                               '%s ', cmd_id)
            else:
                # Capture dict of events and times
                events_dict[cmd_id].update({timestamp : [event_id, event_val]})
        elif (rex_obj.pmatch(ENDLOG_PATTERN, res)):
            # End of log marker
            LOGGER.debug('Found end of log')
            break
        else:
            if not log_parser.ignorable_line(line):
                # If no pattern was matched, warn and move on
                LOGGER.warning('Skipping unrecognized line pattern: %s', line)
            else:
                LOGGER.debug('Skipping ignorable line pattern: %s', line)

    # We've exhausted all the lines in the log, but there may be one more set
    # of outstanding results to push to the database.
    results_cmd_id = results['cmd_id']
    if flags['baseline']:
        # special for baseline mods; save all query data
        qid = temp_query_dict[results_cmd_id][ta1_schema.DBP_FQID]
        append_baseline_matches(qid,
                                results_cmd_id, matches, 
                                baseline_matches)
    else:
        if process_query(log_parser, \
                         temp_query_dict[results_cmd_id], \
                         results_cmd_id, matches, \
                         events_dict[results_cmd_id], \
                         results_db, \
                         record_func, flags):
            num_records += 1
        # Conserve memory by deleting the unneeded entry in
        # temp_query_dict.  This is also necessary to keep track of
        # valid cmd_id's for eventmsg collecting.
        del temp_query_dict[results_cmd_id]

    if not flags['baseline']:
        if len(temp_query_dict) > 0:
            LOGGER.warning('Not all queries returned results!')
    return (num_records, baseline_matches)

def record_func(query_info, command_id, results_db):
    """Function used to process each complete query record. Returns 0 if no new
       rows are created, and returns 1 if a new row is created."""

    LOGGER.info('Pushing command %s to DB', command_id)
    LOGGER.debug(query_info)

    added = False

    try:
        results_db.add_row(ta1_schema.DBP_TABLENAME, query_info)
        added = True
    except sqlite3.IntegrityError, error:
        LOGGER.warning('Failed to insert row: %s.\nSkipping row:  %s', \
                       error, str(query_info))

    return added

def main():
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
           help = 'Sqlite db name to store parsed performer queries')
    parser.add_argument('-m', '--mod', dest = 'mod',
           action='store_true', required = False,
           help = 'Flag for processing modification logs')
    parser.add_argument('-t', '--throughput', dest = 'throughput',
           action='store_true', required = False,
           help = 'Flag for processing modification logs')
    parser.add_argument('-b', '--baseline', dest = 'baseline',
           action='store_true', required = False,
           help = 'Flag for processing baseline modification logs')
    parser.add_argument('-p', '--perfdb', dest='perfdb',
           type = str, required = False, 
           help = "SQLite database holding performance monitoring data")
    parser.add_argument('-g', '--graph_dir', dest='graph_dir',
            type = str, required = False,
            help = "directory to hold performance graphs")
    parser.add_argument('--log_level', dest = 'log_level', default = 'INFO',
           type = str, choices = log_levels.keys(),
           help = 'Only output log messages with the given severity or '
           'above')

    options = parser.parse_args()

    # Get flag options
    flags = {'mod' : options.mod, 
             'throughput' : options.throughput,
             'baseline' : options.baseline}

    logging.basicConfig(
            level = log_levels[options.log_level],
            format = '%(levelname)s: %(message)s')

    log_parser = log_parser_util.LogParserUtil()
    
    #Use performance monitoring data, if it is present
    perf_graph_generator = None
    graph_dir = None
    if (options.perfdb):
        perf_db = sqlite3.connect(options.perfdb)
        perf_graph_generator = PerfGraphGenerator(perf_db)
        assert options.graph_dir, "must have graph folder if " \
            "performance db provided"
        assert os.path.isdir(options.graph_dir), "graph output directory" \
            "must be a directory"
        graph_dir = options.graph_dir
    

    # Establish database connection
    results_db = ta1_database.Ta1ResultsDB(options.output_db)
    LOGGER.debug("Established database connection")

    try:
        log_list = log_parser.find_logs(options.input_dir, FILE_PATTERN)
        print 'Found %d files' % len(log_list)
    except Exception, error:
        LOGGER.error('Could not find log files in %s: %s', \
                     options.input_dir, error)
        sys.exit(0)
    # all_baseline_matches is used for baseline mods where it needs
    # all the client logs parsed and the results stored before it can
    # update the result db.
    all_baseline_matches = collections.defaultdict(list)
    for log in log_list: 
        # Process the contents of this file
        LOGGER.info('Processing %s...', log)
        # Resolve timestamps on server harness log file
        resolved_file = log_parser.resolve_ts_to_temp(log)
        if resolved_file:
            # Parse the timestamp modified file
            (new_rows, baseline_matches) = \
                parse_queries(log_parser, resolved_file, \
                                  record_func, results_db, flags)
            if options.baseline:
                # merge the baseline data from each log file
                for qid, data in baseline_matches.iteritems():
                    all_baseline_matches[qid].append(data)
                

            LOGGER.info('Inserted %d new rows into database', new_rows)
            resolved_file.close()
            print
        else:
            LOGGER.error('Could not update timestamps in %s!' + \
                         '  Cannot continue parsing file.', log)
        # Produce performance graphs
        if (perf_graph_generator):
            perf_graph_generator.produce_graphs_from_log(log, graph_dir)

    if options.baseline:
        # do baseline mods now that it has all the client logs parsed and 
        # stored in all_baseline_matches
        process_baseline_matches(all_baseline_matches, results_db)


    if options.baseline:
        # do baseline mods now that it has all the client logs parsed and 
        # stored in all_baseline_matches
        process_baseline_matches(all_baseline_matches, results_db)


    results_db.close()


if __name__ == '__main__':
    main()
