# *****************************************************************
#  Copyright 2014 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Unit test for remote_runner
# *****************************************************************

import os
import sys
import argparse
import unittest
import logging
import glob
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.remote_runner.remote_runner as rr
import spar_python.remote_runner.config_classes as config_classes


class RemoteRunnerTest(unittest.TestCase):
    
    def test_assert_names_unique(self):
        '''Tests assert_names_unique'''
        config = config_classes.Config()
        alice_client = config_classes.Component()
        alice_client.name = "Alice"
        alice_client.host = "client"
        bob_client = config_classes.Component()
        bob_client.name = "Bob"
        bob_client.host = "client"
        charlie_client = config_classes.Component()
        charlie_client.name = "Charlie"
        charlie_client.host = "client"
        charlie_client2 = config_classes.Component()
        charlie_client2.name = "Charlie"
        charlie_client2.host = "client"
        alice_server = config_classes.Component()
        alice_server.name = "Alice"
        alice_server.host = "server"
        bob_server = config_classes.Component()
        bob_server.name = "Bob"
        bob_server.host = "server"
        bob_server2 = config_classes.Component()
        bob_server2.name = "Bob"
        bob_server2.host = "server"
        charlie_server = config_classes.Component()
        charlie_server.name = "Charlie"
        charlie_server.host = "server"
        
        # should succeed 
        self.assertTrue(rr.assert_names_unique([alice_client, bob_client, 
                                                charlie_client]), 
                        "assert_names_unique failed to return True")
        self.assertTrue(rr.assert_names_unique([alice_client, alice_server,
                        bob_client, bob_server, charlie_client, 
                        charlie_server]), 
                        "assert_names_equal failed to return True")
        try:
            rr.assert_names_unique([alice_client, charlie_client, bob_client, 
                                    charlie_client2])
            # executing the next line means the function failed to fail
            self.fail("assert_names_unique failed to raise an exception")
        except AssertionError:
            pass # success
        try:
            rr.assert_names_unique([alice_server, charlie_server, bob_server, 
                                    bob_server2])
            # executing the next line means the function failed to fail
            self.fail("assert_names_unique failed to raise an exception")
        except AssertionError:
            pass # success
        try:
            rr.assert_names_unique([alice_client, charlie_client, bob_client, 
                                    charlie_client2, alice_server, 
                                    charlie_server, bob_server, bob_server2])
            # executing the next line means the function failed to fail
            self.fail("assert_names_unique failed to raise an exception")
        except AssertionError:
            pass # success
    
    @unittest.skip("Generates local files and does not delete them; also "
                   "complains about bad key to 'localhost'")
    def test_local(self):
        ''' Tests running remote_runner on localhost.
        This test tells remote_runner to touch a file and
        then verifies that the file exists
        '''
        TEST_RESULT_FILE = 'unit_test_result.log'
        TEST_RESULT_FILE_PATH = os.path.join(this_dir, TEST_RESULT_FILE)

        config = config_classes.Config()
        comp = config_classes.Component()
        comp.name = 'unit_test'
        comp.start_index = 1
        comp.base_dir = this_dir
        comp.args = []
        comp.files = {}
        comp.wait = False
        comp.host = 'localhost'
        comp.executable = '/usr/bin/touch'
        comp.args.extend([TEST_RESULT_FILE])
        config.add_component(comp)
        
        comp2 = config_classes.Component()
        comp2.name = 'output_unit_test'
        comp2.start_index = 2
        comp2.base_dir = this_dir
        comp2.args = []
        comp2.files = {}
        comp2.wait = False
        comp2.host = 'localhost'
        comp2.executable = '/bin/echo'
        comp2.args.extend(["output test"])
        config.add_component(comp2)

        # Get default options 
        # remote_runner requires a -c file which will be unused
        parser = rr.get_parser()
        options = parser.parse_args(["-c", "nothing",'-l','DEBUG'])

        # Set logging based on log_level option
        # NOTE with nosetests the output from the logger only appears
        # when there is an error but I am putting this code here as an
        # example. It will be useful for python code that calls
        # remote_runner methods.
        log_level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR}
        logging.basicConfig(
            level = log_level_mapping[options.log_level],
            format = '%(levelname)s: %(message)s')

        # config_dir is the directory where the configuration files live
        # and is used by run() when it calls canonicalize_paths() on the
        # component's executable. For local components, if the path is
        # relative on the local machine then it will make them relative to
        # config_dir.  If all the local component's executable paths are
        # absolute paths then config_dir is unused. If here are no local
        # components then config_dir is unused.
        config_dir = 'unused'
        
        filename_pattern_1 = "rr_output_%s*.txt" % comp.name
        filename_pattern_2 = "rr_output_%s*.txt" % comp2.name

        # remove any existing test files
        if os.path.exists(TEST_RESULT_FILE_PATH):
            os.remove(TEST_RESULT_FILE_PATH)
        for f in glob.glob(filename_pattern_1):
            os.remove(f)
        for f in glob.glob(filename_pattern_2):
            os.remove(f)

        # run the test
        rr.run(config, options, config_dir)

        # check that the file exists
        self.assertEqual(os.path.isfile(TEST_RESULT_FILE_PATH), True)
        
        # check that the output files exist
        self.assertEqual(len(glob.glob(filename_pattern_1)), 1, 
                           "can't find output file for first component")
        self.assertEqual(len(glob.glob(filename_pattern_2)), 1, 
                           "can't find output file for second component")

        # remove the test files
        if os.path.exists(TEST_RESULT_FILE_PATH):
            os.remove(TEST_RESULT_FILE_PATH)
        for f in glob.glob(filename_pattern_1):
            os.remove(f)
        for f in glob.glob(filename_pattern_2):
            os.remove(f)


        

if __name__ == '__main__':
    unittest.main()
