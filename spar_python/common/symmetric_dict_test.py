# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for SymmetricDict. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 Feb 2012   omd            Original Version
# *****************************************************************

import unittest
from symmetric_dict import SymmetricDict
from memo_table import MemoTable

class SymmetricDictTest(unittest.TestCase):
    def test_retreival(self):
        """Create a SymmetricDict from a dict that already has values for some
        pairs and make sure I can retrive the symmetric versions."""
        base = {(1, 5): (1, 5),
                (3, 10): (3, 10),
                (2, 2): (2, 2),
                (1, 4): (1, 4)}

        sd = SymmetricDict(base)

        self.assertEqual(sd[1, 5], (1, 5))
        self.assertEqual(sd[5, 1], (1, 5))

        self.assertEqual(sd[3, 10], sd[10, 3])
        self.assertEqual(sd[10, 3], (3, 10))

        self.assertEqual(sd[2, 2], (2, 2))

    def test_set_and_get(self):
        """Create an empty SymmetricDict, set items and retrieve them."""
        sd = SymmetricDict({})
        sd[1, 3] = 'hello'
        self.assertEqual(sd[3, 1], 'hello')
        self.assertEqual(sd[1, 3], 'hello')

        sd[1, 2] = 'goodbye'
        self.assertEqual(sd[1, 2], 'goodbye')
        self.assertEqual(sd[2, 1], 'goodbye')

        sd[1, 1] = 100
        self.assertEqual(sd[1, 1], 100)

    def test_tuples_work(self):
        """Like the test above but instead of passing [i, j] we pass the tuple
        (i, j). It shoud work the same."""
        sd = SymmetricDict({})
        sd[(1, 3)] = 'hello'
        self.assertEqual(sd[3, 1], 'hello')
        self.assertEqual(sd[1, 3], 'hello')
        self.assertEqual(sd[(3, 1)], 'hello')
        self.assertEqual(sd[(1, 3)], 'hello')

    def test_contains(self):
        """Test the that the in operator works correctly."""
        sd = SymmetricDict({})
        sd[1, 2] = 100
        self.assertTrue((1, 2) in sd)
        self.assertTrue((2, 1) in sd)
        
        self.assertFalse((3, 2) in sd)
        sd[2, 3] = 200
        self.assertTrue((3, 2) in sd)

    def test_memo_table(self):
        """Make sure it works with a MemoTable as the base table."""

        # Create a MemoTable that computes the product of its arguments. Also
        # give it a set to track which keys it was called with so we can make
        # sure the function is only called once per symmetric key pair.
        called_keys = set()
        def multiple_args(key):
            called_keys.add(key)
            self.assertEqual(len(key), 2)
            return key[0] * key[1]
        
        mt = MemoTable(multiple_args)
        sd = SymmetricDict(mt)
        self.assertEqual(sd[2, 3], 6)
        self.assertTrue((2, 3) in called_keys)
        self.assertFalse((3, 2) in called_keys)
        self.assertEqual(sd[3, 2], 6)
        self.assertFalse((3, 2) in called_keys)

        self.assertFalse((4, 5) in called_keys)
        self.assertFalse((5, 4) in called_keys)
        self.assertEqual(sd[5, 4], 20)
        self.assertTrue((4, 5) in called_keys)
        self.assertFalse((5, 4) in called_keys)
        self.assertEqual(sd[4, 5], 20)
        self.assertTrue((4, 5) in called_keys)
        self.assertFalse((5, 4) in called_keys)
