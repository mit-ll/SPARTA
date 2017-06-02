# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Ariel
#  Description:        Tests for the query ids classes
# *****************************************************************

import os
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.query_generation.query_ids as qids
import unittest


class QueryIdsResultTest(unittest.TestCase):

    def setUp(self):
        pass
    
    def testAtomicWhere(self):
        self.assertEqual(qids.atomic_where_has_been_seen(1,"it"), 1)
        self.assertEqual(qids.atomic_where_has_been_seen(2,"it"), 1)
        qids.reset_atomic_where()
        self.assertEqual(qids.atomic_where_has_been_seen(1,"it"), 1)
    
    def testFullWhere(self):
        self.assertEqual(qids.full_where_has_been_seen(1,"it"), 1)
        self.assertEqual(qids.full_where_has_been_seen(2,"it"), 1)
        qids.reset_full_where()
        self.assertEqual(qids.full_where_has_been_seen(1,"it"), 1)
        
    def testAtomicQID(self):
        qids.reset_atomic_qid_seen()
        self.assertEqual(qids.atomic_qid_seen(100), False)
        self.assertEqual(qids.atomic_qid_seen(100), True)
        qids.reset_atomic_qid_seen()
        self.assertEqual(qids.atomic_qid_seen(100), False)
        
    def testFullQID(self):
        qids.reset_full_qid_seen()
        self.assertEqual(qids.full_qid_seen(100), False)
        self.assertEqual(qids.full_qid_seen(100), True)
        qids.reset_full_qid_seen()
        self.assertEqual(qids.full_qid_seen(100), False)