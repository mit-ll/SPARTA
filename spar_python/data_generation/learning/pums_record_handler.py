# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Parser, descriptor, and manipulator for a single
#                      record of PUMS data
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  09 Dec 2011   omd            Original Version
# *****************************************************************

import copy
from spar_python.common.enum import Enum
import spar_python.data_generation.learning.pums_variables as pums_variables

class PUMSRecordHandler(object):
    """A PUMSRecordHandler knows how to read PUMS data files and
    produce records from the files. It can also interpret the returned
    records indicating which field corresponds to which variable, what
    the string representation of those variables are, etc.

    The record handler is configured via the constructor and can thus
    be used to parse any number of fields in any order."""
    def __init__(self, vars_dict):
        """Constructor.

        The vars_dict argument specifies which variables to extract from the
        data and how to extract/parse/manipulate them. For example, 
        vars_dict might be given by:

        {AGE: (AGE_PARSER, AGE_MANIPULATOR),
         STATE: (STATE_PARSER, STATE_MANIPULATOR)}

        This implies that the record-handler will get the AGE and STATE 
        values (using the associated manipulator and parser).

        args:
            vars_dict: a dict mapping variables to a pair of (Parser,
                Mainpulator) pairse for that variable.
        """

        self.__parsers = {}
        self.__person_vars = []
        self.__household_vars = []
        self.__manipulators = {}


        for var in vars_dict:
            self.__parsers[var] = vars_dict[var][0]
            if self.__parsers[var].source() == \
                pums_variables.RECORD_SOURCE.HOUSEHOLD:
                self.__household_vars.append(var)
            else:
                assert self.__parsers[var].source() == \
                        pums_variables.RECORD_SOURCE.PERSON
                self.__person_vars.append(var)
            self.__manipulators[var] = vars_dict[var][1]



    def record_generator(self, file_obj):
        """Given an open file-like object, file_obj, iterator over that file
        returning complete person records. For each record found the tuple
        (weight, record) is returned where weight indicates the weight to give
        to this record and record is dictonary mapping the variable name 
        (given as a key to the vars_dict argument to the constructor) to values.
        """
        # Records must be stateful since the household information applies to
        # all the people in the household. However, we dont want to return a
        # reference to the object we're using to hold state so we maintain a
        # cur_record variable and copy it before returning it.
        cur_record = {}
        for line in file_obj:
            if line.startswith('H'):
                # This is a household record so parse it. These values will then
                # persist for all person records for that household.
                for var in self.__household_vars:
                    cur_record[var] = self.__parsers[var].parse(line)
            else:
                # Its a person record. Parse it and return a copy of the record.
                assert line.startswith('P')
                for var in self.__person_vars:
                    cur_record[var] = self.__parsers[var].parse(line)
                weight = int(line[12:16])
                # The are individuals in the data with 0 weight! That doesn't
                # make sense but I called the census bureau and verified that
                # this is the case.
                if weight == 0:
                    continue
                yield (weight, copy.copy(cur_record))

    def mutli_file_generator(self, files):
        """Like record_generator but with multiple files. Files must be an
        iterable of file-like objects. This generates records for each file in
        turn."""
        for f in files:
            for data in self.record_generator(f):
                yield data

    def as_string(self, record, index):
        """Return a string representation of the variable at position index in
        record."""
        return self.__manipulators[index].to_string(record[index])

    def record_to_string(self, record):
        """Given an array representing a single record return a new array
        representing the same record but with each value represented as a
        string."""
        assert \
            len(record) == len(self.__person_vars) + len(self.__household_vars)
        return [self.as_string(record, i) for i in xrange(len(record))]
