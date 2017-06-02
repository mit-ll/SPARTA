# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Wraps cPickle.load so you can iterate through
#                      a file of pickled objects.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  18 Apr 2012   omd            Original Version
# *****************************************************************

import cPickle

class PickleIter(object):
    def __init__(self, file_obj):
        self.__file = file_obj

    def __iter__(self):
        return self.generate()

    def generate(self):
        while True:
            try:
                obj = cPickle.load(self.__file)
                yield obj
            except EOFError, e:
                break
            
