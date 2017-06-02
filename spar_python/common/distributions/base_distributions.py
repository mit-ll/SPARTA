# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Classes for holding probability distributions
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  20 Sept       JCH            Original file, but derived from Oliver's
#                               DiscreteDistributionGenerator.py
#  29 July 2013  ATLH         Added query generation support
# *****************************************************************

"""
This module holds various classes intended to hold probability
distributions.  Some of these classes model independent distributions,
where the probabilities do not depend on any other values. Some are
conditional, meaning that the probabilites do depend on other values
(independent variables). Names of these independent variables are
provided at initialization.

All the classes will provide a common set of methods, including:

* add(item, weight=1, *args): this method updates the distribution,
  telling it to add the item, with relative weight, to the
  distribution. Independent distributions ignore the
  *args. Conditional probabilties will accept *args as the values of
  the independent variables.

* generate(ind_vars): this method returns a random item provided by a
  previous call to add(). The relative probabilities of these items
  are governed by the weights provided to add (where weights 'stack'
  when the same item is added twice). Independent distributions will
  ignore ind_vars. Conditional distributions will look in ind_vars (as
  if it were a list) for the values of the independent variables.

* generate_pdf(ind_vars, min, max): this method returns a random item
  provided by a previos call to add() that falls between the min and 
  max (values between 0 and 1) in the pdf. For example adding 'hello'
  with a weight of 3 and 'there' with a weight of 1. A call to generate
  pdf with a min of 0 and max of 0.25 would generate 'there' 100% of the
  time, min of 0 max of 0.5 'hello' and 'there' would have an even chance 
  of being generated, and min of 0.5, max of 0.75 would have a 100% of 
  generating 'hello'
  
At the time of this writing, this module provides two implementations
of indepenent distributions. One independent distribution, called the
'simple' implementation, keeps an explicit list add() calls. It uses
more memory, but is faster. The other, 'compact' representation,
aggregates add() calls. This implementation is smaller, but marginally
slower.

Also at the time of this writing, this module provides one conditional
probability class. This is basically a dictionary of independent
distributions, keyed by the values of the independent variables.
"""


import os
import sys
import math
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import bisect
import spar_python.common.spar_random as spar_random
import operator
from spar_python.common.enum import Enum



class CompactIndependentDistribution(object):
    """
    This class is used to calculate the distribution of items and then
    be able to generate items from the observed distribution. It will
    work with any type of item that is hashable.

    Basic usage:
      td = CompactIndependentDistribution()
      td.add('hello')
      td.add('hello')
      td.add('world')

      td.generate()
      # Has a 2/3 chance of generating 'hello' and a 1/3 chance of generating
      # 'world'

    """
    def __init__(self, comp_enum = None):
        # A dictionary mapping items to the number of times that item was
        # observed. When the generate() function is called for the first time
        # this will be set to None and a CDF will be generated instead.
        
        # comp_enum is the enum object, if any, that the distribution holds
        # values for. 
        self.__counts = {}
        self._comp_enum = comp_enum
        
    def add(self, item, weight=1, *args):
        """
        Updates the __counts dictionary with an observation of
        item. This can not be called after generate() has been called
        the first time.
        """
        assert self.__counts is not None
        try:
            self.__counts[item] += weight
        except KeyError:
            self.__counts[item] = weight

    def __counts_to_cdf(self):
        """
        Converts __counts to data structures that we can efficiently
        use to generate data with the correct distribution. See the
        generate method for details on how this works.
        """
        assert(self.__counts is not None)
        self.__total = 0
        self.__values = []
        self.__cum_counts = []
        self.__pdf_counts = []
        for item, count in sorted(self.__counts.iteritems(),key=lambda x: x[1]):
            self.__total += count
            self.__values.append(item)
            self.__cum_counts.append(self.__total)
            self.__pdf_counts.append(count)
        
        self.__sorted_counts = []
        self.__sorted_values = []
        total = 0
        if self._comp_enum:
            def format (x):
                enum = self._comp_enum.to_string(x)
                return enum.upper()
            sorted_counts = sorted(self.__counts.iteritems(), 
                                    key = lambda x: format(x[0]))
        else:
            key_op = str.upper
            try:
                sorted_counts = sorted(self.__counts.iteritems(), 
                                    key = lambda x: key_op(x[0]))
            except TypeError:
                sorted_counts = sorted(self.__counts.iteritems(), 
                                    key = lambda x: x[0])
        for (item, count) in sorted_counts:
            total +=count
            self.__sorted_values.append(item)
            self.__sorted_counts.append(total)
                   
        self.__counts = None
        
    def generate(self, ind_vars={}):
        """
        Returns a random item that relects the distribution of add calls.

        The first time this is called it calls __counts_to_cdf to
        convert __counts to data structures that are more efficient
        for random number generation. The data structures are as
        follows: __total is the total number of times add() was
        called. __values[] is an array of the *distinct* values that
        were passed to add(). __cum_counts is a running sum of the
        number of observations that correspond to __values. So
        __cum_counts[0] is the number of times __values[0] was passed
        to add(). __cum_counts[1] is the number of times either
        __values[0] or __values[1] was passed to add() and so on.

        To quickly generate values with the right distribution we
        generate a random number in [min*__total, max*__total]. Where
        min and max are the cdf values we wish to generate between 
        (normalized to be between 0 and 1). We then do a binary
        search to find the first index in __cum_counts that is >= the
        generated value. If we then return the corresponding value
        from __values we will generate from the right distribution.
        """
       
        
        if self.__counts is not None:
            self.__counts_to_cdf()
            assert(self.__counts is None)
            
        assert self.__total > 0 
        x = spar_random.randint(1, self.__total)
        idx = bisect.bisect_left(self.__cum_counts, x)
        return self.__values[idx]
    
    def generate_conditional_pdf(self, min, max, ind_vars):
        """
        Returns a random item according to pdf values of min and max
        Functionality is to present an unified face for query 
        generation in conditional distributions
        """ 
        return self.generate_pdf(min,max,ind_vars)
    
    def generate_less_than(self, minim, maxim, **kwargs):
        '''
        Functionality to generate single sided ranges. Searches
        through a sorted list of keys until to the cumulative weight
        of the objects before/after it is within the desired minim/maxim
        Then returns that value.
        '''
        
        assert maxim >= minim and maxim <= 1 and minim >=0
        if self.__counts is not None:
            self.__counts_to_cdf()
            assert(self.__counts is None)
        
        assert self.__total > 0 
        
        max_limit = math.ceil(maxim * self.__total)
        min_limit = math.floor(max(1, self.__total * minim))
        x = spar_random.randint(min_limit, max_limit)
        idx = bisect.bisect_left(self.__sorted_counts, x)
        if idx == len(self.__sorted_counts):
            idx -= 1
        return self.__sorted_values[idx]
    
    def generate_greater_than(self, minim, maxim, **kwargs):
        '''
        Functionality to generate single sided ranges. Searches
        through a sorted list of keys until to the cumulative weight
        of the objects before/after it is within the desired minim/maxim
        Then returns that value.
        '''
        
        assert maxim >= minim and maxim <= 1 and minim >=0
        if self.__counts is not None:
            self.__counts_to_cdf()
            assert(self.__counts is None)
        
        assert self.__total > 0 
        
        max_limit = math.ceil((1-minim) * self.__total)
        min_limit = math.floor(max(1, self.__total * (1-maxim)))
        x = spar_random.randint(min_limit, max_limit)
        idx = bisect.bisect_right(self.__sorted_counts, x)
        if idx == len(self.__sorted_counts):
            idx -= 1
        return self.__sorted_values[idx]
    
    def generate_double_range(self, minim, maxim, **kwargs):
        '''
        '''
        assert maxim >= minim and maxim <= 1 and minim >=0
        if self.__counts is not None:
            self.__counts_to_cdf()
            assert(self.__counts is None)
        
        assert self.__total > 0 
        max_limit = math.ceil(maxim * self.__total)
        min_limit = math.floor(max(1, self.__total * minim))
        range = spar_random.randint(min_limit, max_limit)
        weight_lower = spar_random.randint(1, max(1,self.__total-range))
        weight_upper = weight_lower + range
        id_lower = bisect.bisect_left(self.__sorted_counts, weight_lower)
        id_upper = bisect.bisect_left(self.__sorted_counts, weight_upper)
        if id_upper == len(self.__sorted_counts):
            id_upper -= 1
        return (self.__sorted_values[id_lower], self.__sorted_values[id_upper])
        
    def generate_pdf(self, minim, maxim, ind_vars={}):
        """
        Returns a random item that relects the distribution of add calls.

        The first time this is called it calls __counts_to_cdf to
        convert __counts to data structures that are more efficient
        for random number generation. The data structures are as
        follows: __total is the total number of times add() was
        called. __values[] is an array of the *distinct* values that
        were passed to add(). __cum_counts is a running sum of the
        number of observations that correspond to __values. So
        __cum_counts[0] is the number of times __values[0] was passed
        to add(). __cum_counts[1] is the number of times either
        __values[0] or __values[1] was passed to add() and so on.

        To quickly generate values with the right distribution we
        generate a random number in [min*__total, max*__total]. Where
        min and max are the cdf values we wish to generate between 
        (normalized to be between 0 and 1). We then do a binary
        search to find the first index in __cum_counts that is >= the
        generated value. If we then return the corresponding value
        from __values we will generate from the right distribution.
        """
        assert maxim >= minim and maxim <= 1 and minim >=0
       
        
        if self.__counts is not None:
            self.__counts_to_cdf()
            assert(self.__counts is None)
        
            
        assert self.__total > 0 
        max_limit = math.ceil(maxim * self.__total)
        min_limit = math.floor(max(1, self.__total * minim))
        idmin = bisect.bisect_left(self.__pdf_counts, min_limit)
        if idmin == len(self.__pdf_counts):
            idmin -= 1
        idmax = bisect.bisect(self.__pdf_counts, max_limit)
        if idmax != idmin:
            idmax -= 1
    
        idx = spar_random.randint(idmin, idmax)
        return self.__values[idx]

    def size_pdf(self):
        """
        Returns the number of distinct items that could be generated
        by a call to generate_pdf().
        """
        return self.size()
         
    def size(self, *args):
        """
        Returns the number of distinct items that could be generated
        by a call to generate(*args). *args are ignored.
        """
        if self.__counts is not None:
            return len(self.__counts.viewkeys())
        else:
            return self.__total
        
    def support(self, *args):
        """
        Returns the set of values which might be produced by generate(*args).
        *args are ignored.
        """
        if self.__counts is not None:
            return set(self.__counts.keys())
        else:
            return self.__values
        

    def remap(self, orig, replacement):
        '''Make it so that the distribution generates replacement instead 
        of orig.
        '''
        if self.__counts is not None:
            
            # First, check that orig is actually in the distribution
            if orig not in self.__counts:
                pass
            else:
                # Okay, we know orig is in the distribution. If replacement
                # is already in the distribution, then we need to combine
                # the entries. Otherwise, just switch one for the other.
                if replacement in self.__counts:
                    self.__counts[replacement] += self.__counts[orig]
                else:
                    self.__counts[replacement] = self.__counts[orig]
                del self.__counts[orig]

        else:
            # Replace orig with replacement in self.__values
            def replace_if_orig(x):
                if x == orig:
                    return replacement
                else:
                    return x
            self.__values = map(replace_if_orig, self.__values)
        


class SimpleIndependentDistribution(CompactIndependentDistribution):
    """
    This class is used to calculate the distribution of items and then
    be able to generate items from the observed distribution. It will
    work with any type of item that is hashable.

    Basic usage:
      td = SimpleIndependentDistribution()
      td.add('hello')
      td.add('hello')
      td.add('world')

      # Has a 2/3 chance of generating 'hello' and a 1/3 chance of generating
      # 'world'
      td.generate()      
    """
    
    def __init__(self, comp_enum = None):
        super(SimpleIndependentDistribution, self).__init__(comp_enum)
        self._added_items = []
        self._seen = set()
        
        # Note: self._size will always be equal to len(self._seen), but
        # it becomes a bottleneck to re-compute it each time. So we maintain
        # it as a separate counter, and keep it in sync with self._seen
        self._size = 0
        
        # Note: rather than re-computing the length of __added_items each
        # time we call generate(), we will keep track of it explicitly--
        # not not directly. Since spar_random.randint will actually want
        # (length-1) we will track that in the following attribute:
        self.__randint_bound = -1
        
    def add(self, item, weight=1, *args):
        """
        Updates the __counts dictionary with an observation of
        item. Note: weight must be a non-negative integer.
        """
        super(SimpleIndependentDistribution, self).add(item,weight,*args)
        assert weight >= 0
        new_items = [item] * weight
        self._added_items.extend(new_items)
        self._seen.add(item)
        self._size = len(self._seen)
        self.__randint_bound += weight
        

    def generate(self, ind_vars = None):
        """
        Returns a random item that relects the distribution of add
        calls.
        """
        x = spar_random.randint(0, self.__randint_bound)
        return self._added_items[x]

    def size(self, *args):
        """
        Returns the number of distinct items that could be generated
        by a call to generate(*args). *args are ignored.
        """
        return self._size

    def support(self, *args):
        """
        Returns the set of values which might be produced by generate(*args).
        *args are ignored.
        """
        return self._seen


    def remap(self, orig, replacement):
        '''Make it so that the distribution generates replacement instead 
        of orig.
        '''
        super(SimpleIndependentDistribution, self).remap(orig, replacement)
        def replace_if_orig(x):
           if x == orig:
               return replacement
           else:
               return x
        self._added_items = map(replace_if_orig, self._added_items)

        self._seen = (self._seen - set([orig])) | set([replacement])
        self._size = len(self._seen)

class SimpleConditionalDistribution(object):
    """
    This class models conditional distributions. It can be initialized
    by:

    cd = ConditionalDistribution(FOO, BAR)

    where FOO and BAR are strings, integers, tuples, or any hashable
    item. (In normal use, they would be something like VARS.ENUM and
    VARS.BAR, where VARS is an Enum.)
    
    At this point, cd understands that the probaiblity it represents
    is conditioned on the values of independent variables named by FOO
    and BAR.

    The distribution is defined through repeated calls to add():

    cd.add('a', weight=1, True, False)
    cd.add('2', weight=2, True, False)

    At this point, the probability of cd, conditioned on FOO = True and
    BAR = False is 1/3 'a', 2/3 'b'. (Note: the weight keyword arguement
    is not optional when independent variables are used, but the keyword
    itself can be omitted. That is, the calls above are equivelent to:

    cd.add('a', 1, True, False)
    cd.add('2', 2, True, False)

    In either case, one can then sample from the conditional
    distribution by calling generate(d) where d is a dict containing
    values for FOO and BAR. That is, if

    some_list[FOO] == True
    some_list[BAR] == False 

    then:
    
    cd.generate( l )

    should return 'a' with probability 1/3, 'b' with probability 2/3.
    (The purpose of all this rigamarole with the list and the indicies
    is to allow a very tight loop in the row-generator code.)

    If generate() is called on a list which does not contain
    values for FOO and BAR, or hold values for FOO and BAR which
    were not previously seen in a call to add(), and exception is
    thrown.

    As opposed to CompactConditionalDistribution, this uses
    SimpleIndependentDistribution objects under the hood.
    """
    def __init__(self, *args, **kwargs):
        self._ind_vars = args
        self._underlying_dists = {}
        try:
            comp_enum = kwargs['comp_enum']
            self._top_level_dist = CompactIndependentDistribution(comp_enum)
        except KeyError:
            self._top_level_dist = CompactIndependentDistribution()


    def _make_new_dist(self):
        """
        Makes new underlying independent distributions
        """
        return SimpleIndependentDistribution()
    
    def add(self, item, weight=1, *args):
        """
        Updates the conditional distribution, adding item (with
        weight) conditioned on the independent variables being *args.
        """
        #Updates the __counts dictionary with an observation of item.
        # First, check that we have enough args:
        if not len(args) == len(self._ind_vars):
            raise KeyError("Not enough independent variables")
        else:
            # Now, use that tuple to find the right underlying distribution.
            # If none found, create one
            try:
                dist = self._underlying_dists[args]
            except KeyError:
                dist = self._make_new_dist()
                self._underlying_dists[args] = dist

            # add the item
            dist.add(item, weight)
            self._top_level_dist.add(item, weight)
            
    def _get_underlying_dist(self, ind_vars):
        """
        Helper function to find the right underlying independent
        distribution given the values of the independent
        variables. Note that ind_vars must be a dict, holding the
        values of the ind_vars as values keyed on the names of the
        ind_vars provided at initilization. Note: will throw KeyError
        if these ind_vars were not previously seen in prior call to add().
        """
        ind_var_values = [ind_vars[v] for v in self._ind_vars]
        ind_var_tuple = tuple(ind_var_values)
        underlying_dist = self._underlying_dists[ind_var_tuple]
        return underlying_dist

    def generate_pdf(self, min, max, ind_vars):
        """
        Wrapper function for pdf generation of the total values 
        stored in the various conditional distributions
        """
        return self._top_level_dist.generate_pdf(min, max)
    
    def generate_less_than(self, minim, maxim, **kwargs):
        """
        Wrapper function for range generation of the total values
        stored in the various contitional distributions
        """
        return self._top_level_dist.generate_less_than(minim, maxim)
    
    def generate_greater_than(self, minim, maxim, **kwargs):
        """
        Wrapper function for range generation of the total values
        stored in the various contitional distributions
        """
        return self._top_level_dist.generate_greater_than(minim, maxim)
    
    def generate_double_range(self, minim, maxim, **kwargs):
        """
        Wrapper function for range generation of the total values
        stored in the various contitional distributions
        """
        return self._top_level_dist.generate_double_range(minim, maxim) 
    
    def generate_conditional_pdf(self, min, max, ind_vars):
        """
        Returns a random item according to pdf values of min and max
        conditioned on the values for the independent vars in ind_var
        """
        try:
            underlying_dist = self._get_underlying_dist(ind_vars)        
        except KeyError:
            # Oops. We have not seen these ind_vars before.
            # Get a random underlying_dict.
            ind_var_tuples = self._underlying_dists.keys()
            random_tuple = spar_random.choice(ind_var_tuples)
            underlying_dist = self._underlying_dists[random_tuple]
            
        return underlying_dist.generate_pdf(min, max)
    
    def generate(self, ind_vars):
        """
        Returns a random item that relects the distribution of add
        calls, conditioned on the values for the independent vars in
        ind_vars.
        """
        try:
            underlying_dist = self._get_underlying_dist(ind_vars)        
        except KeyError:
            # Oops. We have not seen these ind_vars before.
            # Get a random underlying_dict.
            ind_var_tuples = self._underlying_dists.keys()
            random_tuple = spar_random.choice(ind_var_tuples)
            underlying_dist = self._underlying_dists[random_tuple]
            
        return underlying_dist.generate()
    def size_pdf(self):
        """
        Returns the number of distinct items that could be generated
        by a call to generate_pdf().
        """
        return self._top_level_dist.size()
        
    def size(self, ind_vars):
        """
        Returns the number of distinct items that could be generated
        by a call to generate(ind_vars).
        """
        underlying_dist = self._get_underlying_dist(ind_vars)        
        return underlying_dist.size()

    def remap(self, orig, replacement):
        '''Make it so that the distribution generates replacement instead 
        of orig.
        '''
        self._top_level_dist.remap(orig, replacement)
        for (_, dist) in self._underlying_dists.items():
            dist.remap(orig, replacement)

    def support(self):
        return_me = set()
        for (_, dist) in self._underlying_dists.items():
            return_me.update(dist.support())
        return return_me

class CompactConditionalDistribution(SimpleConditionalDistribution):
    """
    See the documentation for SimpleConditionalDistribution.

    As opposed to SimpleConditionalDistribution, this uses
    CompactIndependentDistribution objects under the hood.
    """

    def _make_new_dist(self):
        """
        Makes new underlying independent distributions.
        """
        return CompactIndependentDistribution()
