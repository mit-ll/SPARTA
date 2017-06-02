# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Test for create_ta1_scripts
#                      which does test script and query file 
#                      generation
# *****************************************************************
import sys
import string
import os
import unittest
import random
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.query_generation.query_schema as qs
import spar_python.query_generation.query_result as qr
import spar_python.query_generation.query_ids as qids
import spar_python.test_generation.create_scripts as cts
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.report_generation.ta1.ta1_database as ta1_database
import spar_python.test_generation.query_file_handler as qfh

                                                              
class QueryFileHandlerTest(unittest.TestCase):
    
    def setUp(self):
        '''
        make a fake resultdb for testing
        '''
        queries = []
        results = []
        
        query1 = { qs.QRY_CAT : 'P1',
                   qs.QRY_PERF : 'IBM1',
                   qs.QRY_SUBCAT : 'eqand',
                   qs.QRY_ENUM : qs.CAT.P1_EQ_AND,
                   qs.QRY_DBNUMRECORDS : 30,
                   qs.QRY_DBRECORDSIZE : 1003,
                   qs.QRY_QID : 1,
                   qs.QRY_WHERECLAUSE : 'fname = nick AND lname = jones',
                   qs.QRY_NUMTERMSPERCLAUSE : 3,
                   qs.QRY_NUMCLAUSES : 2 }
    
        sub_result1 = { qs.QRY_QID : 2,
                        rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        sub_result2 = { qs.QRY_QID : 3,
                        rdb.DBF_MATCHINGRECORDIDS : set([1,3,5]) }
    
        result1 = { qs.QRY_QID : 1,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]),
                    qs.QRY_NUMRECORDSMATCHINGFIRSTTERM : 2,
                    qs.QRY_SUBRESULTS : [sub_result1, sub_result2]
                    }
        queries.append(query1)
        results.append(result1)
        

        query2 = { qs.QRY_CAT : 'P1',
                   qs.QRY_SUBCAT : 'eqnot',
                   qs.QRY_PERF : 'IBM1',
                   qs.QRY_ENUM : qs.CAT.P1_EQ_NOT,
                   qs.QRY_DBNUMRECORDS : 30,
                   qs.QRY_DBRECORDSIZE : 1003,
                   qs.QRY_QID : 2,
                   qs.QRY_WHERECLAUSE : 'NOT(fname = nick) AND NOT(lname = jones)',
                   qs.QRY_NEGATEDTERMS : set([0,1]),
                   qs.QRY_NUMTERMSPERCLAUSE : 3,
                   qs.QRY_NUMCLAUSES : 2 }
        
        result2 = { qs.QRY_QID : 2,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]),
                    qs.QRY_NUMRECORDSMATCHINGFIRSTTERM : 2,
                    rdb.DBF_P1NEGATEDTERM : set([0,1]),
                    qs.QRY_SUBRESULTS : [sub_result1, sub_result2]
                    }
        queries.append(query2)
        results.append(result2)
        
        # make a bunch of equality queries
        for num in range(20):
            ran_num = random.randint(1, 100000)
            qid = 100 + num
            name = 'fred' + str(num)
            matches = set(range(ran_num)) # meaningless set of numbers
            query = { qs.QRY_CAT : 'EQ',
                      qs.QRY_SUBCAT : '',
                      qs.QRY_PERF : 'IBM1',
                      qs.QRY_DBNUMRECORDS : 30,
                      qs.QRY_DBRECORDSIZE : 1003,
                      qs.QRY_QID : qid,
                      qs.QRY_WHERECLAUSE : 'fname = ' + name,
                      qs.QRY_FIELD : 'FNAME',
                      qs.QRY_FIELDTYPE : 'string',
                      qs.QRY_VALUE : name }
            result = { qs.QRY_QID : qid,
                       rdb.DBF_MATCHINGRECORDIDS : matches }
            queries.append(query)
            results.append(result)

        # make a bunch of equality queries
        for num in range(20):
            ran_num = random.randint(1, 2000)
            qid = 1000 + num
            name = 'dan' + str(num)
            matches = set(range(ran_num)) # meaningless set of numbers
            query = { qs.QRY_CAT : 'EQ',
                      qs.QRY_SUBCAT : '',
                      qs.QRY_PERF : 'IBM1',
                      qs.QRY_DBNUMRECORDS : 30,
                      qs.QRY_DBRECORDSIZE : 1003,
                      qs.QRY_QID : qid,
                      qs.QRY_WHERECLAUSE : 'fname = ' + name,
                      qs.QRY_FIELD : 'FNAME',
                      qs.QRY_FIELDTYPE : 'string',
                      qs.QRY_VALUE : name }
            result = { qs.QRY_QID : qid,
                       rdb.DBF_MATCHINGRECORDIDS : matches }
            queries.append(query)
            results.append(result)


        query3 = { qs.QRY_CAT : 'EQ',
                   qs.QRY_SUBCAT : '',
                   qs.QRY_PERF : 'IBM1',
                   qs.QRY_DBNUMRECORDS : 30,
                   qs.QRY_DBRECORDSIZE : 1003,
                   qs.QRY_QID : 3,
                   qs.QRY_WHERECLAUSE : 'fname = nick',
                   qs.QRY_FIELD : 'FNAME',
                   qs.QRY_FIELDTYPE : 'string',
                   qs.QRY_VALUE : 'nick' }
        result3 = { qs.QRY_QID : 3,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        queries.append(query3)
        results.append(result3)
        
        query4 = { qs.QRY_CAT : 'P2',
                   qs.QRY_SUBCAT : 'foo-range',
                   qs.QRY_PERF : 'IBM1',
                   qs.QRY_DBNUMRECORDS : 30,
                   qs.QRY_DBRECORDSIZE : 1003,
                   qs.QRY_QID : 4,
                   qs.QRY_WHERECLAUSE : '100 <= foo <= 500',
                   qs.QRY_FIELD : 'foo',
                   qs.QRY_FIELDTYPE : 'integer',
                   qs.QRY_LBOUND : 100,
                   qs.QRY_UBOUND : 500,
                   qs.QRY_RANGE : 4,
                   qs.QRY_RANGECOVERAGE : 400}
        result4 = { qs.QRY_QID : 4,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        queries.append(query4)
        results.append(result4)
    
        query5 = { qs.QRY_CAT : 'P3',
                   qs.QRY_SUBCAT : '',
                   qs.QRY_PERF : 'IBM1',
                   qs.QRY_DBNUMRECORDS : 33,
                   qs.QRY_DBRECORDSIZE : 1003,
                   qs.QRY_QID : 5,
                   qs.QRY_WHERECLAUSE : 'CONTAINED_IN(notes1, \"dogs\")',
                   qs.QRY_FIELD : 'notes1',
                   qs.QRY_FIELDTYPE : 'text',
                   qs.QRY_SEARCHFOR : 'dogs',
                   qs.QRY_KEYWORDLEN : 4 }
        result5 = { qs.QRY_QID : 5,
                    rdb.DBF_MATCHINGRECORDIDS : set([1,3]) }
        queries.append(query5)
        results.append(result5)

        qids.reset_full_qid_seen()
        db_name = ':memory:'
        db_object = ta1_database.Ta1ResultsDB(db_name)
    
        for query, result in zip(queries,results):
            qr.QueryResultBase.write_to_full_table(query, 
                                                   result, db_object)
        self.resultdb = db_object
