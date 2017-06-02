# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Iterators for tokens in a text file, lines in files.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2011   omd            Original Version
#  04 Oct 2012   jch            Added FileLineIterator
# *****************************************************************

import string
import copy

class FileTokenIterator(object):
    """
    A class for iterating over the "tokens" in a file. This is used by
    TextGenerator to get the tokens so it can compute the distributions of
    tokens to generate realistic English sentences.

    A token is defined to be any sequence of ascii characters
    separated by white-space. Punctuation characters that end a
    sentence are treated specially as these terminate other tokens as
    count as tokens themselves.  For example, a line like"this is fun."
    produces 4 tokens: ['this', 'is', 'fun', '.'].

    To use this class, instantiate it with an open file-like object and
    then use it as a standard iterator. It will returns tokens one at
    time.
    """

    # These characters are treated as their own complete tokens if they
    # appear.  For example, "hello there." should have 3 tokens: ('hello',
    # 'there', '.') so we have to put '.' in this set.
    COMPLETE_TOKEN_CHARS = set(['.', '!', '?', ':'])

    # This is the set of characters that "count". All other characters,
    # including white space, are skipped.
    VALID_CHARS = set(string.ascii_letters)
    VALID_CHARS = VALID_CHARS.union(COMPLETE_TOKEN_CHARS)

    # Add ' as a valid character so conjunctions like it's are OK. Note that
    # this might get sticky with some kinds of quoting...
    VALID_CHARS = VALID_CHARS.union(("'"))

    def __init__(self, file):
        """Constructor. file should be an open, non-empty file-like object."""
        self.__file = file

        # index into the current line where we'll start searching for
        # the next token.
        self.__cur_index = 0
        self.__cur_line = file.readline()

        # readline returns the empty string ONLY when it encounters
        # EOF. Thus constructing this with an empty file is an
        # error. 
        assert(len(self.__cur_line) > 0)

    def __iter__(self):
        return self

    def next(self):
        token_start = -1

        while True:
            # Look for tokens starting from __cur_index, the place where we
            # should start looking for the next valid token.
            for i in xrange(self.__cur_index, len(self.__cur_line)):
                cur_char = self.__cur_line[i] 
                if cur_char in self.VALID_CHARS:
                    if cur_char in self.COMPLETE_TOKEN_CHARS:
                        # We found a character that is, by itself, a valid
                        # token. If it was by itself (e.g. separated by white
                        # space) we return it. Otherwise we return the
                        # current token and set __cur_index to i so we'll
                        # return the punctuation character on the next call.
                        if token_start == -1:
                            self.__cur_index = i + 1
                            return cur_char
                        else:
                            self.__cur_index = i
                            return self.__cur_line[token_start:i]
                    else:
                        if token_start == -1:
                            # This current token was in VALID_CHARS and we
                            # didn't yet have a token_start so we should
                            # start looking for a token here.
                            token_start = i
                else:
                    if token_start != -1:
                        # cur_char wasn't in VALID_CHARS and we did have a
                        # current token so return it.
                        self.__cur_index = i
                        return self.__cur_line[token_start:i]

            # We reached EOF. If we have token output it.
            if token_start != -1:
                self.__cur_index = len(self.__cur_line)
                ts_temp = token_start
                token_start = -1
                return self.__cur_line[ts_temp:]

            # We've exhausted the current line so read the next one.
            self.__cur_line = self.__file.readline()
            if len(self.__cur_line) == 0:
                # readline returns the empty string *only* on EOF so we've
                # hit the end of the file and we're done.
                raise StopIteration
            # Set __cur_index and token_start to indicate that we've got a
            # new line and we have not yet found anything on it.
            self.__cur_index = 0
            token_start = -1

