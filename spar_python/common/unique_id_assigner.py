# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        A class that assigned unique id's to keys. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  12 Jan 2012   omd            Original Version
# *****************************************************************

class UniqueIdAssigner(object):
    """Assigns an integer, increasing id to each key in the order the keys are
    added. Example usage:

    ua = UniqueIdAssigner()
    ua.insert('hello') # return 0, the id assigned to 'hello'
    ua.insert('goodbye') # returns 1, the id assigned to 'goodbye'
    ua.get_id('hello') # returns 0
    ua.get_key(1) # returns 'goodbye'
    """
    def __init__(self):
        self.__next_id = 0
        self.__key_to_id = {}
        self.__id_to_key = {}

    def insert(self, key):
        assert not key in self.__key_to_id
        self.__key_to_id[key] = self.__next_id
        self.__id_to_key[self.__next_id] = key

        self.__next_id += 1
        # Return the id that was assigned
        return self.__next_id - 1

    def get_id(self, key):
        return self.__key_to_id[key]

    def get_key(self, id):
        return self.__id_to_key[id]
