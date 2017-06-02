# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for ArrayView 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  13 Jan 2012   omd            Original Version
# *****************************************************************

import unittest
from array_view import ArrayView
from array_view import get_array_view_or_slice
import numpy

class ArrayViewTest(unittest.TestCase):
    def test_is_view(self):
        """Make sure that a view is really a view: e.g. that changes to it are
        reflected in the base array and vice versa."""
        base = numpy.array([1, 2, 3, 4, 5])
        view = ArrayView(base, [0, 2])
        self.assertEqual(view[0], 1)
        self.assertEqual(view[1], 3)

        # Now modify base. The changes should be reflected in the view.
        base[2] = 100
        self.assertEqual(view[0], 1)
        self.assertEqual(view[1], 100)
        self.assertEqual(base[0], 1)
        self.assertEqual(base[2], 100)

        # Now modify the view. The changes should be reflected in base.
        view[1] = 3
        self.assertEqual(view[0], 1)
        self.assertEqual(view[1], 3)
        self.assertEqual(base[0], 1)
        self.assertEqual(base[2], 3)

    def test_view_slices(self):
        """We should be able to get and set via slices as well and still preserve
        the view property."""
        base = numpy.arange(0, 100)
        view = ArrayView(base, [0, 20, 22, 50, 77])
        self.assertEqual(view[0], 0)
        self.assertEqual(view[1], 20)
        self.assertEqual(view[2], 22)
        self.assertEqual(view[3], 50)
        self.assertEqual(view[4], 77)

        # The [:] slice should just be the same view again.
        same_view = view[:]
        self.assertEqual(same_view[0], 0)
        self.assertEqual(same_view[1], 20)
        self.assertEqual(same_view[2], 22)
        self.assertEqual(same_view[3], 50)
        self.assertEqual(same_view[4], 77)

        # And it should really be a view
        same_view[1] = 1
        self.assertEqual(same_view[1], 1)
        self.assertEqual(view[1], 1)
        self.assertEqual(base[20], 1)
        same_view[1] = 20

        base[77] = -1
        self.assertEqual(view[4], -1)
        self.assertEqual(same_view[4], -1)
        base[77] = 77

        # And other slices should work as well
        middle_two = view[1:3]
        self.assertEqual(middle_two[0], 20)
        self.assertEqual(middle_two[1], 22)

        # and it too should be a view
        middle_two[0] = 0
        self.assertEqual(middle_two[0], 0)
        self.assertEqual(base[20], 0)
        middle_two[0] = 20


    def test_iteration(self):
        base = numpy.arange(0, 100)
        view = ArrayView(base, [0, 20, 22, 50, 77])
        expected = [0, 20, 22, 50, 77]
        for expected, observed in zip(expected, view):
            self.assertEqual(expected, observed)

    def test_len(self):
        base = numpy.arange(0, 100)
        view = ArrayView(base, [0, 20, 22, 50, 77])
        self.assertEqual(len(view), 5)

    def test_contains(self):
        base = numpy.arange(0, 100)
        view = ArrayView(base, [0, 20, 22, 50, 77])
        self.assertTrue(20 in view)
        self.assertTrue(22 in view)
        self.assertFalse(1 in view)
        self.assertFalse(19 in view)

    def test_add(self):
        """Simple addition of arrays should work."""
        base = numpy.array([0, 1, 1, 0])
        # view = [1, 0]
        view = ArrayView(base, [1, 3])
        added = view + numpy.array([1, 1])
        self.assertEqual(added[0], 2)
        self.assertEqual(added[1], 1)

    def test_plus_equal(self):
        """The += operator should work and since it's a view it should modify
        both the view and the base array."""
        base = numpy.array([0, 1, 1, 0])
        # view = [1, 0]
        view = ArrayView(base, [1, 3])
        view += numpy.array([1, 1])
        
        self.assertEqual(view[0], 2)
        self.assertEqual(view[1], 1)

        # make sure base was modified too
        self.assertEqual(base[1], 2)
        self.assertEqual(base[3], 1)

    def test_plus_equal_two_views(self):
        """Test that += works correctly with a view on the left and right of the
        assignment."""
        base1 = numpy.array([0, 1, 1, 0])
        base2 = numpy.array([1, 1, 1, 1])
        # view1 == [1, 0]
        view1 = ArrayView(base1, [1, 3])
        # veiw2 == [1, 1]
        view2 = ArrayView(base2, [0, 2])

        view1 += view2

        self.assertEqual(view1[0], 2)
        self.assertEqual(view1[1], 1)

        # make sure base was modified too
        self.assertEqual(base1[1], 2)
        self.assertEqual(base1[3], 1)

        # view2 and base2 should be unmodified
        self.assertEqual(view2[0], 1)
        self.assertEqual(view2[1], 1)
        self.assertTrue(numpy.all(base2 == numpy.array([1, 1, 1, 1])))

    def test_other_in_place_math(self):
        """I've overrident most of the other "in place" math operators like -=,
        %=, etc. Here we test some of them and, in parcticular, make sure
        they're modifying the base array."""
        base = numpy.array([0, 1, 1, 0])
        # view = [1, 0]
        view = ArrayView(base, [1, 3])
        
        view -= numpy.array([1, 2])

        self.assertEqual(view[0], 0)
        self.assertEqual(view[1], -2)

        self.assertEqual(base[0], 0)
        self.assertEqual(base[1], 0)
        self.assertEqual(base[2], 1)
        self.assertEqual(base[3], -2)

        base = numpy.array([0, 1, 1, 0])
        # view = [1, 0]
        view = ArrayView(base, [1, 3])
        view *= numpy.array([2, 2])

        self.assertEqual(view[0], 2)
        self.assertEqual(view[1], 0)

        self.assertEqual(base[0], 0)
        self.assertEqual(base[1], 2)
        self.assertEqual(base[2], 1)
        self.assertEqual(base[3], 0)
    
    def test_get_array_view_or_slice(self):
        """Make sure the get_array_view_or_slice method returns the right thing
        and that the returned slice contains the right data."""
        base = numpy.array([0, 1, 2, 3, 4, 5])

        # contiguous indices should be a slice
        s1 = get_array_view_or_slice(base, [0, 1, 2, 3])
        self.assertEqual(type(s1), numpy.ndarray)
        self.assertEqual(len(s1), 4)
        self.assertEqual(s1[0], 0)
        self.assertEqual(s1[1], 1)
        self.assertEqual(s1[2], 2)
        self.assertEqual(s1[3], 3)
        # and the slice should act as a view
        s1[0] = -1
        self.assertEqual(base[0], -1)
        base[0] = 100
        self.assertEqual(s1[0], 100)

        # Put it back the way it was.
        base[0] = 0

        # And make sure it works if the start index isn't 0
        s2 = get_array_view_or_slice(base, [2, 3])
        self.assertEqual(type(s2), numpy.ndarray)
        self.assertEqual(len(s2), 2)
        self.assertEqual(s2[0], 2)
        self.assertEqual(s2[1], 3)

        # And make sure an ArrayView is returned if the indices aren't
        # contiguous
        av = get_array_view_or_slice(base, [0, 1, 3])
        self.assertEqual(type(av), ArrayView)
        self.assertEqual(len(av), 3)
        self.assertEqual(av[0], 0)
        self.assertEqual(av[1], 1)
        self.assertEqual(av[2], 3)



