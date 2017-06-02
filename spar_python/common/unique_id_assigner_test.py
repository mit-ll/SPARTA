# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for uniqe id assigner 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  12 Jan 2012   omd            Original Version
# *****************************************************************

from unique_id_assigner import UniqueIdAssigner
import unittest

class UniqueIdAssignerTest(unittest.TestCase):
    def test_basic(self):
        ua = UniqueIdAssigner()
        self.assertEqual(ua.insert('hello'), 0)
        self.assertEqual(ua.insert('world'), 1)
        self.assertEqual(ua.insert('oliver'), 2)
        self.assertEqual(ua.get_id('world'), 1)
        self.assertEqual(ua.get_id('oliver'), 2)
        self.assertEqual(ua.get_key(2), 'oliver')
        self.assertEqual(ua.get_key(0), 'hello')
