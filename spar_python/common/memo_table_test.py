# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for MemoTable 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  02 Feb 2012   omd            Original Version
# *****************************************************************

import unittest
from memo_table import MemoTable
import time
import spar_python.common.default_dict as dd

class MemoTableTest(unittest.TestCase):
    def test_values_correct(self):
        """Create a function that computes the square of its argument. Then wrap
        a memo-table around that and make sure we get the correct values for
        things."""
        def square(x):
            return x * x

        mt = MemoTable(square)

        # We check each value twice as the 1st time it should be computed while
        # the second it should come from the MemoTable.
        self.assertEqual(mt[2], 4)
        self.assertEqual(mt[2], 4)

        self.assertEqual(mt[4], 16)
        self.assertEqual(mt[4], 16)

    def test_memo_faster(self):
        """Bascially the same test as above but we make the square function
        really slow (to square 100 it'll add 100 to itself 100 times). Then we
        make sure it's much faster to get a value the 2nd time than it is the
        first as the 2nd time it should be memo-ized while the 1st it had to be
        computed."""
        # Note: this uses time.clock() which is CPU time *used by this process*
        # on Linux and is thus an accurate reflection of how much time it took
        # to compute things. However, on Windows, clock() returns wall-clock
        # time. As a result this test won't be hugely robust on Windows as other
        # processes might steal the CPU while this is executing and cause the
        # test to fail. Since this is designed for Linux and the test is fairly
        # robust (e.g. we only check that it's 20x as fast even though it should
        # be at least 1000x as fast) it shouldn't matter much.
        def slow_square(x):
            answer = 0.0
            for _ in xrange(x):
                answer += x
            return answer

        mt = MemoTable(slow_square)

        # Time to compute squares of 1000 different values
        NUM_COMPUTE = 1000
        # start with 100 so computing its square is slow
        MIN_VAL = 1000
        # pre-allocate the array so timing doesn't include heap operations.
        computed_vals = [0] * NUM_COMPUTE
        t1 = time.clock()
        for i, x in enumerate(xrange(MIN_VAL, MIN_VAL + NUM_COMPUTE)):
            computed_vals[i] = mt[x]
        t2 = time.clock()
        time_compute = t2 - t1

        lookup_vals = [0] * NUM_COMPUTE
        t1 = time.clock()
        for i, x in enumerate(xrange(MIN_VAL, MIN_VAL + NUM_COMPUTE)):
            lookup_vals[i] = mt[x]
        t2 = time.clock()
        time_lookup = t2 - t1

        # Should be *at least* 20x as fast
        self.assertLess(time_lookup, time_compute / 20.0)
        for a, b in zip(lookup_vals, computed_vals):
            self.assertEqual(a, b)

    def test_called_only_once(self):
        """This ensures that the MemoTable calls its supplied function exactly
        once for each key no matter how many times the key is looked up. This is
        perhaps a better test that test_memo_faster so perhaps that test should
        be removed??"""
        calls_per_key = dd.DefaultDict(0)
        def memo_fun(x):
            calls_per_key[x] += 1
            return x

        mt = MemoTable(memo_fun)
        # Lookup keys 0 - 9  5 times each
        NUM_LOOKUPS = 5
        for i in xrange(NUM_LOOKUPS):
            for j in xrange(10):
                self.assertEqual(mt[j], j)

        for i in xrange(10):
            self.assertEqual(calls_per_key[i], 1)

        # And just to be thorough, look up a few string values
        self.assertEqual(mt['hello'], 'hello')
        self.assertEqual(mt['hello'], 'hello')
        self.assertEqual(mt['hello'], 'hello')
        self.assertEqual(mt['hello'], 'hello')
        self.assertEqual(calls_per_key['hello'], 1)

    def test_immutable(self):
        """It should not be possible to manually set a value in a MemoTable."""
        def square(x):
            return x ** 2

        mt = MemoTable(square)
        with self.assertRaises(TypeError):
            mt[10] = 100

        self.assertEqual(mt[10], 100)
        with self.assertRaises(TypeError):
            mt[10] = 100

        
