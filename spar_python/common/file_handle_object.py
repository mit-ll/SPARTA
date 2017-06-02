
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA2 file handle object class
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  28 Nov 2012   SY             Original Version
# *****************************************************************

import os

class FileHandleObject(object):
    """A class that handles writing to the file system. We want to separate
    all file system modification mothods out into a separate class so that we
    can overwrite them for unit testing.
    """
    def __init__(self):
        """no initialization necessary."""
        pass
    
    def create_dir(self, dir_name):
        """creates a directory corresponding to dir_name"""
        # this method exists to aid in unit testing. we do not want to actually
        # be creating directories during unit tests, so we will use a subclass
        # of this class wherein this method is overwritten.
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    def get_file_object(self, file_name, command):
        """returns a file object. command shoule be either 'r' or 'w'."""
        # this method exists to aid in unit testing. we do not want to actually
        # be accessing files during unit tests, so we will use a subclass
        # of this class wherein this method is overwritten.
        return open(file_name, command)

    def close_file_object(self, file_object):
        """closes the file object."""
        # this method exists to aid in unit testing. we do not want to
        # be closing files during unit tests, so we will use a subclass
        # of this class wherein this method is overwritten.
        return file_object.close()
