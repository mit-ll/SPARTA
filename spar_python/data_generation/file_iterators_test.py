# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Tests for FileTokenIterator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2011   omd            Original Version

# *****************************************************************


import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

from spar_python.data_generation.file_iterators import FileTokenIterator
from StringIO import StringIO
import unittest

class FileTokenIteratorTest(unittest.TestCase):
    def test_single_line(self):
        fake_file = StringIO('This has four tokens')
        expected = ['This', 'has', 'four', 'tokens']
        actual = [x for x in FileTokenIterator(fake_file)]
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(actual, expected)

    def test_single_line_punctuation(self):
        fake_file = StringIO('This. Is a token? As.Is this.')
        expected = ['This', '.', 'Is', 'a', 'token', '?',
                'As', '.', 'Is', 'this', '.']
        actual = [x for x in FileTokenIterator(fake_file)]
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(actual, expected)

    def test_mutli_line(self):
        fake_file = StringIO('ta tb\ntc  \n\n  td')
        expected = ['ta', 'tb', 'tc', 'td']
        actual = [x for x in FileTokenIterator(fake_file)]
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(actual, expected)

    def test_skip_non_characters(self):
        fake_file = StringIO('ta 18 tb409824tc ()&* td  ')
        expected = ['ta', 'tb', 'tc', 'td']
        actual = [x for x in FileTokenIterator(fake_file)]
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(actual, expected)

