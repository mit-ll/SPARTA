# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Tim Meunier
#  Description:        Unit tests for the perfomer queries log file 
#                      parser
# *****************************************************************

import unittest
import StringIO

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta1.ta1_schema as ta1_schema
import spar_python.analytics.ta1.parse_client_harness_log as parse_client_harness
import spar_python.analytics.common.log_parser_util as log_parser_util

class ParsePerfLogTest(unittest.TestCase):
    """Test performer queries log parser"""
    maxDiff = None

    # command id 33-1
    gold_query1 = {ta1_schema.DBP_PERFORMERNAME: 'IBM',
                   ta1_schema.DBP_FQID : 2384,
                   ta1_schema.DBP_TESTCASEID : '001',
                   ta1_schema.DBP_QUERYLATENCY : repr(0.10711013292893767),
                   ta1_schema.DBP_EVENTMSGTIMES : [],
                   ta1_schema.DBP_EVENTMSGIDS : [],
                   ta1_schema.DBP_EVENTMSGVALS : [],
                   ta1_schema.DBP_RESULTSTIME : repr(3305997.545109896),
                   ta1_schema.DBP_SENDTIME : repr(3305997.437999763),
                   ta1_schema.DBP_STATUS : [],
                   ta1_schema.DBP_RETURNEDRECORDHASHES : [],
                   ta1_schema.DBP_RETURNEDRECORDIDS :
                                  [ '42825118908495',
                                    '44435731644979',
                                    '95438468284621',
                                   '171815871709769',
                                   '178893977813230',
                                   '205058918580953',
                                   '273198574731828',
                                   '279383327637992',
                                   '318944271401057',
                                   '348897373323835',
                                   '349017632408193',
                                   '380267814454218',
                                   '386091790107092',
                                   '404590214250850',
                                   '410555923825061',
                                   '416371309544263',
                                   '425210352239438',
                                   '425738633216567'],
                   ta1_schema.DBP_SELECTIONCOLS : 'id',
                   ta1_schema.DBP_ISMODIFICATIONQUERY : 0,
                   ta1_schema.DBP_ISTHROUGHPUTQUERY : 0}
    # command id 36-4
    gold_query2 = {ta1_schema.DBP_PERFORMERNAME : 'IBM',
                   ta1_schema.DBP_FQID : 90,
                   ta1_schema.DBP_TESTCASEID : '001',
                   ta1_schema.DBP_QUERYLATENCY : repr(670.1062920428813),
                   ta1_schema.DBP_EVENTMSGTIMES : [],
                   ta1_schema.DBP_EVENTMSGIDS : [],
                   ta1_schema.DBP_EVENTMSGVALS : [],
                   ta1_schema.DBP_RESULTSTIME : repr(3306667.545109896),
                   ta1_schema.DBP_SENDTIME : repr(3305997.438817853),
                   ta1_schema.DBP_STATUS : [],
                   ta1_schema.DBP_RETURNEDRECORDHASHES : [],
                   ta1_schema.DBP_RETURNEDRECORDIDS : ['123', '456', '789'],
                   ta1_schema.DBP_SELECTIONCOLS : 'id, data',
                   ta1_schema.DBP_ISMODIFICATIONQUERY : 0,
                   ta1_schema.DBP_ISTHROUGHPUTQUERY : 0}
    # command id 35-3
    gold_query3 = {ta1_schema.DBP_PERFORMERNAME : 'IBM',
                   ta1_schema.DBP_FQID : 28,
                   ta1_schema.DBP_QUERYLATENCY : repr(553.1068647759967),
                   ta1_schema.DBP_EVENTMSGTIMES : [],
                   ta1_schema.DBP_EVENTMSGIDS : [],
                   ta1_schema.DBP_EVENTMSGVALS : [],
                   ta1_schema.DBP_RESULTSTIME : repr(3306550.545432123),
                   ta1_schema.DBP_SENDTIME : repr(3305997.438567347),
                   ta1_schema.DBP_STATUS : ['FAILED', 'Some', 'failure',
                                            'results', 'FAILED', 'Second',
                                            'failure', 'results'],
                   ta1_schema.DBP_RETURNEDRECORDHASHES : [],
                   ta1_schema.DBP_RETURNEDRECORDIDS : ['111111111111111',
                                                       '555555555555555',
                                                       '999999999999999'], 
                   ta1_schema.DBP_TESTCASEID : '001',
                   ta1_schema.DBP_SELECTIONCOLS : 'id',
                   ta1_schema.DBP_ISMODIFICATIONQUERY : 0,
                   ta1_schema.DBP_ISTHROUGHPUTQUERY : 0}
    # command id 34-2
    gold_query4 = {ta1_schema.DBP_PERFORMERNAME : 'IBM',
                   ta1_schema.DBP_FQID : 5847,
                   ta1_schema.DBP_QUERYLATENCY : repr(670.5616685952991),
                   ta1_schema.DBP_EVENTMSGTIMES : ['3305997.438667347',
                                                   '3305997.448667347',
                                                   '3305997.545209896',
                                                   '3306555.545432123',
                                                   '3306667.545209896',
                                                   '3306668.545209896'],
                   ta1_schema.DBP_EVENTMSGIDS : ['1', '2', '3', '4', '5', '6'],
                   ta1_schema.DBP_EVENTMSGVALS : ['', '22', '', '44', '', ''],
                   ta1_schema.DBP_RESULTSTIME : repr(3306667.999999999),
                   ta1_schema.DBP_SENDTIME : repr(3305997.438331404),
                   ta1_schema.DBP_RETURNEDRECORDHASHES :
                                  ['ffffffffffffffffffff',
                                   '3a677e6490ff058c492d',
                                   '55f729ab502948d9375c'],
                   ta1_schema.DBP_STATUS : [],
                   ta1_schema.DBP_RETURNEDRECORDIDS : ['13857229552',
                                                       '487575939385',
                                                       '677029582263'],
                   ta1_schema.DBP_TESTCASEID : '001',
                   ta1_schema.DBP_SELECTIONCOLS : '*',
                   ta1_schema.DBP_ISMODIFICATIONQUERY : 0,
                   ta1_schema.DBP_ISTHROUGHPUTQUERY : 0}

    # copy of command id 34-2
    gold_mod_query = {ta1_schema.DBP_PERFORMERNAME : 'IBM',
                      ta1_schema.DBP_FQID : 5847,
                      ta1_schema.DBP_QUERYLATENCY : repr(670.5616685952991),
                      ta1_schema.DBP_EVENTMSGTIMES : ['3305997.438667347',
                                                      '3305997.448667347',
                                                      '3305997.545209896',
                                                      '3306555.545432123',
                                                      '3306667.545209896',
                                                      '3306668.545209896'],
                      ta1_schema.DBP_EVENTMSGIDS : ['1', '2', '3', '4', '5', '6'],
                      ta1_schema.DBP_EVENTMSGVALS : ['', '22', '', '44', '', ''],
                      ta1_schema.DBP_RESULTSTIME : repr(3306667.999999999),
                      ta1_schema.DBP_SENDTIME : repr(3305997.438331404),
                      ta1_schema.DBP_RETURNEDRECORDHASHES :
                                     ['ffffffffffffffffffff',
                                      '3a677e6490ff058c492d',
                                      '55f729ab502948d9375c'],
                      ta1_schema.DBP_STATUS : [],
                      ta1_schema.DBP_RETURNEDRECORDIDS : ['13857229552',
                                                          '487575939385',
                                                          '677029582263'],
                      ta1_schema.DBP_TESTCASEID : '001',
                      ta1_schema.DBP_SELECTIONCOLS : '*',
                      ta1_schema.DBP_ISMODIFICATIONQUERY : 1,
                      ta1_schema.DBP_ISTHROUGHPUTQUERY : 0}
    # copy of command id 34-2
    gold_tp_query = {ta1_schema.DBP_PERFORMERNAME : 'IBM',
                      ta1_schema.DBP_FQID : 5847,
                      ta1_schema.DBP_QUERYLATENCY : repr(670.5616685952991),
                      ta1_schema.DBP_EVENTMSGTIMES : ['3305997.438667347',
                                                      '3305997.448667347',
                                                      '3305997.545209896',
                                                      '3306555.545432123',
                                                      '3306667.545209896',
                                                      '3306668.545209896'],
                      ta1_schema.DBP_EVENTMSGIDS : ['1', '2', '3', '4', '5', '6'],
                      ta1_schema.DBP_EVENTMSGVALS : ['', '22', '', '44', '', ''],
                      ta1_schema.DBP_RESULTSTIME : repr(3306667.999999999),
                      ta1_schema.DBP_SENDTIME : repr(3305997.438331404),
                      ta1_schema.DBP_RETURNEDRECORDHASHES :
                                     ['ffffffffffffffffffff',
                                      '3a677e6490ff058c492d',
                                      '55f729ab502948d9375c'],
                      ta1_schema.DBP_STATUS : [],
                      ta1_schema.DBP_RETURNEDRECORDIDS : ['13857229552',
                                                          '487575939385',
                                                          '677029582263'],
                      ta1_schema.DBP_TESTCASEID : '001',
                      ta1_schema.DBP_SELECTIONCOLS : '*',
                      ta1_schema.DBP_ISMODIFICATIONQUERY : 0,
                      ta1_schema.DBP_ISTHROUGHPUTQUERY : 1}

    gold_log = """[2936548.490002438] 2013-05-30 13:34:43 IBM-dbname-001_something_something
[2936548.490002438] Invoked from /home/lincoln/spar-testing/bin/
[2936548.490002438] NOTE: ID x-y QID z = x-globalID, y-localID, z-resultsDBQueryID
[3305996.925772338] VariableDelayQueryRunner queries/10T/p3-notes3.sql 1 NO_DELAY
[3305997.437652770] EPOCH_TIME: 1305997.437652770
[3305997.437999763] ID 33-1 sent
[3305997.438091660] ID 33-1 QID 2384: [[SELECT id FROM main WHERE CONTAINED_IN(notes3, 'tourments')]]
[3305997.438119056] ID 34-2 QID 5847: [[SELECT * FROM main WHERE CONTAINED_IN(notes3, 'erit')]]
[3305997.438120347] ID 34-2 event 0 occurred
[3305997.438122770] EPOCH_TIME: 1305997.438122770
[3305997.438141846] ID 35-3 QID 28: [[SELECT id FROM main WHERE CONTAINED_IN(notes3, 'nehmen')]]
[3305997.438163889] ID 36-4 QID 90: [[SELECT id, data FROM main WHERE CONTAINED_IN(notes3, 'l\'ennemi')]]
[3305997.438331404] ID 34-2 sent
[3305997.438567347] ID 35-3 sent
[3305997.438667347] ID 34-2 event 1 occurred
[3305997.438817853] ID 36-4 sent
[3305997.448667347] ID 34-2 event 2 with value [[22]] occurred
[3305997.545109896] ID 33-1 results:
380267814454218
95438468284621
44435731644979
42825118908495
205058918580953
404590214250850
348897373323835
[3305997.545209896] ID 34-2 event 3 occurred
349017632408193
279383327637992
178893977813230
425210352239438
318944271401057
425738633216567
416371309544263
171815871709769
273198574731828
410555923825061
386091790107092
[3306550.545432123] ID 35-3 results:
111111111111111
FAILED
Some
failure
results
ENDFAILED
555555555555555
FAILED
Second
failure
[3306555.545432123] ID 34-2 event 4 with value [[44]] occurred
results
ENDFAILED
999999999999999
[3306667.545209896] ID 34-2 event 5 occurred
[3306667.545109896] ID 36-4 results:
123
456
789

[3306667.999999999] ID 34-2 results:
677029582263 55f729ab502948d9375c
487575939385 3a677e6490ff058c492d
13857229552 ffffffffffffffffffff
[3306668.545209896] ID 34-2 event 6 occurred
[3306669.545209896] ID 99-9 event 6 occurred
[3306669.545209897] END_OF_LOG
"""

    gold_log_abort = """[2936548.490002438] 2013-05-30 13:34:43 IBM-dbname-001_something_something
[2936548.490002438] Invoked from /home/lincoln/spar-testing/bin/
[2936548.490002438] NOTE: ID x-y QID z = x-globalID, y-localID, z-resultsDBQueryID
[3305996.925772338] VariableDelayQueryRunner queries/10T/p3-notes3.sql 1 NO_DELAY
[3305997.437652770] EPOCH_TIME: 1305997.437652770
[3305997.437999763] ID 33-1 sent
[3305997.438091660] ID 33-1 QID 2384: [[SELECT id FROM main WHERE CONTAINED_IN(notes3, 'tourments')]]
[3305997.438119056] ID 34-2 QID 5847: [[SELECT * FROM main WHERE CONTAINED_IN(notes3, 'erit')]]
[3305997.438120347] ID 34-2 event 0 occurred
[3305997.438122770] EPOCH_TIME: 1305997.438122770
[3305997.438141846] ID 35-3 QID 28: [[SELECT id FROM main WHERE CONTAINED_IN(notes3, 'nehmen')]]
[3305997.438163889] ID 36-4 QID 90: [[SELECT id, data FROM main WHERE CONTAINED_IN(notes3, 'l\'ennemi')]]
[3305997.438331404] ID 34-2 sent
[3305997.438567347] ID 35-3 sent
[3305997.438667347] ID 34-2 event 1 occurred
[3305997.438817853] ID 36-4 sent
[3305997.448667347] ID 34-2 event 2 with value [[22]] occurred
[3305997.545109896] ID 33-1 results:
380267814454218
95438468284621
44435731644979
42825118908495
205058918580953
404590214250850
348897373323835
[3305997.545209896] ID 34-2 event 3 occurred
349017632408193
279383327637992
178893977813230
425210352239438
318944271401057
425738633216567
416371309544263
171815871709769
273198574731828
410555923825061
386091790107092
[3306550.545432123] ID 35-3 results:
111111111111111
FAILED
Some
failure
results
ENDFAILED
555555555555555
FAILED
Second
failure
[3306555.545432123] ID 34-2 event 4 with value [[44]] occurred
results
ENDFAILED
999999999999999
[3306667.545209896] ID 34-2 event 5 occurred
[3306667.545109896] ID 36-4 results:
123
456
789

[3306667.999999999] ID 34-2 results:
677029582263 55f729ab502948d9375c
487575939385 3a677e6490ff058c492d
13857229552 ffffffffffffffffffff
[3306668.545209896] ID 34-2 event 6 occurred
[3306669.545209896] ID 99-9 event 6 occurred
[3306670.437999763] ID 39-1 sent
[3306670.438091660] ID 39-1 QID 1123: [[SELECT id FROM main WHERE CONTAINED_IN(notes3, 'basketball')]]
[3306670.545109896] ID 39-1 results:
425210352239438
318944271401057
425738633216567
416371309544263
171815871709769
"""


    def _ut_record_func(self, query_info, command_id, results_db):
        """Test function to fake writing of data to a DB"""
        if (command_id == "33-1"):
            self.assertEqual(query_info, self.gold_query1)
        elif (command_id == "36-4"):
            self.assertEqual(query_info, self.gold_query2)
        # FAILED query test
        elif (command_id == "35-3"):
            self.assertEqual(query_info, self.gold_query3)
        # Query with hashes in results and select * and events
        elif (command_id == "34-2"):
            self.assertEqual(query_info, self.gold_query4)
        # Test for process_query()
        elif (command_id == '10-1'):
            self.assertEqual(query_info, self.gold_query4)
        # Test modification query for process_query()
        elif (command_id == '10-2'):
            self.assertEqual(query_info, self.gold_mod_query)
        # Test throughput query for process_query()
        elif (command_id == '10-3'):
            self.assertEqual(query_info, self.gold_tp_query)
        else:
            self.failureException('Unexpected command_id found')
        return 1

    def test_parse_queries(self):
        """Test parsing logfile and generating query dict in memory"""
        gold_records = 4
        log_parser = log_parser_util.LogParserUtil()
        test_log = StringIO.StringIO(self.gold_log) 
        flags = {'mod' : False, 'throughput' : False, 'baseline' : False }
        (ut_records, unused_baseline_matches) = \
            parse_client_harness.parse_queries(log_parser,
                                               test_log,
                                               self._ut_record_func,
                                               None, flags)
        self.assertEqual(ut_records, gold_records)
        
    def test_parse_queries_abort(self):
        """Test parsing logfile and generating query dict in memory"""
        gold_records = 5
        log_parser = log_parser_util.LogParserUtil()
        test_log = StringIO.StringIO(self.gold_log_abort) 
        flags = {'mod' : False, 'throughput' : False, 'baseline' : False }
        (ut_records, unused_baseline_matches) = \
            parse_client_harness.parse_queries(log_parser,
                                               test_log,
                                               self._ut_record_func,
                                               None, flags)
        self.assertEqual(ut_records, gold_records)

    def test_process_matches(self):
        """Test conversion of matches hash to two lists.  One of ids, one of
           hashes sorted by ids"""
        with_hashes = {555555555 : 'aaaaaaaaa',
                       999999999 : '000000000',
                       111111111 : 'fffffffff'}
        no_hashes = {555555555 : '',
                     999999999 : '',
                     111111111 : ''}
        gold_ids = ['111111111', '555555555', '999999999']
        gold_hashes = ['fffffffff', 'aaaaaaaaa', '000000000']

        # Test with hashes
        (test_ids, test_hashes) = \
            parse_client_harness.process_matches(with_hashes)
        self.assertEqual(test_ids, gold_ids)
        self.assertEqual(test_hashes, gold_hashes)

        # Test without hashes
        (test_ids, test_hashes) = \
            parse_client_harness.process_matches(no_hashes)
        self.assertEqual(test_ids, gold_ids)
        self.assertEqual(test_hashes, [])

    def test_process_query(self):
        """Test preparation of a query that has results for insertion
           into the DB."""

        # Based on global gold_query4
        test_matches = {'13857229552' : 'ffffffffffffffffffff',
                        '487575939385' : '3a677e6490ff058c492d',
                        '677029582263' : '55f729ab502948d9375c'}
        test_events = {'3305997.438667347' : ['1', ''],
                       '3305997.448667347' : ['2', '22'],
                       '3305997.545209896' : ['3', ''],
                       '3306555.545432123' : ['4', '44'],
                       '3306667.545209896' : ['5', ''],
                       '3306668.545209896' : ['6', '']}
        good_query = {ta1_schema.DBP_PERFORMERNAME : 'IBM',
                      ta1_schema.DBP_FQID : 5847,
                      ta1_schema.DBP_QUERYLATENCY : repr(670.5616685952991),
                      ta1_schema.DBP_RESULTSTIME : repr(3306667.999999999),
                      ta1_schema.DBP_SENDTIME : repr(3305997.438331404),
                      ta1_schema.DBP_STATUS : [],
                      ta1_schema.DBP_TESTCASEID : '001',
                      ta1_schema.DBP_SELECTIONCOLS : '*'}

        bad_query = {ta1_schema.DBP_PERFORMERNAME : 'IBM',
                     ta1_schema.DBP_FQID : 28,
                     ta1_schema.DBP_QUERYLATENCY : repr(553.1068647759967),
                     ta1_schema.DBP_RESULTSTIME : repr(3306550.545432123),
                     ta1_schema.DBP_SENDTIME : repr(3305997.438567347),
                     ta1_schema.DBP_STATUS : ['FAILED', 'Some', 'failure',
                                              'results'], 
                     ta1_schema.DBP_TESTCASEID : '001'}

        log_parser = log_parser_util.LogParserUtil()
        flags = {'mod' : False, 'throughput' : False, 'baseline' : False}
        ret = parse_client_harness.process_query(log_parser, good_query, \
                                                 '10-1', test_matches, \
                                                 test_events, None, \
                                                 self._ut_record_func, flags)
        self.assertTrue(ret)
        ret = parse_client_harness.process_query(log_parser, bad_query, \
                                                 '10-1', test_matches, \
                                                 test_events, None, \
                                                 self._ut_record_func, flags)
        self.assertFalse(ret)
        good_query[ta1_schema.DBP_ISMODIFICATIONQUERY] = 1
        flags['mod'] = True
        ret = parse_client_harness.process_query(log_parser, good_query, \
                                                 '10-2', test_matches, \
                                                 test_events, None, \
                                                 self._ut_record_func, flags)
        self.assertTrue(ret)
        good_query[ta1_schema.DBP_ISMODIFICATIONQUERY] = 0
        good_query[ta1_schema.DBP_ISTHROUGHPUTQUERY] = 1
        flags['mod'] = False
        flags['throughput'] = True
        ret = parse_client_harness.process_query(log_parser, good_query, \
                                                 '10-3', test_matches, \
                                                 test_events, None, \
                                                 self._ut_record_func, flags)
        self.assertTrue(ret)
