#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module performs utility functions
#                      regarding files that can be used by the
#                      various performance monitoring tools
# *****************************************************************

    
class CollectlFileIterator():
    '''Class to handle collectl outputs, which are similar to a
    commented file, except that the last comment line 
    
    # a lot of comment lines
    # more comment lines
    # ...
    #Date,Time,other,column,names,
    date1,time1,other1,...
    date2,time2,other2...
    '''
    def __init__(self, handle, commentstring="#"):
        '''Initializer.
        
        Inputs:
        handle: handle to a file (open("foo.csv"))
        commentstring (optional, default="#"): the comment marker
        
        Returns: nothing'''
        # Ensure not a filename
        if isinstance(handle, str):
            raise TypeError("Handle must be a handle, not a filename")
        self._handle = handle
        self.commentstring = commentstring

    def next(self):
        '''Returns the next non-comment line, non-header'''
        line = self._handle.next()
        while line.startswith(self.commentstring):
            if line.startswith(self.commentstring + "Date,"):
                line = line.lstrip(self.commentstring)
                break
            line = self._handle.next()
        return line

    def __iter__(self):
        ''' Iterator '''
        return self