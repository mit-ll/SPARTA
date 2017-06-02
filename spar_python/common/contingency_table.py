# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        A class that allows you to get a contigency table for any
#                      subset of variables.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  26 Jan 2012   omd            Original Version
# *****************************************************************

import spar_python.common.default_dict as dd

class ContingencyTable(dd.DefaultDict):
    """A contigency table maps combinations of variables to the number of times
    those combinations occur. This class takes a weighted data set and
    constructs a contigency table from it. It can then compute sub-tables for
    just a subset of the variables."""
    def __init__(self, data = None):
        """Constructor. Builds a contingency table from data.

        Note that most users will always supply data. The only reason data is
        allowed to be NULL is so get_subtable can efficiently create another
        ContingencyTable without needing to supply data to the constructor.

        Arguments:
            data: an iterable that returns (weight, record).
        """
        dd.DefaultDict.__init__(self, 0)
        if data:
            self.__build_base_table(data)

    def __build_base_table(self, data):
        """Construct the contigency table."""
        self.__total_count = 0
        for weight, record in data:
            assert weight > 0
            record = tuple(record)
            self[record] += weight
            self.__total_count += weight

    @property
    def total_count(self):
        """Returns the sum of the weights in all records supplied to the
        constructor."""
        return self.__total_count

    @property
    def total_not_all_none_count(self):
        """Returns total_count less the value of the record for which all values
        of the key are None. In other words, if the keys are tuples of length 3
        this would return total_count - self[(None, None, None)]."""
        if len(self) == 0:
            return 0
        else:
            key_len = len(self.iterkeys().next())
            none_key = (None,) * key_len
            return self.total_count - self[none_key]

    def get_subtable(self, *args):
        """This assumes that the records supplied to the constructor are tuples.
        In that case args should be a list of indices into those tuples. This
        then returns a new ContingencyTable that is the same as what you'd get
        if you took the original data but replaced each record with
        record[args] (e.g. just those items in record specified by args).
        
        See the unit tests for examples."""
        subtable = ContingencyTable()
        for key, val in self.iteritems():
            assert val > 0
            new_key = tuple([key[i] for i in args])
            subtable[new_key] += val
        subtable.__total_count = self.__total_count
        return subtable
