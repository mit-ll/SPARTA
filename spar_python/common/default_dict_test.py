# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for DefaultDict 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  14 Dec 2011   omd            Original Version
# *****************************************************************

import unittest
from default_dict import DefaultDict

class DefaultDictTest(unittest.TestCase):
    def test_dict(self):
        """Test that it behaves like a regular dictionary if we don't try to
        access items that aren't in the dict."""
        d = DefaultDict(0)
        d['a'] = 1
        d[2] = 'b'
        self.assertEqual(d['a'], 1)
        self.assertEqual(d[2], 'b')

        self.assertFalse('c' in d)
        self.assertTrue('a' in d)

        # Comparing a DefaultDict to a regular dict should work as expected.
        d2 = {'a': 1, 2: 'b'}
        self.assertEqual(d, d2)

        # The value for 'a' is different so these should not be equal
        d3 = {'a': 3, 2: 'b'}
        self.assertNotEqual(d, d3)

        # d4 has an extra element, 'c', so not equal
        d4 = {'a': 1, 2: 'b', 'c': 5}
        self.assertNotEqual(d, d4)

        # d5 is missing a key and so should not be equal
        d5 = {'a': 1}
        self.assertNotEqual(d, d5)

    def test_constructors(self):
        """Make sure the regular dictionary constructors still work."""
        dd1 = DefaultDict(0, {1: 'a', 2: 'b', 3: 'c'})
        rd1 = {1: 'a', 2: 'b', 3: 'c'}
        self.assertEqual(dd1, rd1)

        dd2 = DefaultDict(0, ((1, 'a'), (2, 'b'), (3, 'c')))
        rd2 = dict(((1, 'a'), (2, 'b'), (3, 'c')))
        self.assertEqual(dd2, rd2)
        self.assertEqual(dd2, dd1)

    def test_defaults(self):
        """Test that the default part of a DefaultDict works as expected."""
        # DefaultDict with a default value of 1 and some initial elements.
        dd = DefaultDict(1, {'a': 1, 'b': 2, 'c': 3})
        # default values for all keys
        self.assertEqual(dd['d'], 1)
        self.assertEqual(dd['e'], 1)

        # Checking for keys does not add them to the dict
        self.assertFalse('d' in dd)
        self.assertFalse('e' in dd)

        # but other keys work as expected
        self.assertEqual(dd['a'], 1)
        self.assertEqual(dd['b'], 2)
        self.assertEqual(dd['c'], 3)

        # += should work as expected

        # 'a': 1 so adding one it should be 2
        dd['a'] += 1
        # 'd' should get the default of 1 and have 1 added so it should be 2
        dd['d'] += 1
        # 'e' has default of 1 + 5 == 6
        dd['e'] += 5
        # Check all values in the dict to make sure the ones we didn't modify
        # remain unchanged.
        self.assertEqual(dd['a'], 2)
        self.assertEqual(dd['b'], 2)
        self.assertEqual(dd['c'], 3)
        self.assertEqual(dd['d'], 2)
        self.assertEqual(dd['e'], 6)

