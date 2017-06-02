# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Tim Meunier
#  Description:        Unit tests for the perfomer encrypted
#                      circuit log file parser
# *****************************************************************

import unittest
import StringIO
import collections

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta2.ta2_schema as ta2_schema
import spar_python.analytics.ta2.parse_circuit_log as parse_circuit_log

class ParseCircuitLogTest(unittest.TestCase):
    '''Test performer encrypted circuit log parser'''

    gold_log = """TEST: these_are_BIG_circuits /home/lincoln/spar-testing/tests/ta2/testfile/IBM2-circuit-001-these_are_BIG_circuits.ts
TIME: 2013-05-30 13:34:43
Invoked from /home/lincoln/spar-testing/bin/
PERFORMER: IBM2
RECOVERY
KEYPARAMS: /home/lincoln/spar-testing/tests/ta2/params/5.params
TIME: 2013-05-30 13:34:44
KEYGEN: 0.00128211
KEYTRANSMIT: 1.1383e-05
KEYSIZE: 7
CIRCUIT: /home/lincoln/spar-testing/tests/ta2/circuits/1.cir
TIME: 2013-05-30 13:34:45
INGESTION: 0.0763259
CIRCUITTRANSMIT: 10.6568
INPUT: /home/lincoln/spar-testing/tests/ta2/inputs/57.input
TIME: 2013-05-30 13:34:55
ENCRYPT: 0.00013619
INPUTTRANSMIT: 4.2838e-05
INPUTSIZE: 202
EVAL: 0.328568
OUTPUTTRANSMIT: 9.15502e-06
OUTPUTSIZE: 1
DECRYPTED RESULT: 1
DECRYPT: 0.000103113
INPUT: /home/lincoln/spar-testing/tests/ta2/inputs/103.input
TIME: 2013-05-30 13:35:08
ENCRYPT: 0.00013619
INPUTTRANSMIT: 4.2838e-05
INPUTSIZE: 202
EVAL: 0.328568
OUTPUTTRANSMIT: 9.15502e-06
OUTPUTSIZE: 1
DECRYPTED RESULT: 1
DECRYPT: 0.000103113
KEYPARAMS: /home/lincoln/spar-testing/tests/ta2/params/15.params
TIME: 2013-05-30 13:35:21
KEYGEN: 0.00555211
KEYTRANSMIT: 1.1383e-08
KEYSIZE: 9
CIRCUIT: /home/lincoln/spar-testing/tests/ta2/circuits/23.cir
TIME: 2013-05-30 13:35:22
INGESTION: 0.0763259
CIRCUITTRANSMIT: 10.6568
KEYPARAMS: /home/lincoln/spar-testing/tests/ta2/params/19.params
TIME: 2013-05-30 13:35:32
KEYGEN: 0.09128211
KEYTRANSMIT: 1.0003e-05
KEYSIZE: 10
CIRCUIT: /home/lincoln/spar-testing/tests/ta2/circuits/102.cir
TIME: 2013-05-30 13:35:34
INGESTION: 0.0763259
CIRCUITTRANSMIT: 10.6568
INPUT: /home/lincoln/spar-testing/tests/ta2/inputs/004.input
TIME: 2013-05-30 13:35:44
ENCRYPT: 0.00013619
INPUTTRANSMIT: 4.2838e-05
INPUTSIZE: 202
EVAL: 0.328568
OUTPUTTRANSMIT: 9.15502e-06
OUTPUTSIZE: 1
DECRYPTED RESULT: 1
DECRYPT: 0.000103113
INPUT: /home/lincoln/spar-testing/tests/ta2/inputs/999.input
TIME: 2013-05-30 13:50:00
ENCRYPT: 0.00013619
INPUTTRANSMIT: 4.2838e-05
INPUTSIZE: 202
EVAL: 0.328568
OUTPUTTRANSMIT: 9.15502e-06
OUTPUTSIZE: 1
DECRYPT: 0.000103113"""


    gold_results = collections.defaultdict(list,
                   {ta2_schema.PERKEYGEN_TABLENAME :
                         [{ta2_schema.PERKEYGEN_LATENCY : '0.00128211',
                           ta2_schema.PERKEYGEN_TIMESTAMP : '2013-05-30 13:34:44',
                           ta2_schema.PERKEYGEN_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PERKEYGEN_PID : 5,
                           ta2_schema.PERKEYGEN_PERFORMERNAME : 'IBM2',
                           ta2_schema.PERKEYGEN_TRANSMITLATENCY : '1.1383e-05',
                           ta2_schema.PERKEYGEN_KEYSIZE : '7',
                           ta2_schema.PERKEYGEN_RECOVERY : 1},
                          {ta2_schema.PERKEYGEN_LATENCY : '0.00555211',
                           ta2_schema.PERKEYGEN_TIMESTAMP : '2013-05-30 13:35:21',
                           ta2_schema.PERKEYGEN_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PERKEYGEN_PID : 15,
                           ta2_schema.PERKEYGEN_PERFORMERNAME : 'IBM2',
                           ta2_schema.PERKEYGEN_TRANSMITLATENCY : '1.1383e-08',
                           ta2_schema.PERKEYGEN_KEYSIZE : '9'},
                          {ta2_schema.PERKEYGEN_LATENCY : '0.09128211',
                           ta2_schema.PERKEYGEN_TIMESTAMP : '2013-05-30 13:35:32',
                           ta2_schema.PERKEYGEN_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PERKEYGEN_PID : 19,
                           ta2_schema.PERKEYGEN_PERFORMERNAME : 'IBM2',
                           ta2_schema.PERKEYGEN_TRANSMITLATENCY : '1.0003e-05',
                           ta2_schema.PERKEYGEN_KEYSIZE : '10'}],
                    ta2_schema.PERINGESTION_TABLENAME :
                         [{ta2_schema.PERINGESTION_LATENCY : '0.0763259',
                           ta2_schema.PERINGESTION_CID : 1,
                           ta2_schema.PERINGESTION_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PERINGESTION_PERFORMERNAME : 'IBM2',
                           ta2_schema.PERINGESTION_TIMESTAMP : '2013-05-30 13:34:45',
                           ta2_schema.PERINGESTION_TRANSMITLATENCY : '10.6568'},
                          {ta2_schema.PERINGESTION_LATENCY : '0.0763259',
                           ta2_schema.PERINGESTION_CID : 23,
                           ta2_schema.PERINGESTION_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PERINGESTION_PERFORMERNAME : 'IBM2',
                           ta2_schema.PERINGESTION_TIMESTAMP : '2013-05-30 13:35:22',
                           ta2_schema.PERINGESTION_TRANSMITLATENCY : '10.6568'},
                          {ta2_schema.PERINGESTION_LATENCY : '0.0763259',
                           ta2_schema.PERINGESTION_CID : 102,
                           ta2_schema.PERINGESTION_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PERINGESTION_PERFORMERNAME : 'IBM2',
                           ta2_schema.PERINGESTION_TIMESTAMP : '2013-05-30 13:35:34',
                           ta2_schema.PERINGESTION_TRANSMITLATENCY : '10.6568'}],
                    ta2_schema.PEREVALUATION_TABLENAME :
                         [{ta2_schema.PEREVALUATION_DECRYPTIONLATENCY : '0.000103113',
                           ta2_schema.PEREVALUATION_ENCRYPTIONLATENCY : '0.00013619',
                           ta2_schema.PEREVALUATION_TIMESTAMP : '2013-05-30 13:34:55',
                           ta2_schema.PEREVALUATION_INPUTTRANSMITLATENCY : '4.2838e-05',
                           ta2_schema.PEREVALUATION_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PEREVALUATION_IID : 57,
                           ta2_schema.PEREVALUATION_PERFORMERNAME : 'IBM2',
                           ta2_schema.PEREVALUATION_OUTPUT : '1',
                           ta2_schema.PEREVALUATION_OUTPUTTRANSMITLATENCY : '9.15502e-06',
                           ta2_schema.PEREVALUATION_INPUTSIZE : '202',
                           ta2_schema.PEREVALUATION_OUTPUTSIZE : '1',
                           ta2_schema.PEREVALUATION_EVALUATIONLATENCY : '0.328568'},
                          {ta2_schema.PEREVALUATION_DECRYPTIONLATENCY : '0.000103113',
                           ta2_schema.PEREVALUATION_ENCRYPTIONLATENCY : '0.00013619',
                           ta2_schema.PEREVALUATION_TIMESTAMP : '2013-05-30 13:35:08',
                           ta2_schema.PEREVALUATION_INPUTTRANSMITLATENCY : '4.2838e-05',
                           ta2_schema.PEREVALUATION_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PEREVALUATION_IID : 103,
                           ta2_schema.PEREVALUATION_PERFORMERNAME : 'IBM2',
                           ta2_schema.PEREVALUATION_OUTPUT : '1',
                           ta2_schema.PEREVALUATION_OUTPUTTRANSMITLATENCY : '9.15502e-06',
                           ta2_schema.PEREVALUATION_INPUTSIZE : '202',
                           ta2_schema.PEREVALUATION_OUTPUTSIZE : '1',
                           ta2_schema.PEREVALUATION_EVALUATIONLATENCY : '0.328568'},
                          {ta2_schema.PEREVALUATION_DECRYPTIONLATENCY : '0.000103113',
                           ta2_schema.PEREVALUATION_ENCRYPTIONLATENCY : '0.00013619',
                           ta2_schema.PEREVALUATION_TIMESTAMP : '2013-05-30 13:35:44',
                           ta2_schema.PEREVALUATION_INPUTTRANSMITLATENCY : '4.2838e-05',
                           ta2_schema.PEREVALUATION_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PEREVALUATION_IID : 4,
                           ta2_schema.PEREVALUATION_PERFORMERNAME : 'IBM2',
                           ta2_schema.PEREVALUATION_OUTPUT : '1',
                           ta2_schema.PEREVALUATION_OUTPUTTRANSMITLATENCY : '9.15502e-06',
                           ta2_schema.PEREVALUATION_INPUTSIZE : '202',
                           ta2_schema.PEREVALUATION_OUTPUTSIZE : '1',
                           ta2_schema.PEREVALUATION_EVALUATIONLATENCY : '0.328568'},
                          {ta2_schema.PEREVALUATION_DECRYPTIONLATENCY : '0.000103113',
                           ta2_schema.PEREVALUATION_ENCRYPTIONLATENCY : '0.00013619',
                           ta2_schema.PEREVALUATION_TIMESTAMP : '2013-05-30 13:50:00',
                           ta2_schema.PEREVALUATION_INPUTTRANSMITLATENCY : '4.2838e-05',
                           ta2_schema.PEREVALUATION_TESTNAME : 'these_are_BIG_circuits',
                           ta2_schema.PEREVALUATION_IID : 999,
                           ta2_schema.PEREVALUATION_PERFORMERNAME : 'IBM2',
                           ta2_schema.PEREVALUATION_OUTPUT : '',
                           ta2_schema.PEREVALUATION_OUTPUTTRANSMITLATENCY : '9.15502e-06',
                           ta2_schema.PEREVALUATION_INPUTSIZE : '202',
                           ta2_schema.PEREVALUATION_OUTPUTSIZE : '1',
                           ta2_schema.PEREVALUATION_EVALUATIONLATENCY : '0.328568',
                           ta2_schema.PEREVALUATION_STATUS : 'FAILED'}]})
    maxDiff = None

    def setUp(self):
        '''Prepair shared variables for all tests.'''
        self.circuit_parser = parse_circuit_log.CircuitParser(':memory:')

    def test_parse_log(self):
        '''Test log file parsing and results population.'''
        test_log = StringIO.StringIO(self.gold_log)
        self.circuit_parser.parse_log(test_log)
        self.assertEqual(dict(self.circuit_parser.results), dict(self.gold_results))

    @unittest.skip("OUTATIME")
    def test_process_results(self):
        '''Test applying results to the DB.'''
        self.circuit_parser.results = self.gold_results
        self.circuit_parser.process_results()
        ### TODO
        self.assertTrue(True)

    def test_get_id_from_filename(self):
        '''Test extracting id from a file path.'''
        test_path1 = '/home/lincoln/spar-testing/tests/ta2/circuits/102.cir'
        gold_id1 = 102
        test_path2 = '201.cir'
        gold_id2 = 201
        self.assertEqual(gold_id1, self.circuit_parser.get_id_from_filename( \
                                       test_path1))
        self.assertEqual(gold_id2, self.circuit_parser.get_id_from_filename( \
                                       test_path2))

    def test_is_token_valid(self):
        '''Test verification that the found token is in the list of expected
           tokens.'''
        good_token = 'KEYSIZE'
        bad_token = 'DECRYPT'
        self.circuit_parser.table_name = ta2_schema.PERKEYGEN_TABLENAME
        self.assertTrue(self.circuit_parser.is_token_valid(good_token))
        self.assertFalse(self.circuit_parser.is_token_valid(bad_token))

    def test_check_tokens(self):
        '''Test the check for row completeness.'''
        self.circuit_parser.table_name = ta2_schema.PERKEYGEN_TABLENAME
        test_row = dict(self.gold_results[self.circuit_parser.table_name][0])

        self.circuit_parser.check_tokens(test_row)
        self.assertEqual(test_row, self.gold_results \
                                            [self.circuit_parser.table_name][0])

        test_bad_row = dict(self.gold_results \
                                     [self.circuit_parser.table_name][0])
        gold_bad_row = dict(test_bad_row)
        del test_bad_row['keysize']
        gold_bad_row['keysize'] = ''
        gold_bad_row['status'] = 'FAILED'
        self.circuit_parser.check_tokens(test_bad_row)
        self.assertEqual(test_bad_row, gold_bad_row)
