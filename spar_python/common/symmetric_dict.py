# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        A wrapper around a dictionary that has keys that are
#                      2-tuples .
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 Feb 2012   omd            Original Version
# *****************************************************************

class SymmetricDict(object):
    """If you have a dictionary that has 2-tuples as keys and you know that
    d[(i,j)] == d[(j, i)] for any i and j then can you wrap your dict with a
    SymmetricDict and only store 1/2 the data. This is particularly useful if
    the base dictionary is a MemoTable as you can then also cut in half the
    amount of computation performed."""
    def __init__(self, base_dict):
        """base_dict is either an empty or filled in dictionary (though if
        filled in it should contain only entries for the tuple (i, j) where i <=
        j).

        SymmetricDict will use base_dict to store all items but will first
        re-order keys so it's only storing (or retreiving or modifying) entries
        where i <= j. Thus if a user looks up (20, 2) SymmetricDict will look up
        (2, 20) in base_dict and return that."""
        self.__base_dict = base_dict

    @staticmethod
    def __get_ordered_key(key1, key2):
        if key1 > key2:
            return (key2, key1)
        else:
            return (key1, key2)

    def __getitem__(self, key_tuple):
        return self.__base_dict[self.__get_ordered_key(*key_tuple)]

    def __setitem__(self, key_tuple, value):
        key = self.__get_ordered_key(*key_tuple)
        self.__base_dict[key] = value

    def __contains__(self, key_tuple):
        key = self.__get_ordered_key(*key_tuple)
        return key in self.__base_dict
