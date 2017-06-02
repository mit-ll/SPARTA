#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module containts the unit tests for
#                      file_utils.py 
# *****************************************************************

import unittest
import os
import sys
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
from spar_python.perf_monitoring.file_utils import CollectlFileIterator
from csv import DictReader
import StringIO


class FileUtilsTest(unittest.TestCase):
    '''Unit tests for file_utils'''
               
    def test_collectl_file_iterator(self):
        '''test for CollectlFileIterator class'''
        
        comments = ['#COMMENT LINE 1\n', '# COMMENT 2\n', '############ COMMENT 3 ######\n']
        header = ['#Date,Time,Number\n']
        data = ['20130102,01:23:45.56,5\n','20120807,15:30:00.001,7']
        
        mystring = StringIO.StringIO(''.join(comments) + ''.join(header) + ''.join(data))
        myfile = CollectlFileIterator(mystring)
        reader = DictReader(myfile)
        
        self.assertEqual(reader.fieldnames, ["Date", "Time", "Number"])
        
        entry1 = reader.next()
        entry2 = reader.next()     
        
        self.assertEqual(entry1["Date"], "20130102")
        self.assertEqual(entry1["Time"], "01:23:45.56")
        self.assertEqual(entry1["Number"], "5")
        self.assertEqual(entry2["Date"], "20120807")
        self.assertEqual(entry2["Time"], "15:30:00.001")
        self.assertEqual(entry2["Number"], "7")
        
        
        
        