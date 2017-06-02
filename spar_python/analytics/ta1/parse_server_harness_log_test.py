# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill Poland
#  Description:        Unit tests for the server harness log file 
#                      parser
# *****************************************************************

#import os
#import sys
import os
import sys
import unittest
import StringIO
import collections
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.analytics.ta1.parse_server_harness_log \
           as parse_server_harness_log
import spar_python.report_generation.ta1.ta1_schema as ta1_schema
import spar_python.analytics.common.log_parser_util as log_parser_util


class ParseSHLogTest(unittest.TestCase):
    ''' test class for the parse server harness log file functionality '''

    test_log_file = """[2936548.490002438] 2013-05-30 13:34:43 IBM001
[2936548.490002438] Invoked from /home/lincoln /spar-testing/bin/
[2936548.490002438] NOTE: ID x MID y = x-globalID, y-resultsDBModificationID
[3305997.437652770] EPOCH TIME: 1365108319.361063719
[3305997.438331404] ID 0 sent
[3306010.438431404] ID 0 event 4 occurred
[3306997.438567347] ID 0 MID 53: INSERT 4927728924000000000
[3306997.545109896] ID 0 results: DONE
[3305997.438331404] ID 1 sent
[3305997.437652770] EPOCH TIME: 1365108319.361063719
[3305997.438567347] ID 1 MID 682: UPDATE 1026497184236
[3306020.458567347] ID 1 event 5 with value 55 occurred
[3305997.545109896] ID 1 results: FAILED
Could not convert string to integer.
ENDFAILED
[3305997.438331404] ID 2 sent
[3305997.438567347] ID 2 MID 53: DELETE 4927728924000000000
[3305997.545109896] ID 2 results: DONE
[3308000.551111111] ID 3 sent
[3308010.552222222] ID 3 MID 555: VERIFY 1234
[3308020.553333333] ID 3 results: DONE
[3309000.551111111] ID 4 sent
[3309010.552222222] ID 4 MID 78: VERIFY 5678
[3309020.553333333] ID 4 results: FAILED
Failure string
[3309020.554444444] ID 4 event 44 occurred
on multiple lines
[3309020.555555555] ID 4 event 55 with value 555 occurred
ENDFAILED
[3310000.551111111] ID 5 sent
[3310010.552222222] ID 5 MID 79: VERIFY 91011
[3310020.553333333] ID 5 results: FAILED
VERIFY FALSE
What he say!?
ENDFAILED
"""

    gold = {'0' : {ta1_schema.PMODS_STATUS : [''],
                   ta1_schema.PMODS_PERFORMER : 'IBM',
                   ta1_schema.PMODS_MID : '53',
                   ta1_schema.PMODS_RESULTSTIME : repr(3306997.545109896),
                   ta1_schema.PMODS_SENDTIME : repr(3305997.438331404),
                   ta1_schema.PMODS_TESTCASEID : '001',
                   ta1_schema.PMODS_MODLATENCY : repr(1000.10677849221974611),
                   ta1_schema.PMODS_EVENTMSGTIMES : ['3306010.438431404'],
                   ta1_schema.PMODS_EVENTMSGIDS : ['4'],
                   ta1_schema.PMODS_EVENTMSGVALS : ['']},
            '1' : {ta1_schema.PMODS_STATUS : ['FAILED', 'Could not convert ' + \
                                              'string to integer.'],
                   ta1_schema.PMODS_PERFORMER : 'IBM',
                   ta1_schema.PMODS_MID : '682',
                   ta1_schema.PMODS_RESULTSTIME : repr(3305997.545109896),
                   ta1_schema.PMODS_SENDTIME : repr(3305997.438331404),
                   ta1_schema.PMODS_TESTCASEID : '001',
                   ta1_schema.PMODS_MODLATENCY : repr(0.10677849221974611),
                   ta1_schema.PMODS_EVENTMSGTIMES : ['3306020.458567347'],
                   ta1_schema.PMODS_EVENTMSGIDS : ['5'],
                   ta1_schema.PMODS_EVENTMSGVALS : ['55']},
            '2' : {ta1_schema.PMODS_STATUS : [''],
                   ta1_schema.PMODS_PERFORMER : 'IBM',
                   ta1_schema.PMODS_MID : '53',
                   ta1_schema.PMODS_RESULTSTIME : repr(3305997.545109896),
                   ta1_schema.PMODS_SENDTIME : repr(3305997.438331404),
                   ta1_schema.PMODS_TESTCASEID : '001',
                   ta1_schema.PMODS_MODLATENCY : repr(0.10677849221974611)},
            # Note that gid 3 - 5 are verification queries BEFORE they
            # are converted to verification queries.  Therefor they use PMODS
            # constants and the failure case does not contain a value for
            # 'verification'.  This mimics how the parsing code is written.
            '3' : {'command' : 'VERIFY',
                   ta1_schema.PMODS_MID : '555',
                   ta1_schema.PMODS_STATUS : [''],
                   ta1_schema.PMODS_PERFORMER : 'IBM',
                   'record_id' : '1234',
                   ta1_schema.PMODS_RESULTSTIME : repr(3308020.553333333),
                   ta1_schema.PMODS_SENDTIME : repr(3308000.551111111),
                   ta1_schema.PMODS_TESTCASEID : '001',
                   ta1_schema.PMODS_MODLATENCY : repr(20.002222222276031971),
                   'verification' : 1},
            '4' : {'command' : 'VERIFY',
                   ta1_schema.PMODS_MID : '78',
                   ta1_schema.PMODS_STATUS : ['FAILED', 'Failure string',
                                             'on multiple lines'],
                   ta1_schema.PMODS_PERFORMER : 'IBM',
                   'record_id' : '5678',
                   ta1_schema.PMODS_RESULTSTIME : repr(3309020.553333333),
                   ta1_schema.PMODS_SENDTIME : repr(3309000.551111111),
                   ta1_schema.PMODS_TESTCASEID : '001',
                   ta1_schema.PMODS_MODLATENCY : repr(20.002222222276031971),
                   ta1_schema.PMODS_EVENTMSGTIMES : ['3309020.554444444',
                                                     '3309020.555555555'],
                   ta1_schema.PMODS_EVENTMSGIDS : ['44', '55'],
                   ta1_schema.PMODS_EVENTMSGVALS : ['', '555']},
            '5' : {'command' : 'VERIFY',
                   ta1_schema.PMODS_MID : '79',
                   ta1_schema.PMODS_STATUS : [''],
                   ta1_schema.PMODS_PERFORMER : 'IBM',
                   'record_id' : '91011',
                   ta1_schema.PMODS_RESULTSTIME : repr(3310020.553333333),
                   ta1_schema.PMODS_SENDTIME : repr(3310000.551111111),
                   ta1_schema.PMODS_TESTCASEID : '001',
                   ta1_schema.PMODS_MODLATENCY : repr(20.002222222276031971),
                   'verification' : 0}}

    def test_convert_to_verification(self):
        ''' Test conversion from a modification query to a verification
        query. '''
        # Use the existing unconverted query results as the input
        test_query = self.gold.get('3')
        gold_query = {ta1_schema.PVER_STATUS : [''],
                      ta1_schema.PVER_PERFORMER : 'IBM',
                      ta1_schema.PVER_RECORDID : '1234',
                      ta1_schema.PMODS_RESULTSTIME : repr(3308020.553333333),
                      ta1_schema.PMODS_SENDTIME : repr(3308000.551111111),
                      ta1_schema.PVER_TESTCASEID : '001',
                      ta1_schema.PVER_VERIFICATIONLATENCY : \
                                   repr(20.002222222276031971),
                      ta1_schema.PVER_VERIFICATION : 1}
        result_query = parse_server_harness_log.convert_to_verification( \
                                                  test_query)
        self.assertEqual(result_query, gold_query)

    def _my_process_results_data(self, results, output_db):
        ''' check the query results data '''

        gids = results.keys()
        self.assertEqual(len(gids), 6)
        for test_gid in gids:
            if not self.gold[test_gid]:
                self.failureException('ID %s not expected.', test_gid)
            else:
                self.assertEqual(results[test_gid], self.gold[test_gid])


    @unittest.skip("Does not reflect the current log message format")
    def test_parse_file(self):
        '''test the parse method '''

        log_parser = log_parser_util.LogParserUtil()
        test_file = StringIO.StringIO(self.test_log_file)

        # Parse the log file
        res = collections.defaultdict(dict)
        res = parse_server_harness_log.parse_file(log_parser, test_file)
        self._my_process_results_data(res, ':memory:')
        test_file.close()
