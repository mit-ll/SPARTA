#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      commented_file_iterator.py 
# *****************************************************************

import StringIO
import unittest
from commented_file_iterator import CommentedFileIterator

class CommentedFileIteratorTest(unittest.TestCase):
    '''Unit tests for commented_file_iterators'''
    
    def test_commented_file_iterator(self):
        '''test for CommentedFileIterator class
        
        Instantiate a few objects with different comment characters,
        ensure each returns the appropriate non-commeneted lines'''
        pound_lines = ["# line of text\n", "#another line of text\n",
                        "###########\n"]
        dollar_lines = ["$ line of text\n", "$another line of text\n",
                         "$$$$$$$$$$$$$$$\n"]
        abc_lines = ["abc line of text\n", "abcanother line of text\n", 
                     "abcabcabcabcabcabcabc\n"]
    
        mystring = StringIO.StringIO(''.join(pound_lines) +
                                  ''.join(dollar_lines) + ''.join(abc_lines))
    
        myfile = CommentedFileIterator(mystring)

        for i in range(len(dollar_lines)):
            self.assertEqual(dollar_lines[i], myfile.next())
        for i in range(len(abc_lines)):
            self.assertEqual(abc_lines[i], myfile.next())
    
        mystring.seek(0)
        
        myfile = CommentedFileIterator(mystring, commentstring="$")

        for i in range(len(pound_lines)):
            self.assertEqual(pound_lines[i], myfile.next())
        for i in range(len(abc_lines)):
            self.assertEqual(abc_lines[i], myfile.next())

        mystring.seek(0)
        myfile = CommentedFileIterator(mystring, commentstring="abc")

        for i in range(len(pound_lines)):
            self.assertEqual(pound_lines[i], myfile.next())
        for i in range(len(dollar_lines)):
            self.assertEqual(dollar_lines[i], myfile.next())