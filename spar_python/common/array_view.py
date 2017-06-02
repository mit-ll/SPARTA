# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Complex views of numpy arrays 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  12 Jan 2012   omd            Original Version
# *****************************************************************

import numpy

def get_array_view_or_slice(array, indices):
    """A slice is much faster than an array view (it's implemented in C rather
    than Python) but sometimes it's hard to know in your code if a slice is
    possible (e.g. if all the indices are contiguous). This is common, for
    example, in our neural net code when creating views of node outputs to be
    the inputs to other nodes - often all upstream nodes are connected
    downstream so tha a slice would work, but not always. This method checks the
    indices and, if they form a valid slice a slice is returned. Otherwise an
    ArrayView is returned. Since these objects have the same interface that
    works fine."""
    nexti = indices[0]
    for idx in indices:
        if idx != nexti:
            return ArrayView(array, indices)
        nexti += 1

    # If we made it here all the indices were contiguous so we can return a
    # slice.
    return array[indices[0]:indices[-1] + 1]

class ArrayView(object):
    """numpy supports "views" of array for standard slices. For example:

    a = numpy.array([1, 1, 1, 1])
    v = a[1:2]
    # Modifies the base array since it's a "view"
    v[0] += 1
    assert a[1] == 2

    Unfortuantely the view support does not extend to "fancy indexing" in which
    an array of indices is passed. This class allows us to create views using
    fancy indexing too. See the unit tests to get a sense for how this works."""
    def __init__(self, array, indices):
        """Create a view of array that includes only the indices specified by
        the  iterable indices."""
        assert isinstance(array, numpy.ndarray)
        assert len(numpy.shape(array)) == 1
        self.__array = array
        self.__indices = indices

    def __getitem__(self, index):
        if isinstance(index, slice):
            # See if it's the [:] slice in which case just return self.
            # Otherwise create a new ArrayView object with the new indices
            s = index.indices(len(self.__indices))
            if s == (0, len(self.__indices), 1):
                return self
            else:
                return ArrayView(self.__array, self.__indices[index])
        else:
            array_indices = self.__indices[index]
            return self.__array[array_indices]

    def __setitem__(self, index, value):
        array_indices = self.__indices[index]
        self.__array[array_indices] = value

    def __len__(self):
        return len(self.__indices)

    def __iter__(self):
        return iter(self.__array[self.__indices])

    def __contains__(self, item):
        return item in self.__array[self.__indices]

    def __iadd__(self, other):
        self.__array[self.__indices] += other
        return self

    def __isub__(self, other):
        self.__array[self.__indices] -= other
        return self

    def __imul__(self, other):
        self.__array[self.__indices] *= other
        return self

    def __idiv__(self, other):
        self.__array[self.__indices] /= other
        return self

    def __ifloordiv__(self, other):
        self.__array[self.__indices] //= other
        return self

    def __imod__(self, other):
        self.__array[self.__indices] %= other
        return self

    def __ipow__(self, other):
        self.__array[self.__indices] **= other
        return self


