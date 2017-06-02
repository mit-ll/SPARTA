# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill Poland
#  Description:        Unit tests for the server harness log file 
#                      parser
# *****************************************************************

import re
import unittest
import StringIO

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import spar_python.analytics.common.log_parser_util as log_parser_util


class LogParserUtilTest(unittest.TestCase):
    ''' test class for the parse server harness log file functionality '''

    def setUp(self):
        self.log_parser = log_parser_util.LogParserUtil()

    def create_sh_log_file(self):
        ''' internal routine to create a sample server harness log
        file as a StringIO object and return that object
        Note: the caller must close the object '''
        sh_log_file = StringIO.StringIO()
        sh_log_file.write('[2936548.490002438] 2013-05-30 13:34:43 IBM001\n')
        sh_log_file.write('[2936548.490002438] Invoked from /home/lincoln'
                          '/spar-testing/bin/\n')
        sh_log_file.write('[2936548.490002438] NOTE: ID x MID y = '
                          'x-globalID, y-resultsDBModificationID\n')
        sh_log_file.write('[3305997.437652770] EPOCH_TIME: '
                          '1365108319.361063719\n') 
        sh_log_file.write('[3305997.438331404] ID 0 sent\n')
        sh_log_file.write('[3305997.438567347] ID 0 MID 53: INSERT '
                          '4927728924000000000\n')
        sh_log_file.write('[3305997.545109896] ID 0 results: DONE\n')
        sh_log_file.write('[3305997.438331404] ID 1 sent\n')
        sh_log_file.write('[3305997.437652770] EPOCH_TIME: '
                          '1365108319.361063719\n')
        sh_log_file.write('[3305997.438567347] ID 1 MID 682: UPDATE '
                          '1026497184236\n')
        sh_log_file.write('[3305997.545109896] ID 1 results: DONE\n')
        sh_log_file.write('[3305997.438331404] ID 2 sent\n')
        sh_log_file.write('[3305997.438567347] ID 2 MID 53: DELETE '
                          '4927728924000000000\n')
        sh_log_file.write('[3305997.545109896] ID 2 results: DONE\n')
        file_contents = sh_log_file.getvalue()
        sh_log_file.close()
        return file_contents

    def test_compute_latency(self):
        ''' test latency method '''
        time1 = '1365108319.361742258'
        time2 = '1365108319.468520880'
        gold = 0.106778621674

        latency = self.log_parser.compute_latency(time1, time2)
        self.assertAlmostEqual(latency, gold)

    def test_resolve_timestamps(self):
        ''' resolve timestamps on the file contents and return 
        new file contents '''
        # Open a new file object with the sample file contents
        orig_file_object = StringIO.StringIO(self.create_sh_log_file())

        # Open a new file object which will contain the modified file contents
        mod_file_object = StringIO.StringIO()

        # Call the resolve timestamp program passing in both file objects
        self.log_parser.hwclock_to_epoch_log_converter(orig_file_object, \
                                                       mod_file_object)

        # close both files objects
        orig_file_object.close()
        mod_file_object.close()

    def test_expand_path(self):
        '''Test path expansion'''
        test_path_user = "~/some/path/in/my/home/"
        user_pattern = re.compile('^/(home|Users)/.+/some/path/in/my/home')
        test_path_var = "$HOME/some/$HOME/path/in/my/home"
        var_pattern = re.compile('^/(home|Users)/.+/some/(home|Users)/.+/path/in/my/home')
        test_path_abby_normal = "/here/is/../was/a/./path//that//needs" + \
                                "/../needed/normalizing"
        abby_str = "/here/was/a/path/that/needed/normalizing"

        path = self.log_parser.expand_path(test_path_user)
        self.assertRegexpMatches(path, user_pattern)

        path = self.log_parser.expand_path(test_path_var)
        self.assertRegexpMatches(path, var_pattern)
 
        path = self.log_parser.expand_path(test_path_abby_normal)
        self.assertEqual(path, abby_str)

    def test_find_logs(self):
        '''Test for finding files matching a specified regular expression'''
        bad_dir = 'noexistant'
        all_pattern = re.compile('.*')

        self.assertRaises(Exception, self.log_parser.find_logs, \
                          [bad_dir, all_pattern])

        # Search for this script and the compiled .pyc in this directory so
        # we can be sure there are files that exist to find without needing
        # dummy files.
        good_dir = os.path.dirname(os.path.abspath(__file__))
        my_name = os.path.splitext(os.path.basename(__file__))[0]
        known_pattern = re.compile('^' + my_name + '.py[c]?$')
        gold_files = [good_dir + '/' + my_name + '.py', \
                      good_dir + '/' + my_name + '.pyc']
        
        my_files = self.log_parser.find_logs(good_dir, known_pattern)
        self.assertEqual(sorted(my_files), sorted(gold_files))

    def test_capture_failure(self):
        '''Test grabbing failure statements and returning a proper list. '''
        fail_file_object = StringIO.StringIO(
"""Failure 1
Oh, noes!
ENDFAILED
good result""")
        gold_fail = ['FAILED', 'Failure 1', 'Oh, noes!']

        test_fail = self.log_parser.capture_failure(fail_file_object)
        self.assertEqual(test_fail, gold_fail)

    def test_verify_result(self):
        '''Test result verification.'''
        required_cols = ['one', 'two', 'three']
        test_dict_bad = {'one' : 1, 'three' : 3}
        test_dict_good = {'one' : 1, 'two' : 2, 'three' : 3}

        self.assertFalse(self.log_parser.verify_result(test_dict_bad, \
                                                       required_cols))
        self.assertTrue(self.log_parser.verify_result(test_dict_good, \
                                                      required_cols))

    def test_ignorable_line(self):
        '''Test that defined lines are ignored'''
        valid_line = '[3305997.437999763] ID 33-1 sent'
        invalid_line = '[3305997.437999763] Nothing happened but should have'
        ignored_line = '[3305997.437999763] NOTE: Anything'
        self.assertFalse(self.log_parser.ignorable_line(valid_line))
        self.assertFalse(self.log_parser.ignorable_line(invalid_line))
        self.assertTrue(self.log_parser.ignorable_line(ignored_line))

    def test_process_events(self):
        """Test conversion of events hash to two lists.  One of timestamps, 
           one of ids sorted by timestamp"""
        unordered_events = {3306667.545209896 : ['5', '55'],
                            3305997.438667347 : ['1', ''],
                            3305997.448667347 : ['2', '22']}
        gold_ts = [3305997.438667347, 3305997.448667347, 3306667.545209896]
        gold_ids = ['1', '2', '5']
        gold_vals = ['', '22', '55']

        (test_ts, test_ids, test_vals) = \
            self.log_parser.process_events(unordered_events)
        self.assertEqual(test_ts, gold_ts)
        self.assertEqual(test_ids, gold_ids)
        self.assertEqual(test_vals, gold_vals)
    
