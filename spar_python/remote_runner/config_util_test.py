# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for the methods in config_util 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Jan 2013   omd            Original Version
# *****************************************************************

import config_util
import os
import shutil
import tempfile
import unittest

class TestConfigUtil(unittest.TestCase):
    def test_recursive_files_dict(self):
        """Test that the recursive_add_files method of the Component class works
        as expected."""
        # To make this test robust we create the files in a temporary directory
        # instead of relying on anyting to be already existing on the file
        # system.
        tdir = tempfile.mkdtemp()
        try:
            f1 = file(os.path.join(tdir, 'file1'), 'w+')
            f2 = file(os.path.join(tdir, 'file2'), 'w+')
            sub_name = os.path.join(tdir, 'sub')
            sub = os.mkdir(sub_name)
            f3 = file(os.path.join(sub_name, 'file3'), 'w+')

            result = config_util.recursive_files_dict(tdir, '/path/on/remote')

            expected = {
                    os.path.join(tdir, 'file1'): '/path/on/remote/file1',
                    os.path.join(tdir, 'file2'): '/path/on/remote/file2',
                    os.path.join(tdir, 'sub/file3'):
                        '/path/on/remote/sub/file3'}
            self.assertEqual(result, expected)

        finally:
            shutil.rmtree(tdir)

