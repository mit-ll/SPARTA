# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jill
#  Description:        Aggregators for query generation
# *****************************************************************
from __future__ import division 
import os
import sys
import collections
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)
import copy
import operator
import itertools

import spar_python.common.aggregators.base_aggregator as base_aggregator

import spar_python.data_generation.spar_variables as sv
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.query_generation.query_schema as qs
import abc
import spar_python.query_generation.query_bounds as qbs

class GenChooseAggregator(base_aggregator.BaseAggregator):
    """
    Aggregator for batches of queries where x are generated and y are
    chosen from the set
    """
    def __init__(self, aggregators):
        ''' Initialize needs a list of aggregators '''
        self.aggs = aggregators
        self.active = len(self.aggs) > 0
        
    def fields_needed(self):
        ''' returns a set of all fields needed for all aggregators'''
        if self.active:
            fields_needed_sets = [a.fields_needed() for a in self.aggs]
            s = reduce(set.union, fields_needed_sets, set())
        else: 
            s = set()
        return s

    def map(self, row):
        '''Maps across all contained aggregators and applies their map
        function to the row'''
        return { qs.QRY_SUBRESULTS : [agg.map(row) for agg in self.aggs] }
          
    
    def map_reduce_row_list(self, row_list):
        return {qs.QRY_SUBRESULTS : 
                [agg.map_reduce_row_list(row_list) for agg in self.aggs]}
        
    
    def reduce(self, larger, smaller):
        '''Maps across all aggregators and applies their reduce functions to
        the results associated with that aggregator'''

        assert len(self.aggs) == len(larger[qs.QRY_SUBRESULTS]) 
        assert len(self.aggs) == len(smaller[qs.QRY_SUBRESULTS])
        return { qs.QRY_SUBRESULTS : 
                 [ agg.reduce(lg,sm) 
                   for agg,lg,sm in zip(self.aggs,larger[qs.QRY_SUBRESULTS],
                                        smaller[qs.QRY_SUBRESULTS]) ] }
        
    def set_process_limit(self, num_processes):
        '''
        Caps the number of results the contained aggregators can 
        collect per process for that run
        '''
        for a in self.aggs:
            a.set_process_limit(num_processes)
        
    def done(self):
        '''Does nothing'''
        pass


class AndQueryAggregator(GenChooseAggregator):
    """
    Aggregator that collects results for and queries
    """
    pass

class OrQueryAggregator(GenChooseAggregator):
    """
    Aggregator that collects results for or queries
    """
    pass

class ThresholdQueryAggregator(GenChooseAggregator):
    """
    Aggregator that collects results for threshold queries
    """
    pass

class AtomicQueryAggregatorBase(base_aggregator.BaseAggregator):
    ''' 
    Base aggregators for non-compound queries and clauses of compound queries
    
    NOTE THAT THESE AGGREGATORS BREAK THE 'STATELESS' DESIGN REQUIREMENT.
    To kill a memory bottleneck, these aggregators keep track of how many 
    matching rows they have seen and, once that limit has been exceeded,
    start outputting a constant, empty 'invalid' result. This works, but only
    because the rest of the data-generator engine happens to be written just
    right. It will almost certainly break (silently!) if the data-generator 
    engine is re-factored or aggregators are created/destroyed more frequently
    than once per worker.
    
    We *strongly* suggest that you do not use statefulness of this kind
    (or any kind) unless performance bottlenecks make it absolutely
    necessary.
    
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, query):        
        ''' Initialize the needed class variables from the query '''
        self._qid = query[qs.QRY_QID]
        self._field = sv.sql_name_to_enum(query[qs.QRY_FIELD])
        # try/except block is mostly for backwards compatability
        # with unit tests
        try:
            self._process_cutoff = qbs.get_rss_upper(query[qs.QRY_ENUM])
        except KeyError:
            self._process_cutoff = 100000
        self._count = 0
        #If the query is atomic (i.e. top level), we want to apply a limit
        #on what it can collect, otherwise we want no process limit in
        #effect
        try:
            self._top_level = query['top_level']
        except KeyError:
            self._top_level = True
            
    def fields_needed(self):
        '''
        Return a set() containing the fields which will actually
        be written to file.
        '''
        return set([self._field])
        
    @abc.abstractmethod
    def match_row(self, row):
        '''
        The method that determines whether the row matches the predicate. 
        Returns True if it matches; False otherwise
        Sub-classes must override this method.
        '''    
        pass
    
    def extract_value(self, row):
        '''
        Extract the value of field from row in the format needed for
        the specific aggregator.

        Returns the value for the requested field from the row
        '''    
        try:
            return row.in_query_aggregator_format[self._field]
        except AttributeError:                 
            # We were given an old-style dictionary (probably in a unit test).
            # For backwards compatibility, re-compute the needed value.
            field_id = self._field       
            reformat = sv.VAR_CONVERTERS[field_id].to_agg_fmt
            reformatted_val = reformat(row[field_id])
            return reformatted_val
    
    def set_process_limit(self, num_processes):
        '''
        This is the number of results an aggregator can collect
        for this query on a per process basis, if it collects
        more than that value, aggregation is stopped and the 
        query is marked as not 'valid'
        '''
        self._process_cutoff =  self._process_cutoff / num_processes
          
    def map(self, row):
        '''
        Return a dictionary where DBF_MATCHINGRECORDIDS either
        contains a set of the matching row number or an empty set if
        there is no match
        '''
        #The use of lists instead of sets is a huge memory 
        #optimization, at the cost of some functionality 
        if self.match_row(row):
            self._count += 1
            if self._top_level == True and self._count > self._process_cutoff:
                return { qs.QRY_QID     : self._qid, 
                         qs.QRY_VALID : False,
                         rdb.DBF_MATCHINGRECORDIDS : [] }
            else:
                return { qs.QRY_QID     : self._qid, 
                         qs.QRY_VALID : True,
                         rdb.DBF_MATCHINGRECORDIDS : [row[sv.VARS.ID]] }
        else:
            return { qs.QRY_QID : self._qid,
                     qs.QRY_VALID : True,
                     rdb.DBF_MATCHINGRECORDIDS : \
                         [] }


    def reduce(self, larger, smaller):
        larger[qs.QRY_VALID] = larger[qs.QRY_VALID] and \
                                     smaller[qs.QRY_VALID]
        if not larger[qs.QRY_VALID]:
            larger[rdb.DBF_MATCHINGRECORDIDS] = []
        else:
            larger[rdb.DBF_MATCHINGRECORDIDS].extend(smaller[rdb.DBF_MATCHINGRECORDIDS])
        return larger
            
    

    def map_reduce_row_list(self, row_list):
        """
        Take a list of rows and return the single final result for the 
        whole list. Overriding default implementation from BaseAggregator 
        for efficiency. Note: this function is the bottleneck, and so has
        been extensively optimized.
        """
        match_row = self.match_row
        matching_rows = filter(match_row, row_list)
        num_matching_rows = len(matching_rows)
        self._count += num_matching_rows
        getitem = operator.getitem
        sv_VARS_ID = sv.VARS.ID
        sv_VARS_ID_repeater = itertools.repeat(sv_VARS_ID, num_matching_rows)
        matching_row_ids = map(getitem, matching_rows, sv_VARS_ID_repeater)
        matching_row_id_list = matching_row_ids
        valid = True
        if self._top_level==True and self._count > self._process_cutoff:
            valid = False
            matching_row_id_list = []
        return { qs.QRY_QID : self._qid, qs.QRY_VALID : valid, 
                rdb.DBF_MATCHINGRECORDIDS : matching_row_id_list }


    def done(self):
        '''
        Do nothing.
        '''
        return None


class EqualityQueryAggregator(AtomicQueryAggregatorBase):
    """An aggregator for equality"""
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(EqualityQueryAggregator, self).__init__(query)
        self._value = query[qs.QRY_VALUE]
        if type(self._value) is str:
            self._value = self._value.upper()

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.extract_value(row) == self._value

class NotEqualQA(EqualityQueryAggregator):
    """An aggregator for equality"""
    
    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.extract_value(row) != self._value

class RangeQueryAggregator(AtomicQueryAggregatorBase):
    """An aggregator for double sided inequality"""
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(RangeQueryAggregator, self).__init__(query)
        self._lbound = query[qs.QRY_LBOUND]
        self._ubound = query[qs.QRY_UBOUND]
        if type(self._lbound) is str:
            self._lbound = self._lbound.upper()
            self._ubound = self._ubound.upper()

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self._lbound <= self.extract_value(row) <= self._ubound

       
class LessThanQueryAggregator(AtomicQueryAggregatorBase):
    """An aggregator for equality"""
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(LessThanQueryAggregator, self).__init__(query)
        self._value = query[qs.QRY_VALUE]
        if type(self._value) is str:
            self._value = self._value.upper()

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.extract_value(row) <= self._value


class GreaterThanQueryAggregator(AtomicQueryAggregatorBase):
    """An aggregator for equality"""
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(GreaterThanQueryAggregator, self).__init__(query)
        self._value = query[qs.QRY_VALUE]
        if type(self._value) is str:
            self._value = self._value.upper()

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.extract_value(row) >= self._value



class P3P4QueryAggregator(AtomicQueryAggregatorBase):
    """An aggregator for P3 and P4-stemming """
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(P3P4QueryAggregator, self).__init__(query)
        # searches are case-insensitive
        self._search_for = query[qs.QRY_SEARCHFOR].upper()
        # index into the word_stem_pair of the notes fields
        if query[qs.QRY_CAT] == 'P4':
            self.search_against = 'stems'
        else:
            self.search_against = 'lowers'

    def extract_value(self, row):
        '''
        Extract the value of field from row in the format needed for
        the specific aggregator.

        Overrides the baseclass method.

        Returns the value for the requested field from the row
        '''    
        return row[self._field]

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        gened_text = self.extract_value(row)
        if self.search_against == 'stems':
            return gened_text.contains_stem(self._search_for)
        elif self.search_against == 'lowers':
            return gened_text.contains_upper(self._search_for)
        else:
            raise RuntimeError("Invalid list: %s" % self.search_against)


###########################################################################
# Implement a specific class for each type of search for performance 
# reasons
#
# There are 3 base classes for searches:
#
# 1) class SearchQABase 
# Used for one value
# Implements:
# __initial
# match_row
#
# Derived classes implement is_match(value, data)
# P7InitialQA
#  for: P7_initial
# P7BothQA
#  for: P7_both
# P7FinalQA
#  for: P7_final
#
#
# 2) class SearchNumQABase
# Used for one value and a num
# where num is the number of characters that should be untouched at the 
#  beginning or end of the data string
# Implements:
# __initial
# match_row
#
# Derived classes implement is_match(value, num, data)
# SearchInitialNumQA
#   for: P6_initial_one, P7_other_5, P7_other_6
# SearchFinalNumQA
#   for: P6_final_one, P7_other_1, P7_other_2
# 
#
# 3) class SearchMultipleNumQABase
# Used for mutiple values and num (value_list, num, data)
# where num is the number of characters in between each value
# Implements:
# __initial
# match_row
#
# Derived classes implement is_match(value_list, num, data)
# SearchMultipleNumQA
#   for: P6_middle_one, P7_other_3, P7_other_4
# SearchFinalMultipleNumQA
#   for: P7_other_[12,13,14]
# SearchBothMultipleNumQA
#   for: P7_other_[15,16,17]
# SearchInitialMultipleNumQA
#   for: P7_other_[9,10,11]
#
#############################################################################

class SearchQABase(AtomicQueryAggregatorBase):
    ''' 
    Base aggregator for search queries that take one value to match 
    '''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(SearchQABase, self).__init__(query)
        # searches are case-insensitive
        self._value = query[qs.QRY_SEARCHFOR].upper()

    @staticmethod
    @abc.abstractmethod
    # static to make it easer to unit test
    def is_match(value, data):
        ''' check for value in data must be implemented by derived class'''
        pass

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.is_match(self._value, self.extract_value(row))

class P7InitialQA(SearchQABase):
    ''' 
    Aggregator for P7_inital search queries
    Search for: <zero-or-more-chars> value
    '''
    @staticmethod
    def is_match(value, data):
        return data.endswith(value)

class P7BothQA(SearchQABase):
    ''' 
    Aggregator for P7_both search queries
    Search for: <zero-or-more-chars> value <zero-or-more-chars>
    '''
    @staticmethod
    def is_match(value, data):
        return data.find(value) != -1

class P7FinalQA(SearchQABase):
    ''' 
    Aggregator for P7_final search queries
    Search for: value <zero-or-more-chars>
    '''
    @staticmethod
    def is_match(value, data):
        return data.startswith(value)







class SearchNumQABase(AtomicQueryAggregatorBase):
    ''' 
    Base aggregator for search queries that take one value and a num

    value is the string to search for 
    num is the number of characters that should be untouched at the 
      beginning or end of the data string
    '''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(SearchNumQABase, self).__init__(query)
        # searches are case-insensitive
        self._value = query[qs.QRY_SEARCHFOR].upper()
        self._num = query[qs.QRY_SEARCHDELIMNUM] 

    @staticmethod
    @abc.abstractmethod
    # static to make it easer to unit test
    def is_match(value, num, data):
        ''' check for value in data must be implemented by derived class'''
        pass

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.is_match(self._value, self._num, self.extract_value(row))

class SearchInitialNumQA(SearchNumQABase):
    ''' 
    Aggregator for: P6_initial_one, P7_other_5, P7_other_6
    '''
    @staticmethod
    def is_match(value, num, data):
        '''
        Search for: _stuff, __stuff, etc
        
        value is the string to search for 
        num is the number of characters that should be untouched at the 
          beginning of the data string
        data is the string to search in

        For example: for "__stuff", value is "stuff" and num is 2

        Returns True if it found a match; False otherwise
         '''
        return data[num:] == value


class SearchFinalNumQA(SearchNumQABase):
    ''' 
    Aggregator for: P6_final_one, P7_other_1, P7_other_2
    '''
    @staticmethod
    def is_match(value, num, data):
        '''
        Search for stuff_, stuff__, etc

        value is the string to search for
        num is the number of characters that should be untouched at the
          end of the data string
        data is the string to search in

        For example: for "stuff_", value is "stuff" and num is 1
        
        Returns True if it found a match; False otherwise
        '''
        idx = num * (-1)
        return data[0:idx] == value


class SearchMultipleNumQABase(AtomicQueryAggregatorBase):
    ''' 
    Base aggregator for search queries that take a list of values and a num

    value_list contains the list of values to search for in left to right order
    num is the number of characters in between each value
    '''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(SearchMultipleNumQABase, self).__init__(query)
        # searches are case-insensitive
        self._value_list = \
            [ value.upper() for value in query[qs.QRY_SEARCHFORLIST] ]
        self._num = query[qs.QRY_SEARCHDELIMNUM] 

    @staticmethod
    @abc.abstractmethod
    # static to make it easer to unit test
    def is_match(value_list, num, data):
        ''' check for values in data must be implemented by derived class'''
        pass

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.is_match(self._value_list, self._num, 
                             self.extract_value(row))


    @staticmethod
    def multiple_num_helper(value_list, num, data):
        '''
        Search for a list of strings starting at the beginning of
        the data string and separated by a specific number of characters
        
        value_list is the list of strings to search for
        num is the number of characters to expect in between the values
        data is the string to search in

        For example: search for "stuff__stuff2"
          value_list is ['stuff','stuff2']
          num is 2

        Returns a tuple of bools (matched, left_over_data) 
        Where "matched" is True if it found what it expected; False otherwise.  
        Where "left_over_data" is always False if matched is False, 
        and True when there are remaining characters at the end of the data
        string that were not matched by the values.
        '''
        assert(len(value_list) >= 1)
    
        data_sz = len(data)
        data_idx = 0
        for value in value_list:
            if data_idx > data_sz:
                # ran out of data
                return (False, False)
            value_sz = len(value)
            data_idx_end = data_idx + value_sz
            if data_idx_end > data_sz:
                # value too long
                return (False, False)
            if data[data_idx:data_idx_end] != value:
                # not match value
                return (False, False)
            data_idx = data_idx_end + num

        # check for left over characters in data
        left_over_data =  data_idx - num < data_sz

        return (True, left_over_data)
    

    @staticmethod
    def reverse_multiple_num_helper(value_list, num, data):
        '''
        Search for a list of strings starting at the end of
        the data string and separated by a specific number of characters.

        value_list is the list of strings to search for (in Left to right
          order even though this is a reverse method)
        num is the number of characters to expect in between the values
        data is the string to search in

        For example: search for "stuff__stuff2"
          value_list is ['stuff','stuff2']
          num is 2

        Returns a tuple of bools (matched, left_over_data) 
        Where "matched" is True if it found what it expected; False otherwise.
        Where "left_over_data" is always False if matched is False, 
        and True when there are remaining characters at the start of the data
        string that were not matched by the values.
        '''
        assert(len(value_list) >= 1)
    
        data_sz = len(data)
        data_idx = data_sz
        for value in reversed(value_list):
            if data_idx < 0:
                # ran out of data
                return (False, False)
            value_sz = len(value)
            data_idx_start = data_idx - value_sz
            if data_idx_start < 0:
                # value too long
                return (False, False)
            if data[data_idx_start:data_idx] != value:
                # not match value
                return (False, False)
            data_idx = data_idx_start - num

        # check for left over characters in data
        left_over_data =  data_idx + num > 0

        return (True, left_over_data)
    

class SearchMultipleNumQA(SearchMultipleNumQABase):
    ''' 
    Aggregator for: P6_middle_one, P7_other_3, P7_other_4
    '''
    @staticmethod
    def is_match(value_list, num, data):
        '''
        Search for "stuff__stuff2__stuff3", etc

        value_list contains the list of values to search for in 
          left to right order
        num is the number of characters in between each value
        data is the string to search in

        For example: for "stuff__stuff2__stuff3", num is 2 and 
        value_list = ['stuff', 'stuff2', stuff3']

        Returns True if it found a match; False otherwise
        '''
        (matched, left_over_data) = \
            SearchMultipleNumQABase.multiple_num_helper(value_list, num, 
                                                        data)
        # must be an exact match (no initial or final characters left over)
        return matched and not left_over_data


class SearchFinalMultipleNumQA(SearchMultipleNumQABase):
    ''' 
    Aggregator for: P7_other_[12,13,14]
    '''
    @staticmethod
    def is_match(value_list, num, data):
        '''
        Search for "stuff__stuff2_stuff3%", etc
        
        value_list contains the list of values to search for in 
          left to right order
        num is the number of characters in between each value
        data is the string to search in
        
        For example: for "stuff__stuff2__stuff3%", num is 2 and 
        value_list = ['stuff', 'stuff2', stuff3']
        
        Returns True if it found a match; False otherwise
        '''
        (matched, left_over_final_data) = \
            SearchMultipleNumQABase.multiple_num_helper(value_list, 
                                                        num, data)
        return matched


class SearchBothMultipleNumQA(SearchMultipleNumQABase):
    ''' 
    Aggregator for: P7_other_[15,16,17]
    '''
    @staticmethod
    def is_match(value_list, num, data):
        '''
        Search for "%stuff__stuff2_stuff3%", etc

        value_list contains the list of values to search for in 
          left to right order
        num is the number of characters in between each value
        data is the string to search in
        
        For example: for "%stuff__stuff2__stuff3%", num is 2 and 
          value_list = ['stuff', 'stuff2', stuff3']
        
        Returns True if it found a match; False otherwise
        '''
        assert(len(value_list) >= 1)

        # Find first value, start looking at the beginning of data
        idx = data.find(value_list[0])
        if (idx == -1):
            # first value not found
            return False

        if len(value_list) == 1:
            # matched the only value
            return True

        # Pass remainder of data and the remaining values to FinalMultipleNum
        idx = idx + len(value_list[0]) + num
        return SearchFinalMultipleNumQA.is_match(value_list[1:], num, 
                                                 data[idx:])


class SearchInitialMultipleNumQA(SearchMultipleNumQABase):
    ''' 
    Aggregator for: P7_other_[9,10,11]
    '''
    @staticmethod
    def is_match(value_list, num, data):
        '''
        Search for "%stuff__stuff2_stuff3", etc

        value_list contains the list of values to search for in 
          left to right order
        num is the number of characters in between each value
        data is the string to search in

        For example: for "%stuff__stuff2__stuff3", num is 2 and 
        value_list = ['stuff', 'stuff2', stuff3']

        Returns True if it found a match; False otherwise
        '''
        (matched, left_over_initial_data) = \
            SearchMultipleNumQABase.reverse_multiple_num_helper(value_list, 
                                                                num, data)
        return matched



#
# Fishing Aggregators
#

class FishingMixin(object):
    ''' 
    Base class for the map/reduce used by the fishing aggregators. Requires
    
    * match_row()
    * extract_value()
    * _qid
    '''
    def map(self, row):
        '''
        Return a dictionary where DBF_MATCHINGRECORDIDS either
        contains a set of the matching row number or an empty set if
        there is no match
        and QRY_FISHING_MATCHES_FOUND is a dictionary indexed by the
        matching field value containing a set of matching row ids or an empty
        dictionary if there is no match.
        '''
        return_dict = collections.defaultdict(list)
        if self.match_row(row):
            record_id = row[sv.VARS.ID]
            field_value = self.extract_value(row)
            return_dict[field_value] = [record_id]
            
        return {qs.QRY_QID : self._qid, qs.QRY_VALID : True,
                qs.QRY_FISHING_MATCHES_FOUND : return_dict}


    @staticmethod
    def reduce(larger, smaller):
        '''
        Merge two dictionaries for elements MATCHINGRECORDSIDS and
        QRY_FISHING_MATCHES_FOUND.  All other values will be identical
        between the 2 dictionaries and do not need to be merged
        e.g. qid. As a memory optimization, only the smallest 
        value is kept from the chosen value. 
        '''
        def update_fun(matches_found, kv_pair):
            (key, value) = kv_pair
            l = matches_found[key]
            l.extend(value)
            return matches_found
        #merging the two results to get any overlapping values
        #this is unlikely but could happen
        kv_pairs = smaller[qs.QRY_FISHING_MATCHES_FOUND].iteritems()
        fishing_matches = reduce(update_fun, 
                                     kv_pairs, 
                                     larger[qs.QRY_FISHING_MATCHES_FOUND])
        #find the smallest value of the two batches
        new_fishing_matches = collections.defaultdict(list)
        keys = fishing_matches.keys()
        if keys:
            min_key = min(keys)
            new_fishing_matches[min_key] = fishing_matches[min_key] 
            
        larger[qs.QRY_FISHING_MATCHES_FOUND] = new_fishing_matches
        return larger



    def map_reduce_row_list(self, row_list):
        """
        Take a list of rows and produce the final map/reduce value for
        the list. Overrides default implementation in BaseAggregator for speed.
        Note: this method is a bottleneck, so the imeplementation is heavily
        optimized.
        """
        #mapping 
        match_row = self.match_row
        matching_rows = filter(match_row, row_list)
        num_matching_rows = len(matching_rows)
            
        extract_value = self.extract_value
        field_values = map(extract_value, matching_rows)
        
        sv_VARS_ID = sv.VARS.ID
        sv_VARS_ID_repeater = itertools.repeat(sv_VARS_ID, num_matching_rows)
        getitem = operator.getitem
        row_ids = map(getitem, matching_rows, sv_VARS_ID_repeater)
        
        return_me = collections.defaultdict(list)
        if field_values:
            min_field_val = min(field_values)
            min_field_val_id_list = [row_id for (field_val, row_id) in zip(field_values, row_ids) 
                                  if field_val == min_field_val]
            return_me[min_field_val] = min_field_val_id_list
       
        return {qs.QRY_QID : self._qid, qs.QRY_VALID: True,
                qs.QRY_FISHING_MATCHES_FOUND : return_me}



class SearchFishingQA(FishingMixin, P7BothQA):
    ''' 
    Aggregator for P7_both fishing search queries on string fields.
    Used to find a query for things like ssn, and address where
    it is difficult to quess a value to use in an equality query.

    This aggregator will take in a search string and save the actual
    field value that matched the search string. This will allow the
    BOQ to choose and fill in one of the actual values when it
    processes the results of the aggregator.

    Returns inside the aggregator results dictionary, a dictionary called
    QRY_FISHING_MATCHES_FOUND which is indexed by the value of the
    matching field with a set of which row ids matched that exact
    specific field value.
    For example, with the seach string: "%Peach%"
    It might return a Counter:
    { '1 Peach Tree Ln' : set([1]),   # meaning row 1 had this value
      '42 Peach Circle' : set([5,6]), # meaning row 5 & 6 had this value
      ...
    }
    '''
    pass

class RangeFishingQA(FishingMixin, RangeQueryAggregator):
    ''' 
    Aggregator for double sided inequality fishing search queries on 
    numeric and date fields.
    Used to find a query for things like dob and foo where
    it is difficult to quess a value to use in an equality query.

    This aggregator will take in the lbound and ubound and save the actual
    field value that matched the range. This will allow the
    BOQ to choose and fill in one of the actual values when it
    processes the results of the aggregator.

    Returns inside the aggregator results dictionary, a dictionary called
    QRY_FISHING_MATCHES_FOUND which is indexed by the value of the
    matching field with a set of row ids that matched that exact
    specific field value.
    For example, with the range search lbound=100 ubound=500
    It might return a Counter:
    { 102 : set([1]),   # meaning row 1 had this value
      500 : set([5,6]), # meaning row 5 & 6 had this value
      ...
    }
    '''
    pass
        

class XMLLeafQueryAggregator(AtomicQueryAggregatorBase):
    """An aggregator for XML 'leaf' queries"""
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(XMLLeafQueryAggregator, self).__init__(query)
        self._leaf_tag = query[qs.QRY_XPATH]
        self._leaf_value = query[qs.QRY_VALUE].upper()

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.extract_value(row).has_leaf(self._leaf_tag, 
                                                self._leaf_value)


class XMLPathQueryAggregator(AtomicQueryAggregatorBase):
    """An aggregator for XML 'full path' queries"""
    
    def __init__(self, query):
        ''' Initialize base class variables and specific variables  '''
        super(XMLPathQueryAggregator, self).__init__(query)
        self._leaf_tag = query[qs.QRY_XPATH]
        self._leaf_value = query[qs.QRY_VALUE].upper()

    def match_row(self, row):
        '''
        called to determine if this row matches.
        Returns True if it matches; False otherwise
        Overrides baseclass method.
        '''
        return self.extract_value(row).has_path(self._leaf_tag, 
                                                self._leaf_value)






class AlarmwordAggregator(base_aggregator.BaseAggregator):
    """
    Aggregator for the 'alarmword' queries: the presence of two alarmwords
    within a fixed distance of each other. Will return the same dictionary
    as an AtomicQueryAggregatorBase, but with an additional entry for 
    rdb.DBF_MATCHINGRECORDIDDISTANCEPAIRS: an unsorted list of 
    matching-row (row-id, distance) pairs. (Developer's note: this changes
    the implementation enough that it doesn't really make sense for this to 
    be a sub-class of AtomicQueryAggregatorBase.)
    """
    
    def __init__(self, query):
        self._qid = query[qs.QRY_QID]
        self._field = sv.sql_name_to_enum(query[qs.QRY_FIELD])
        self._alarmwords = set([query[qs.QRY_ALARMWORDONE], query[qs.QRY_ALARMWORDTWO]])
        self._alarmword_distance = query[qs.QRY_ALARMWORDDISTANCE]
        self._process_cutoff = qbs.get_rss_upper(query[qs.QRY_ENUM])
        self._count = 0

    def fields_needed(self):
        '''
        Return a set() containing the fields which will actually
        be written to file.
        '''
        return set([self._field])

    def extract_value(self, row):
        '''
        Extract the relevant notes field from the row. Overrides the base-class
        method so as to return the GeneratedText object itself rather than
        its string format. Included in this class for the benefit of the 
        FishingMixin
        '''    
        return row[self._field]

    def set_process_limit(self, num_processes):
        '''
        This is the number of results an aggregator can collect
        for this query on a per process basis, if it collects
        more than that value, aggregation is stopped and the 
        query is marked as 'VALID'
        '''
        self._process_cutoff = self._process_cutoff / num_processes

    def _get_distance(self, row):
        '''
        Returns either:
        
        * The distance between self._alarmword1 and self._alarmword2, if
        the relevant notes field contains both alarmwords, in the correct order,
        and within the distance-limit of each other; or
        
        * None. Note that this is returned in all other cases, so it cannot be
        used to distinguish between 'alarmwords missing', 'alarmwords in 
        wrong order' and 'alarmwords too far apart.'
        
        '''
        
        generated_text = self.extract_value(row)
        alarmwords = set(generated_text.alarmwords)
        try:
            actual_distance = generated_text.alarmword_distances[0]
        except TypeError:
            return None
        else:
            try:        
                if actual_distance <= self._alarmword_distance and\
                   self._alarmwords == alarmwords:
                    return actual_distance
                else:
                    return None
            except IndexError:
                return None
                
                
    def match_row(self, row):
        """
        Returns True if the relevant notes field contains both alarmwords, in
        the correct order, and within the distance-limit of each other. Returns
        False otherwise. Included in this class for the benefit of the
        FishingMixin.
        """
        distance = self._get_distance(row)
        return distance is not None
        
    def map(self, row):
  
        distance = self._get_distance(row)
                
                
        if distance is not None:
            record_id = row[sv.VARS.ID]
            tup = (record_id, distance)
            return {qs.QRY_QID : self._qid,
                    rdb.DBF_MATCHINGRECORDIDS : [record_id],
                    qs.QRY_MATCHINGROWIDANDDISTANCES : [tup]}
        else:
            return {qs.QRY_QID : self._qid,
                    rdb.DBF_MATCHINGRECORDIDS : [],
                    qs.QRY_MATCHINGROWIDANDDISTANCES : []}


    def reduce(self, larger, smaller):
        larger[rdb.DBF_MATCHINGRECORDIDS].extend(smaller[rdb.DBF_MATCHINGRECORDIDS])
        smaller_row_id_dists = smaller[qs.QRY_MATCHINGROWIDANDDISTANCES]
        larger_row_id_dists = larger[qs.QRY_MATCHINGROWIDANDDISTANCES]
        larger_row_id_dists.extend(smaller_row_id_dists)
        larger[qs.QRY_MATCHINGROWIDANDDISTANCES] = larger_row_id_dists

        larger[qs.QRY_VALID] = larger[qs.QRY_VALID] and \
                                     smaller[qs.QRY_VALID]
        if not larger[qs.QRY_VALID]:
            larger[rdb.DBF_MATCHINGRECORDIDS] = []
            larger[qs.QRY_MATCHINGROWIDANDDISTANCES] = []
        return larger
    
    
    def map_reduce_row_list(self, row_list):

        dists = [self._get_distance(row) for row in row_list]
        sv_VARS_ID = sv.VARS.ID
        ids = [row[sv_VARS_ID] for row in row_list]
        id_dist_pairs = [(row_id, dist) 
                           for (row_id, dist) in zip(ids, dists)
                           if dist is not None]
        matching_row_ids = [row_id for (row_id, _) in id_dist_pairs]
        self._count += len(matching_row_ids)
        valid = True
        if self._count > self._process_cutoff:
            valid = False
        return { qs.QRY_QID : self._qid, qs.QRY_VALID : valid,
                rdb.DBF_MATCHINGRECORDIDS : matching_row_ids ,
                qs.QRY_MATCHINGROWIDANDDISTANCES : id_dist_pairs}
        
        