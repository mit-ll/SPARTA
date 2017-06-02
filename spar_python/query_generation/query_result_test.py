# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jill
#  Description:        Tests for the query results classes
# *****************************************************************

import os
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.query_generation.query_schema as qs
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.report_generation.ta1.ta1_database as ta1_database        
import spar_python.query_generation.query_result as qr
import spar_python.query_generation.query_ids as qids
import unittest

class SelectStarTest(unittest.TestCase):
    def setUp(self):
        self.__query = { qs.QRY_CAT : 'eq',
                   qs.QRY_SUBCAT : '',
                   qs.QRY_DBNUMRECORDS : 30,
                   qs.QRY_DBRECORDSIZE : 1003,
                   qs.QRY_QID : 1,
                   qs.QRY_PERF : ['LL'],
                   qs.QRY_WHERECLAUSE : 'fname = nick',
                   qs.QRY_FIELD : 'FNAME',
                   qs.QRY_FIELDTYPE : 'string',
                   qs.QRY_VALUE : 'nick' }
        self.__result = { qs.QRY_QID : 1,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
    def testQueryResult(self):
        qids.reset_full_qid_seen()
        count = 0
        for x in xrange(10):
           self.__query[qs.QRY_QID]=x
           query_result = qr.EqualityQueryResult(self.__query, self.__result,
                                              None, True)

           (_, full_entry, _, _) = query_result.process_query()
           if full_entry[rdb.DBF_SELECTSTAR]:
               count += 1
        self.assertEqual(count,2)

    def testPreWriteToFullTable(self):
        qids.reset_full_qid_seen()
        count = 0
        for x in xrange(10):
           self.__query[qs.QRY_QID]=x
           full_entry= qr.QueryResultBase._pre_write_to_full_table(self.__query, 
                                                                   self.__result)

           if full_entry[rdb.DBF_SELECTSTAR]:
               count +=1
        self.assertEqual(count,2)
             
class EqualityQueryResultTest(unittest.TestCase):
    """
    Test that the EqualityQueryResults class acts as expected.
    """

    def setUp(self):
        ''' setup for test '''
        query1 = { qs.QRY_CAT : 'eq',
                   qs.QRY_SUBCAT : '',
                   qs.QRY_DBNUMRECORDS : 30,
                   qs.QRY_DBRECORDSIZE : 1003,
                   qs.QRY_QID : 1,
                   qs.QRY_PERF : ['LL'],
                   qs.QRY_WHERECLAUSE : 'fname = nick',
                   qs.QRY_FIELD : 'FNAME',
                   qs.QRY_FIELDTYPE : 'string',
                   qs.QRY_VALUE : 'nick' }
        result1 = { qs.QRY_QID : 1,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        self.__query1 = query1
        self.__result1 = result1
        self.__query1_atomic_entry = \
            { rdb.DBA_AQID : query1[qs.QRY_QID],
              rdb.DBA_CAT : query1[qs.QRY_CAT],
              rdb.DBA_SUBCAT : query1[qs.QRY_SUBCAT],
              rdb.DBA_NUMRECORDS : query1[qs.QRY_DBNUMRECORDS],
              rdb.DBA_RECORDSIZE : query1[qs.QRY_DBRECORDSIZE],
              rdb.DBA_WHERECLAUSE : query1[qs.QRY_WHERECLAUSE],
              rdb.DBA_FIELD : query1[qs.QRY_FIELD],
              
              rdb.DBA_FIELDTYPE : query1[qs.QRY_FIELDTYPE],
              rdb.DBA_NUMMATCHINGRECORDS : 2 }
        self.__query1_full_entry = \
            { rdb.DBF_FQID : 1,
              rdb.DBF_CAT : query1[qs.QRY_CAT],
              rdb.DBF_SUBCAT : query1[qs.QRY_SUBCAT],
              rdb.DBF_IBM1SUPPORTED : "IBM1" in query1[qs.QRY_PERF],
              rdb.DBF_IBM2SUPPORTED : "IBM2" in query1[qs.QRY_PERF],
              rdb.DBF_COLUMBIASUPPORTED : "COL" in query1[qs.QRY_PERF],
              rdb.DBF_NUMRECORDS : query1[qs.QRY_DBNUMRECORDS],
              rdb.DBF_RECORDSIZE : query1[qs.QRY_DBRECORDSIZE],
              rdb.DBF_WHERECLAUSE : query1[qs.QRY_WHERECLAUSE],
              rdb.DBF_NUMMATCHINGRECORDS : 2,
              rdb.DBF_MATCHINGRECORDIDS : set([1, 3]),
              rdb.DBF_SELECTSTAR : True }
        self.__query1_full_to_atomic_entry = \
            { rdb.F2A_AQID : 1, rdb.F2A_FQID : 1 }

        # no matches
        self.__query1_atomic_entry_no_matches = dict(self.__query1_atomic_entry)
        self.__query1_atomic_entry_no_matches[rdb.DBA_NUMMATCHINGRECORDS] = 0
        self.__query1_full_entry_no_matches = dict(self.__query1_full_entry)
        self.__query1_full_entry_no_matches[rdb.DBF_NUMMATCHINGRECORDS] = 0
        self.__query1_full_entry_no_matches[rdb.DBF_MATCHINGRECORDIDS] = set()
    
    def test_process_repeat_query(self):
        ''' test process_query with repeats'''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.EqualityQueryResult(self.__query1, self.__result1,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry)
        self.assertEqual(full_entry, self.__query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

        # test again but pass in None for results
        query_result = qr.EqualityQueryResult(self.__query1, None,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        self.assertEqual(atomic_entry, {})
        self.assertEqual(full_entry, {})
        self.assertEqual(full_to_atomic_entry, {})
        self.assertEqual(full_to_full_entry, {})
        
    def test_process_query(self):
        ''' test process_query '''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.EqualityQueryResult(self.__query1, self.__result1,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry)
        self.assertEqual(full_entry, self.__query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

        # test again but pass in None for results
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.EqualityQueryResult(self.__query1, None,
                                              None, True)
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry_no_matches)
        self.assertEqual(full_entry, self.__query1_full_entry_no_matches)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

    def test_write_query(self):
        ''' test write_query '''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_result = qr.EqualityQueryResult(self.__query1, self.__result1,
                                           db_object, True)
        query_result.write_query()
        db_object.close()
        
    def test_init_method(self):
        ''' test __init__ method '''
        query_result = qr.EqualityQueryResult(self.__query1, self.__result1,
                                              None, True)
        self.assertEqual(query_result._query, self.__query1)
        self.assertEqual(query_result._result, self.__result1)
        self.assertEqual(query_result._top, True)
        self.assertEqual(query_result._db_object, None)





class P2QueryResultTest(unittest.TestCase):
    """
    Test that the EqualityQueryResults class acts as expected.
    """

    def setUp(self):
        ''' setup for test '''
        query1 = { qs.QRY_CAT : 'P2',
                   qs.QRY_SUBCAT : 'foorange',
                   qs.QRY_DBNUMRECORDS : 3,
                   qs.QRY_DBRECORDSIZE : 100,
                   qs.QRY_QID : 1,
                   qs.QRY_PERF : ['LL'],
                   qs.QRY_WHERECLAUSE : '100 <= foo <= 500',
                   qs.QRY_FIELD : 'foo',
                   qs.QRY_FIELDTYPE : 'integer',
                   qs.QRY_LBOUND : 100,
                   qs.QRY_UBOUND : 500,
                   qs.QRY_RANGE : 4,
                   qs.QRY_RANGECOVERAGE : 400}
        result1 = { qs.QRY_QID : 1,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        self.__query1 = query1
        self.__result1 = result1
        self.__query1_atomic_entry = \
            { rdb.DBA_AQID : query1[qs.QRY_QID],
              rdb.DBA_CAT : query1[qs.QRY_CAT],
              rdb.DBA_SUBCAT : query1[qs.QRY_SUBCAT],
              rdb.DBA_NUMRECORDS : query1[qs.QRY_DBNUMRECORDS],
              rdb.DBA_RECORDSIZE : query1[qs.QRY_DBRECORDSIZE],
              rdb.DBA_WHERECLAUSE : query1[qs.QRY_WHERECLAUSE],
              rdb.DBA_FIELD : query1[qs.QRY_FIELD],
              rdb.DBA_FIELDTYPE : query1[qs.QRY_FIELDTYPE],
              rdb.DBA_NUMMATCHINGRECORDS : 2,
              rdb.DBA_RANGE : 4}
        self.__query1_full_entry = \
            { rdb.DBF_FQID : 1,
              rdb.DBF_CAT : query1[qs.QRY_CAT],
              rdb.DBF_SUBCAT : query1[qs.QRY_SUBCAT],
              rdb.DBF_IBM1SUPPORTED : "IBM1" in query1[qs.QRY_PERF],
              rdb.DBF_IBM2SUPPORTED : "IBM2" in query1[qs.QRY_PERF],
              rdb.DBF_COLUMBIASUPPORTED : "COL" in query1[qs.QRY_PERF],
              rdb.DBF_NUMRECORDS : query1[qs.QRY_DBNUMRECORDS],
              rdb.DBF_RECORDSIZE : query1[qs.QRY_DBRECORDSIZE],
              rdb.DBF_WHERECLAUSE : query1[qs.QRY_WHERECLAUSE],
              rdb.DBF_NUMMATCHINGRECORDS : 2,
              rdb.DBF_SELECTSTAR : True,
              rdb.DBF_MATCHINGRECORDIDS : set([1, 3]) }
        self.__query1_full_to_atomic_entry = \
            { rdb.F2A_AQID : 1, rdb.F2A_FQID : 1 }

        # no matches
        self.__query1_atomic_entry_no_matches =  dict(self.__query1_atomic_entry)
        self.__query1_atomic_entry_no_matches[rdb.DBA_NUMMATCHINGRECORDS] = 0
        self.__query1_full_entry_no_matches = dict(self.__query1_full_entry)
        self.__query1_full_entry_no_matches[rdb.DBF_NUMMATCHINGRECORDS] = 0
        self.__query1_full_entry_no_matches[rdb.DBF_MATCHINGRECORDIDS] = set()

    def test_process_repeat_query(self):
        ''' test process_query with repeats'''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P2QueryResult(self.__query1, self.__result1,
                                        None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry)
        self.assertEqual(full_entry, self.__query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

        # test again but pass in None for results
        query_result = qr.P2QueryResult(self.__query1, None,
                                     None, True)
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        self.assertEqual(atomic_entry, {})
        self.assertEqual(full_entry, {})
        self.assertEqual(full_to_atomic_entry, {})
        self.assertEqual(full_to_full_entry, {})
    
    def test_process_query(self):
        ''' test process_query '''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P2QueryResult(self.__query1, self.__result1,
                                        None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry)
        self.assertEqual(full_entry, self.__query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

        # test again but pass in None for results
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P2QueryResult(self.__query1, None,
                                     None, True)
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry_no_matches)
        self.assertEqual(full_entry, self.__query1_full_entry_no_matches)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

    def test_write_query(self):
        ''' test write_query '''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_result = qr.P2QueryResult(self.__query1, self.__result1,
                                        db_object, True)
        query_result.write_query()
        db_object.close()
        
    def test_init_method(self):
        ''' test __init__ method '''
        query_result = qr.P2QueryResult(self.__query1, self.__result1,
                                        None, True)
        self.assertEqual(query_result._query, self.__query1)
        self.assertEqual(query_result._result, self.__result1)
        self.assertEqual(query_result._top, True)
        self.assertEqual(query_result._db_object, None)





class P3P4P6P7QueryResultTest(unittest.TestCase):
    """
    Test that the P3P4P6P7QueryResult class acts as expected.
    """

    def setUp(self):
        ''' setup for test '''
        query1 = { qs.QRY_CAT : 'P3',
                   qs.QRY_SUBCAT : '',
                   qs.QRY_DBNUMRECORDS : 3,
                   qs.QRY_DBRECORDSIZE : 100,
                   qs.QRY_PERF : ['LL'],
                   qs.QRY_QID : 1,
                   qs.QRY_WHERECLAUSE : "CONTAINED_IN(notes1, ''dog\''')",
                   qs.QRY_FIELD : 'notes1',
                   qs.QRY_FIELDTYPE : 'text',
                   qs.QRY_SEARCHFOR : 'dogs',
                   qs.QRY_KEYWORDLEN : 4 }
        result1 = { qs.QRY_QID : 1,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        self.__query1 = query1
        self.__result1 = result1
        self.__query1_atomic_entry = \
            { rdb.DBA_AQID : query1[qs.QRY_QID],
              rdb.DBA_CAT : query1[qs.QRY_CAT],
              rdb.DBA_SUBCAT : query1[qs.QRY_SUBCAT],
              rdb.DBA_NUMRECORDS : query1[qs.QRY_DBNUMRECORDS],
              rdb.DBA_RECORDSIZE : query1[qs.QRY_DBRECORDSIZE],
              rdb.DBA_WHERECLAUSE : query1[qs.QRY_WHERECLAUSE],
              rdb.DBA_FIELD : query1[qs.QRY_FIELD],
              rdb.DBA_FIELDTYPE : query1[qs.QRY_FIELDTYPE],
              rdb.DBA_NUMMATCHINGRECORDS : 2,
              rdb.DBA_KEYWORDLEN : query1[qs.QRY_KEYWORDLEN]}
        self.__query1_full_entry = \
            { rdb.DBF_FQID : 1,
              rdb.DBF_CAT : query1[qs.QRY_CAT],
              rdb.DBF_SUBCAT : query1[qs.QRY_SUBCAT],
              rdb.DBF_IBM1SUPPORTED : "IBM1" in query1[qs.QRY_PERF],
              rdb.DBF_IBM2SUPPORTED : "IBM2" in query1[qs.QRY_PERF],
              rdb.DBF_COLUMBIASUPPORTED : "COL" in query1[qs.QRY_PERF],
              rdb.DBF_NUMRECORDS : query1[qs.QRY_DBNUMRECORDS],
              rdb.DBF_RECORDSIZE : query1[qs.QRY_DBRECORDSIZE],
              rdb.DBF_WHERECLAUSE : query1[qs.QRY_WHERECLAUSE],
              rdb.DBF_NUMMATCHINGRECORDS : 2,
              rdb.DBF_SELECTSTAR : True,
              rdb.DBF_MATCHINGRECORDIDS : set([1, 3]) }
        self.__query1_full_to_atomic_entry = \
            { rdb.F2A_AQID : 1, rdb.F2A_FQID : 1 }

        # no matches
        self.__query1_atomic_entry_no_matches =  dict(self.__query1_atomic_entry)
        self.__query1_atomic_entry_no_matches[rdb.DBA_NUMMATCHINGRECORDS] = 0
        self.__query1_full_entry_no_matches = dict(self.__query1_full_entry)
        self.__query1_full_entry_no_matches[rdb.DBF_NUMMATCHINGRECORDS] = 0
        self.__query1_full_entry_no_matches[rdb.DBF_MATCHINGRECORDIDS] = set()
      
    def test_process_repeat_query(self):
        ''' test process_query with repeats'''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P3P4P6P7QueryResult(self.__query1, self.__result1,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry)
        self.assertEqual(full_entry, self.__query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

        # test again but pass in None for results
        query_result = qr.P3P4P6P7QueryResult(self.__query1, None,
                                              None, True)
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        self.assertEqual(atomic_entry, {})
        self.assertEqual(full_entry, {})
        self.assertEqual(full_to_atomic_entry, {})
        self.assertEqual(full_to_full_entry, {})
        
    def test_process_query(self):
        ''' test process_query '''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P3P4P6P7QueryResult(self.__query1, self.__result1,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry)
        self.assertEqual(full_entry, self.__query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

        # test again but pass in None for results
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P3P4P6P7QueryResult(self.__query1, None,
                                              None, True)
        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.__query1_atomic_entry_no_matches)
        self.assertEqual(full_entry, self.__query1_full_entry_no_matches)
        self.assertEqual(full_to_atomic_entry, 
                         self.__query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

    def test_write_query(self):
        ''' test write_query '''

        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_result = qr.P3P4P6P7QueryResult(self.__query1, self.__result1,
                                              db_object, True)
        query_result.write_query()
        db_object.close()
        
    def test_init_method(self):
        ''' test __init__ method '''
        query_result = qr.P3P4P6P7QueryResult(self.__query1, self.__result1,
                                              None, True)
        self.assertEqual(query_result._query, self.__query1)
        self.assertEqual(query_result._result, self.__result1)
        self.assertEqual(query_result._top, True)
        self.assertEqual(query_result._db_object, None)




class P9AlarmQueryResultTest(unittest.TestCase):
    """
    Test that the EqualityQueryResults class acts as expected.
    """

    def setUp(self):
        ''' setup for test '''
        self.query1 = { qs.QRY_QID : 1,
                 qs.QRY_DBNUMRECORDS : 1000,
                 qs.QRY_DBRECORDSIZE : 100, 
                 qs.QRY_CAT : 'P9',
                 qs.QRY_PERF : ['LL'],
                 qs.QRY_ENUM : qs.CAT.P9_ALARM_WORDS,
                 qs.QRY_SUBCAT : "alarmwords", 
                 qs.QRY_WHERECLAUSE : "alarm_words_distance(''outgrabe'', ''raths'') < 50",
                 qs.QRY_FIELD : 'notes3',
                 qs.QRY_NEGATE : False,
                 qs.QRY_FIELDTYPE : 'string',
                 qs.QRY_LRSS : 1,
                 qs.QRY_URSS : 10,
                 qs.QRY_ALARMWORDONE : 'outgrabe',
                 qs.QRY_ALARMWORDTWO : 'raths',
                 qs.QRY_ALARMWORDDISTANCE : 50}
        self.result1 = {'matching_record_counts': '1|1|2|2', 
                 'qid': 1, 
                 'alarmword_matching_row_id_and_distances': 
                    [(1, 22), (2, 19), (3, 50), 
                     (4, 25), (5, 25), (6, 50)], 
                 'matching_record_ids': [2,1,4,5,3,6]}
        self.query1_atomic_entry = \
            { rdb.DBA_AQID : self.query1[qs.QRY_QID],
              rdb.DBA_CAT : self.query1[qs.QRY_CAT],
              rdb.DBA_SUBCAT : self.query1[qs.QRY_SUBCAT],
              rdb.DBA_NUMRECORDS : self.query1[qs.QRY_DBNUMRECORDS],
              rdb.DBA_RECORDSIZE : self.query1[qs.QRY_DBRECORDSIZE],
              rdb.DBA_WHERECLAUSE : self.query1[qs.QRY_WHERECLAUSE],
              rdb.DBA_FIELD : self.query1[qs.QRY_FIELD],
              
              rdb.DBA_FIELDTYPE : self.query1[qs.QRY_FIELDTYPE],
              rdb.DBA_NUMMATCHINGRECORDS : 6 }
        self.query1_full_entry = \
            { rdb.DBF_FQID : 1,
              rdb.DBF_CAT : self.query1[qs.QRY_CAT],
              rdb.DBF_SUBCAT : self.query1[qs.QRY_SUBCAT],
              rdb.DBF_IBM1SUPPORTED : "IBM1" in self.query1[qs.QRY_PERF],
              rdb.DBF_IBM2SUPPORTED : "IBM2" in self.query1[qs.QRY_PERF],
              rdb.DBF_COLUMBIASUPPORTED : "COL" in self.query1[qs.QRY_PERF],
              rdb.DBF_NUMRECORDS : self.query1[qs.QRY_DBNUMRECORDS],
              rdb.DBF_RECORDSIZE : self.query1[qs.QRY_DBRECORDSIZE],
              rdb.DBF_WHERECLAUSE : self.query1[qs.QRY_WHERECLAUSE],
              rdb.DBF_NUMMATCHINGRECORDS : 6,
              rdb.DBF_MATCHINGRECORDIDS : [2,1,4,5,3,6],
              rdb.DBF_SELECTSTAR : True,
              rdb.DBF_P9MATCHINGRECORDCOUNTS : '1|1|2|2' }
        self.query1_full_to_atomic_entry = \
            { rdb.F2A_AQID : 1, rdb.F2A_FQID : 1 }

        # no matches
        self.query1_atomic_entry_no_matches = dict(self.query1_atomic_entry)
        self.query1_atomic_entry_no_matches[rdb.DBA_NUMMATCHINGRECORDS] = 0
        self.query1_full_entry_no_matches = dict(self.query1_full_entry)
        self.query1_full_entry_no_matches[rdb.DBF_NUMMATCHINGRECORDS] = 0
        self.query1_full_entry_no_matches[rdb.DBF_MATCHINGRECORDIDS] = []
    
    def test_process_repeat_query(self):
        ''' test process_query with repeats'''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P9AlarmQueryResult(self.query1, self.result1,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.query1_atomic_entry)
        self.assertEqual(full_entry, self.query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})

        # test again but pass in None for results
        query_result = qr.EqualityQueryResult(self.query1, None,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        self.assertEqual(atomic_entry, {})
        self.assertEqual(full_entry, {})
        self.assertEqual(full_to_atomic_entry, {})
        self.assertEqual(full_to_full_entry, {})
        
    def test_process_query(self):
        ''' test process_query '''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        query_result = qr.P9AlarmQueryResult(self.query1, self.result1,
                                              None, True)

        (atomic_entry, full_entry, full_to_atomic_entry, full_to_full_entry) = \
            query_result.process_query()
        full_entry[rdb.DBF_SELECTSTAR]=True
        self.assertEqual(atomic_entry, self.query1_atomic_entry)
        self.assertEqual(full_entry, self.query1_full_entry)
        self.assertEqual(full_to_atomic_entry, 
                         self.query1_full_to_atomic_entry)
        self.assertEqual(full_to_full_entry, {})
 

    def test_write_query(self):
        ''' test write_query '''
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
        query_result = qr.P9AlarmQueryResult(self.query1, self.result1,
                                           db_object, True)
        query_result.write_query()
        db_object.close()
        
    def test_init_method(self):
        ''' test __init__ method '''
        query_result = qr.P9AlarmQueryResult(self.query1, self.result1,
                                              None, True)
        self.assertEqual(query_result._query, self.query1)
        self.assertEqual(query_result._result, self.result1)
        self.assertEqual(query_result._top, True)
        self.assertEqual(query_result._db_object, None)
        
class StaticMethodsTest(unittest.TestCase):
    """
    Test that the QueryResultBase static methods act as expected.
    """

    def setUp(self):
        ''' setup for test '''
        self._query1 = { qs.QRY_CAT : 'P1',
                        qs.QRY_SUBCAT : 'eq_and',
                        qs.QRY_ENUM : qs.CAT.P1_EQ_AND,
                        qs.QRY_DBNUMRECORDS : 30,
                        qs.QRY_DBRECORDSIZE : 1003,
                        qs.QRY_QID : 1,
                        qs.QRY_PERF : ['LL'],
                        qs.QRY_WHERECLAUSE : 'fname = nick AND lname = jones',
                        qs.QRY_NUMTERMSPERCLAUSE : 3,
                        qs.QRY_NUMCLAUSES : 2 }

        sub_result1 = { qs.QRY_QID : 2,
                        rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        sub_result2 = { qs.QRY_QID : 3,
                        rdb.DBF_MATCHINGRECORDIDS : set([1,3,5]) }

        self._result1 = \
            { qs.QRY_QID : 1,
              rdb.DBF_MATCHINGRECORDIDS : set([1,3]),
              qs.QRY_NUMRECORDSMATCHINGFIRSTTERM : 2,
              qs.QRY_SUBRESULTS : [sub_result1, sub_result2]
              }



        self._query2 = { qs.QRY_CAT : 'P1',
                        qs.QRY_SUBCAT : 'eq_not',
                        qs.QRY_ENUM : qs.CAT.P1_EQ_NOT,
                        qs.QRY_DBNUMRECORDS : 30,
                        qs.QRY_DBRECORDSIZE : 1003,
                        qs.QRY_QID : 2,
                        qs.QRY_WHERECLAUSE : 'NOT(fname = nick) AND NOT(lname = jones)',
                        qs.QRY_PERF : ["LL"],
                        qs.QRY_NEGATEDTERMS : set([0,1]),
                        qs.QRY_NUMTERMSPERCLAUSE : 3,
                        qs.QRY_NUMCLAUSES : 2 }

        self._result2 = \
            { qs.QRY_QID : 2,
              rdb.DBF_MATCHINGRECORDIDS : set([1,3]),
              qs.QRY_NUMRECORDSMATCHINGFIRSTTERM : 2,
              rdb.DBF_P1NEGATEDTERM : set([0,1]),
              qs.QRY_SUBRESULTS : [sub_result1, sub_result2]
              }

    def test_pre_write_to_full_table_q1(self):
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        entry = qr.QueryResultBase._pre_write_to_full_table(self._query1, 
                                                         self._result1)

        matching_record_ids = self._result1[rdb.DBF_MATCHINGRECORDIDS]
        matching_records =  len(matching_record_ids)
        gold = \
            { rdb.DBF_FQID : self._query1[qs.QRY_QID],
              rdb.DBF_CAT : self._query1[qs.QRY_CAT],
              rdb.DBF_SUBCAT : self._query1[qs.QRY_SUBCAT],
              rdb.DBF_NUMRECORDS : self._query1[qs.QRY_DBNUMRECORDS],
              rdb.DBF_RECORDSIZE : self._query1[qs.QRY_DBRECORDSIZE],
              rdb.DBF_WHERECLAUSE : self._query1[qs.QRY_WHERECLAUSE],
              rdb.DBF_IBM1SUPPORTED : "IBM1" in self._query1[qs.QRY_PERF],
              rdb.DBF_IBM2SUPPORTED : "IBM2" in self._query1[qs.QRY_PERF],
              rdb.DBF_COLUMBIASUPPORTED : "COL" in self._query1[qs.QRY_PERF],
              rdb.DBF_NUMMATCHINGRECORDS : matching_records, 
              rdb.DBF_MATCHINGRECORDIDS : matching_record_ids,
              rdb.DBF_P1NUMTERMSPERCLAUSE :
                  self._query1[qs.QRY_NUMTERMSPERCLAUSE],
              rdb.DBF_P1NUMCLAUSES : self._query1[qs.QRY_NUMCLAUSES],
              rdb.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM : \
                  self._result1[qs.QRY_NUMRECORDSMATCHINGFIRSTTERM] }
        gold[rdb.DBF_SELECTSTAR] = entry[rdb.DBF_SELECTSTAR]
        self.assertEqual(entry, gold)

    def test_pre_write_to_full_table_q2(self):
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        entry = qr.QueryResultBase._pre_write_to_full_table(self._query2, 
                                                         self._result2)

        matching_record_ids = self._result2[rdb.DBF_MATCHINGRECORDIDS]
        matching_records =  len(matching_record_ids)
        gold = \
            { rdb.DBF_FQID : self._query2[qs.QRY_QID],
              rdb.DBF_CAT : self._query2[qs.QRY_CAT],
              rdb.DBF_SUBCAT : self._query2[qs.QRY_SUBCAT],
              rdb.DBF_NUMRECORDS : self._query2[qs.QRY_DBNUMRECORDS],
              rdb.DBF_RECORDSIZE : self._query2[qs.QRY_DBRECORDSIZE],
              rdb.DBF_WHERECLAUSE : self._query2[qs.QRY_WHERECLAUSE],
              rdb.DBF_IBM1SUPPORTED : "IBM1" in self._query2[qs.QRY_PERF],
              rdb.DBF_IBM2SUPPORTED : "IBM2" in self._query2[qs.QRY_PERF],
              rdb.DBF_COLUMBIASUPPORTED : "COL" in self._query2[qs.QRY_PERF],
              rdb.DBF_NUMMATCHINGRECORDS : matching_records, 
              rdb.DBF_MATCHINGRECORDIDS : matching_record_ids,
              rdb.DBF_P1NEGATEDTERM : self._query2[qs.QRY_NEGATEDTERMS], 
              rdb.DBF_P1NUMTERMSPERCLAUSE :
                  self._query2[qs.QRY_NUMTERMSPERCLAUSE],
              rdb.DBF_P1NUMCLAUSES : self._query2[qs.QRY_NUMCLAUSES] }
        gold[rdb.DBF_SELECTSTAR] = entry[rdb.DBF_SELECTSTAR]
        self.assertEqual(entry, gold)

    def test_write_to_full_table_q1(self):
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)

        qr.QueryResultBase.write_to_full_table(self._query1, 
                                               self._result1, db_object)

        db_object._execute("SELECT * FROM " + rdb.DBF_TABLENAME)
        rows = db_object._fetchall()
        self.assertEqual(len(rows), 1) 
        
        fields = [ \
            (rdb.DBF_FQID, 1),
            (rdb.DBF_CAT, self._query1[qs.QRY_CAT]),
            (rdb.DBF_SUBCAT, self._query1[qs.QRY_SUBCAT]),
            (rdb.DBF_NUMRECORDS, self._query1[qs.QRY_DBNUMRECORDS]),
            (rdb.DBF_RECORDSIZE, self._query1[qs.QRY_DBRECORDSIZE]),
            (rdb.DBF_WHERECLAUSE, self._query1[qs.QRY_WHERECLAUSE]),
            (rdb.DBF_NUMMATCHINGRECORDS,  2),
            (rdb.DBF_MATCHINGRECORDIDS, "1|3" ),
            (rdb.DBF_P1NUMTERMSPERCLAUSE, 
             self._query1[qs.QRY_NUMTERMSPERCLAUSE]),
            (rdb.DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM, 
             self._result1[qs.QRY_NUMRECORDSMATCHINGFIRSTTERM]),
            (rdb.DBF_P1NUMCLAUSES, self._query1[qs.QRY_NUMCLAUSES]),
            (rdb.DBF_IBM1SUPPORTED,  "IBM1" in self._query1[qs.QRY_PERF]),
            (rdb.DBF_IBM2SUPPORTED, "IBM2" in self._query1[qs.QRY_PERF]),
            (rdb.DBF_COLUMBIASUPPORTED, "COL" in self._query1[qs.QRY_PERF]) ]

        for field, gold in fields:
            cmd = "SELECT " + field + " FROM " + rdb.DBF_TABLENAME
            db_object._execute(cmd)
            row = db_object._fetchone()
            # note: row is a tuple, we want the first element
            self.assertEqual(row[0], gold)

        db_object.close()
        

    def test_write_to_full_table_q2(self):
        qids.reset_atomic_qid_seen()
        qids.reset_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)

        qr.QueryResultBase.write_to_full_table(self._query2, 
                                               self._result2, db_object)

        db_object._execute("SELECT * FROM " + rdb.DBF_TABLENAME)
        rows = db_object._fetchall()
        self.assertEqual(len(rows), 1) 
        fields = [ \
            (rdb.DBF_FQID, 2),
            (rdb.DBF_CAT, self._query2[qs.QRY_CAT]),
            (rdb.DBF_SUBCAT, self._query2[qs.QRY_SUBCAT]),
            (rdb.DBF_NUMRECORDS, self._query2[qs.QRY_DBNUMRECORDS]),
            (rdb.DBF_RECORDSIZE, self._query2[qs.QRY_DBRECORDSIZE]),
            (rdb.DBF_WHERECLAUSE, self._query2[qs.QRY_WHERECLAUSE]),
            (rdb.DBF_NUMMATCHINGRECORDS,  2),
            (rdb.DBF_MATCHINGRECORDIDS, "1|3" ),
            (rdb.DBF_P1NEGATEDTERM, "0|1"), 
            (rdb.DBF_P1NUMTERMSPERCLAUSE, 
             self._query2[qs.QRY_NUMTERMSPERCLAUSE]),
            (rdb.DBF_P1NUMCLAUSES, self._query1[qs.QRY_NUMCLAUSES]),
            (rdb.DBF_IBM1SUPPORTED,  "IBM1" in self._query2[qs.QRY_PERF]),
            (rdb.DBF_IBM2SUPPORTED, "IBM2" in self._query2[qs.QRY_PERF]),
            (rdb.DBF_COLUMBIASUPPORTED, "COL" in self._query2[qs.QRY_PERF])  ]

        for field, gold in fields:
            cmd = "SELECT " + field + " FROM " + rdb.DBF_TABLENAME
            db_object._execute(cmd)
            row = db_object._fetchone()
            # note: row is a tuple, we want the first element
            self.assertEqual(row[0], gold)

        db_object.close()
        


    def test_pre_write_to_full_to_atomic_table(self):
        qids.reset_full_to_atomic_qid_seen()
        entries = \
            qr.QueryResultBase._pre_write_to_full_to_atomic_table(self._query1, 
                                                                  self._result1)
        gold = [ { rdb.F2A_FQID : 1, rdb.F2A_AQID : 2 },
                 { rdb.F2A_FQID : 1, rdb.F2A_AQID : 3 } ]
        self.assertEqual(entries, gold)


    def test_write_to_full_to_atomic_table(self):
        qids.reset_full_to_atomic_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)

        qr.QueryResultBase.write_to_full_to_atomic_table(self._query1, 
                                                         self._result1, 
                                                         db_object)

        db_object._execute("SELECT * FROM " + rdb.F2A_TABLENAME)
        rows = db_object._fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], (1,2))
        self.assertEqual(rows[1], (1,3))

        db_object.close()

    def test_pre_write_to_full_to_full_table(self):
        # note it really does not make sense to call full_to_full on a P1-and but it works to test it
        qids.reset_full_to_full_qid_seen()
        entries = \
            qr.QueryResultBase._pre_write_to_full_to_full_table(self._query1, 
                                                                self._result1)
        gold = [ { rdb.F2F_BASEQID : 1, rdb.F2F_COMPOSITEQID : 2 },
                 { rdb.F2F_BASEQID : 1, rdb.F2F_COMPOSITEQID : 3 } ]
        self.assertEqual(entries, gold)

    def test_write_to_full_to_full_table(self):
        # note it really does not make sense to call full_to_full on a P1-and but it works to test it
        qids.reset_full_to_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)

        qr.QueryResultBase.write_to_full_to_full_table(self._query1, 
                                                       self._result1, db_object)

        db_object._execute("SELECT * FROM " + rdb.F2F_TABLENAME)
        rows = db_object._fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], (1,2))
        self.assertEqual(rows[1], (1,3))

        db_object.close()
