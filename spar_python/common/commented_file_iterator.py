#!/usr/bin/env python
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        This module iterators through a file that 
#                      contains comments denoted by a leading comment
#                      character, such as a '#'
# *****************************************************************

class CommentedFileIterator():
    '''Class to _handle a file with comment strings, such as
    
    # comment
    interesting line
    another intesting line
    # ignore thiis comment
    ...
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
        '''Returns the next non-comment line'''
        line = self._handle.next()
        while line.startswith(self.commentstring):
            line = self._handle.next()
        return line

    def __iter__(self):
        ''' Iterator '''
        return self