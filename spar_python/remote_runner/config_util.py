# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Various utility functions for writing configuration
#                      files. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Jan 2013   omd            Original Version
# *****************************************************************

import os.path

def recursive_files_dict(src_path, dest_path):
    """Returns a dict suitable for the files attribute of a Component object
    by recursively adding all the files and directories in src_path.

    For example, suppose /tmp/foo contains:

    /tmp/foo:
      - a
      - b
      - sub:
         - c

    Calling this with src_path = '/tmp/foo' and dest_path = '/home/sut/bar'
    would result in the following dict:

    {
      '/tmp/foo/a': '/home/sut/bar/a',
      '/tmp/foo/b': '/home/sut/bar/b',
      '/tmp/foo/sub/c': '/home/sut/bar/sub/c'
    }

    If the desired dest_path is base_dir, just set dest_path = '.'
    """
    res = {}
    for dirpath, dirnames, fnames in os.walk(src_path):
        for fn in fnames:
            file_path = os.path.join(dirpath, fn)
            rel_path = os.path.relpath(file_path, src_path)
            res[file_path] = os.path.join(dest_path, rel_path)

    return res

