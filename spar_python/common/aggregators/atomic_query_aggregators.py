# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Classes to aggregate the 'equality' queries
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  7 May 2013    jch            Original file
# *****************************************************************





import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.common.aggregators.base_aggregator \
    as base_aggregator
import abc
import spar_python.data_generation.spar_variables as sv
import collections
import spar_python.common.spar_stemming as spar_stemming






class BaseCounter(base_aggregator.BaseAggregator):
    """
    Base-class for all *counter* aggregators: aggregators that count the number
    of times values appear in the rows. These aggregators return a dict mapping
    values to the number of times that value was seen.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _extract_value(self, row):
        '''
        The method that extracts (from rows) the value to count. Sub-classes 
        must override this method.
        '''        
        pass


    def map(self, row_dict):
        '''
        Returns a new equality-counter containing only the row passed in.
        '''
        value = self._extract_value(row_dict)
        new_counter = collections.Counter()
        new_counter[value] = 1
        return new_counter

    @staticmethod
    def reduce(larger_counter, smaller_counter):
        '''
        Merge two equality-counts by summing their component-counts
        '''
        larger_counter.update(smaller_counter)
        return larger_counter


    def done(self):
        '''
        Do nothing.
        '''
        pass







class BaseCollector(base_aggregator.BaseAggregator):
    """
    A small helper class for finding rows that match a query. That is, instances
    of this class will be possess some predicate (`match_row`) and some function
    (`extract_value`) on rows. When it sees a row which satisfies the predicate,
    it will apply the function and store the result. The intended usage is that
    function simply extract the row-ID of the field, and this is, in fact, the
    default behavior. Thus, this class would be used to collect the IDs of rows
    which will match the query represented by the predicate-- a common need.
    (Sub- classes are welcome to override this behavior, though.) Note: no
    matter what, though, function- results will be collected in a *set*, not a
    list, and so duplicates will be dropped.
    """



    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def match_row(self, row):
        '''
        The method that determines whether the row matches the predicate. 
        Sub-classes must override this method.
        '''        
        pass
    
    @staticmethod
    def extract_value(row):
        '''
        Extract value from row to store in set. Sub-classes are welcom
        to override this method. Default behavior is to store the row-ID
        of the row.
        '''        
        return row[sv.VARS.ID]
    
    
    def map(self, row_dict):
        '''
        Return either a set containing the extracted value (if the row
        satisfies match_row) or an empty set.
        '''
        if self.match_row(row_dict):
            val = self.extract_value(row_dict)
            return set([val])
        else:
            return set()

    @staticmethod
    def reduce(larger_set, smaller_set):
        '''
        Merge two sets of extracted values.
        '''
        larger_set.update(smaller_set)
        return larger_set

    def done(self):
        '''
        Do nothing.
        '''
        pass





##################################################

class LambdaCollector(BaseCollector):
    '''
    A simple, general purpose extension of BaseCollector that allows the user to
    provide any function they want for row-matching. Note: becuase of this
    generality, the user must also specify the list of all field which might be
    needed, and it is up to the user to ensure that this list is correct and
    comprehensive.
    '''

    def __init__(self, matching_function, fields_needed):
        '''
        matching_function must be a callable which takes in a row_dict
        and returns a boolean. fields_needed must be an iteratable (list, set,
        etc.) which lists all fields which might be needed by 
        matching_function in all possible cases. Preferably, fields_needed
        would be duplicate-free.
        '''
        self.matching_function = matching_function
        self.fields_iterator = fields_needed
        
    def fields_needed(self):
        return self.fields_iterator
    
    def match_row(self, row):
        return self.matching_function(row)
        


##############################################




class EqualityCounter(BaseCounter):
    """
    A small helper class for producing equality-counts on a user-
    specified field. By equality-counts on that field, we mean a dict
    mapping values to the number of times that value was seen. So, if
    the field were first names, for example, the equality counts might
    look like:
    
    { 'Amy' : 20, 
      'Bob' : 22, ...}
    
    where 20 rows had 'Amy' in the first-name field, 22 had 'Bob', etc.
    """


    def __init__(self, field):
        '''
        `field` should be the name/ID of the field to be counted (i.e., the
        key to access in the row-dict generated by DataGeneratorEngine).
        '''
        self.field = field


    def fields_needed(self):
        '''
        Return the single field needed by this aggregator-- the one
        provided at initialization.
        '''
        return set([self.field])


    def _extract_value(self, row):
        '''
        The method that extracts (from rows) the value to count. Sub-classes 
        must override this method.
        '''        
        return row[self.field]




class EqualityCollector(BaseCollector):
    """
    A small helper class for finding rows that match an equality-query. That is,
    instances of this class will be initialized with a field and a value.
    When it sees the value present in the given field, it will collect the 
    row-ID of the row.
    """


    def __init__(self, field, value):
        '''
        `field` should be the field to inspect for `value`. 
        '''
        self.field = field
        self.goal_value = value

    def fields_needed(self):
        '''
        Return the single field needed by this aggregator-- the one
        provided at initialization.
        '''
        return set([self.field])

    def match_row(self, row):
        '''
        A row matches if it has `value` in the field `field`, where
        both `value` and `field` are given in the initializer.
        '''        
        return (row[self.field] == self.goal_value)
    







class RangeCounter(EqualityCounter):
    """
    A small helper class for producing range-queries. Given a
    field (through the constructor), will return a dictionary of
    every value seen in that field, mapped to the number of times 
    that value was seen. External post-processing can be used to find
    ranges that capture the right number of values.
    
    (Note: This is exactly the same functionality as EqualityCounter, and
    is actually the exact same code with a different name. Exists mostly
    for completeness.)
    """
    pass




class RangeCollector(BaseCollector):
    """
    A small helper class for finding rows that match a range-query. That is,
    instances of this class will be initialized with a field and two values--
    either (or both) of which can be None. One of these values represents a
    lower bound and the other represents the upper bound. A value of None
    indicates the absence of a bound in that relevant direction. When it sees
    the value present in the given field that lies on the 'right' side the
    bounds (those that are present, anyway) it collects the row-ID of the row.
    Note: both bounds are *inclusive*, so values that equal a bound will be
    collected as well. Also, if both bounds are None, this class will collect
    every row-ID it sees.
    
    Only use this class on data-types where the less-than or greater-then
    operations (`__le__()` and `__ge__()` methods) are defined.
    """


    def __init__(self, field, lower_bound, upper_bound):
        '''
        `field` should be the field to insepct. Both `upper_bound` and
        `lower_bound` can be None, but if neither are None then `upper_bound`
        must be greater than `lower_bound`. Note that the bounds are inclusive,
        so values equal to the bounds will be collected.
        '''
        # sanity-check values
        if (lower_bound is not None) and (upper_bound is not None):
            assert lower_bound <= upper_bound

        self.field = field
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        
    def fields_needed(self):
        '''
        Return the single field needed by this aggregator-- the one
        provided at initialization.
        '''
        return set([self.field])


    def match_row(self, row):
        '''
        A row matches if the `value` in field `field` is less than or equal to
        `upper_bound` (if `upper_bound` is not None) and greater then or 
        equal to `lower_bound` (if `lower_bound` is not None).
        '''        
        value = row[self.field]
        upper_match =  (self.upper_bound is None) or (value <= self.upper_bound) 
        lower_match =  (self.lower_bound is None) or (self.lower_bound <= value)
        return upper_match and lower_match
    
            




class WordCounter(base_aggregator.BaseAggregator):
    """
    A small abstract class for  producing keyword-queries or stem-
    queries. Given a field (through the constructor), will return a dictionary
    of every keyword  or stem (depending) seen in that field, mapped to the
    number of rows in value was seen. (Duplicates in a given row will not be
    double-counted.)
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, field, match_case = False):
        '''
        `field` should be the name/ID of the field to be counted (i.e., the
        key to access in the row-dict generated by DataGeneratorEngine).
        
        If match_case is False, case is ignored
        '''
        self.field = field
        self.match_case = match_case


    def fields_needed(self):
        '''
        Returns a set containing only the field provided to __init__.
        '''
        return set([self.field])

    @abc.abstractmethod    
    def _extract_tokens(self, generated_text):
        '''
        Choooses word or stem from (word,stem) pairs. Subclasses must provide 
        this.
        '''
        pass

    def map(self, row_dict):
        '''
        Returns dictionary mapping every relevant value from the 
        generated text (ie., every word or every stem, depending on
        the provided implementation of _extract_tokens) to 1.
        '''
        new_counter = collections.Counter()
        generated_text = row_dict[self.field]
        tokens = self._extract_tokens(generated_text)
        for token in tokens:
            new_counter[token] = 1
        return new_counter

    @staticmethod
    def reduce(larger_counter, smaller_counter):
        '''
        Merge two equality-counts by summing their component-counts
        '''
        larger_counter.update(smaller_counter)
        return larger_counter


    def done(self):
        '''
        Do nothing.
        '''
        pass


class KeywordCounter(WordCounter):
    """
    A small abstract class for producing keyword-queries. Given a
    field (through the constructor), will return a dictionary of every keyword
    seen in that field, mapped to the number of rows in value was seen.
    (Duplicates in a given row will not be double-counted.)
    """
    
    def _extract_tokens(self, generated_text):
        if self.match_case:
            return generated_text.word_set
        else:
            return generated_text.upper_set


class StemCounter(WordCounter):
    """
    A small abstract class for producing stem-queries. Given a field
    (through the constructor), will return a dictionary of word-stems for words
    seen in that field, mapped to the number of rows in value was seen.
    (Duplicates in a given row will not be double-counted.) 
    Case is always ignored.
    """
    
    def __init__(self, field):
        super(StemCounter, self).__init__(field, match_case=False)
    
    def _extract_tokens(self, generated_text):
        return generated_text.stem_set







class WordCollector(BaseCollector):
    """
    A small abstract class for finding rows that match a keyword-query or stem-
    query. That is, instances of this class will be initialized with a field and
    a value. When it sees the value present in the given field as either a word
    or a stem, it will collect the row-ID of the row.
    """


    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _extract_word(self, word_stem_pair):
        '''
        Not used in this class.
        '''
        pass



    def __init__(self, field, word, match_case=False):
        '''
        `field` should be the field to insepct, and `word` the word
        to search for. If `match_case` is False, case is ignored. 
        '''

        self.field = field
        self.match_case = match_case 
        if not self.match_case:
            word = word.lower()
        self.word = word
    
    def fields_needed(self):
        '''
        Return the single field needed by this aggregator-- the one
        provided at initialization.
        '''
        return set([self.field])


    
    def match_row(self, row):
        '''
        A row matches if self.word is present in the field, as a keyword or a
        stem depending on the way _extract_word is defined.
    
        '''        
        word_stem_pair_list = row[self.field]
        for word_stem_pair in word_stem_pair_list:
            new_word = self._extract_word(word_stem_pair)
            # new_word might be None if we're extracting stems
            if new_word is not None:
                if not self.match_case:
                    new_word = new_word.lower()
                if self.word == new_word:
                    return True
        return False


class KeywordCollector(WordCollector):
    """
    A small abstract class for finding rows that match a keyword-query. That is,
    instances of this class will be initialized with a field and a value. When
    it sees the value present in the given field as a word, it will collect the
    row-ID of the row.
    """
    
    
    def _extract_word(self, word_stem_pair):
        return word_stem_pair[0]


class StemCollector(WordCollector):
    """
    A small abstract class for finding rows that have a word which stems to the
    same stem as a given word. That is, instances of this class will be
    initialized with a field and a value. It stems the value to find a search-
    term. When it sees the search-term present in the given field as a stem, it
    will collect the row-ID of the row. Case is always ignored.
    """
    
    def __init__(self, field, antistem):
        stem = spar_stemming.stem_word(antistem.lower())
        super(StemCollector, self).__init__(field, stem, match_case = False)
        
    
    def _extract_word(self, word_stem_pair):
        return word_stem_pair[1]

    
    
     
