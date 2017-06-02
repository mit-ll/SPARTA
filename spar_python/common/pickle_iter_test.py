# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for PickleIter 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  18 Apr 2012   omd            Original Version
# *****************************************************************

from StringIO import StringIO
import unittest
from pickle_iter import PickleIter
import cPickle

class PickleIterTest(unittest.TestCase):
    def test_basic(self):
        # A bunch of objects to pickle
        to_pickle = [
                'hello', 22, ['a', 'list of', 'strings'],
                {'a': 22, 'dictionary': 44}]
        file_obj = StringIO()
        for obj in to_pickle:
            cPickle.dump(obj, file_obj)

        # Now rewind the file pointer and iterate through the objects making
        # sure we get back what we put in.
        file_obj.seek(0)
        unpickled = [obj for obj in PickleIter(file_obj)]
        self.assertEqual(unpickled, to_pickle)
