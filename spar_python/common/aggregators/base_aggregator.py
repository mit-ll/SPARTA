# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Abstract Base Class for all other aggregators
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  14 May 2013   jch            original file
# *****************************************************************


import abc

class BaseAggregator(object):
    """
    This class defines the interface for all aggregators, and should be 
    sub-classed by all aggregators. Specifically, all aggregators should
    implement a map-reduce interface:
    
    * It must provide a map() method which, when invoked on a row-dictionary
      (see data_generator_engine.py) will return a value of some 
      aggregator-specific type T.
      
    * It must also provide a reduce() method which takes two arguments of 
      type T and returns an argument of type T. Every attempt is made to enforce
      that when reduce(x,y) is called, x will be the 'larger' of the two values
      and y will be the 'smaller'. (Here, 'larger' and 'smaller' mean 'created
      by reducing more rows' and 'created by reducing fewer rows' respectively.)
      This is enforced to the extent possible, but cannot be relied upon as a
      guarantee. For all x and y, reduce(x,y) should always return the same
      value as reduce(y,x). But when choosing how to implement reduce, one may
      assume that x is 'bigger' than y for optimization reasons.

    
    In addition, this class provides an implementation of two list-based
    methods, reduce_row_list() and map_reduce_row_list(). Subclasses may wish
    to override these naive implementations with optimized ones.
    
    
    A note about state: it is strongly advised that aggregators be as 
    state-free as possible, and that map(), reduce(), reduce_row_list() and 
    map_reduce_row_list() be pure functions with no side effects. However, 
    this will not always be the case. For example, an aggregator that writes
    rows to a file or database will need to keep some state, such as the file
    handle or network connection to which rows should be written. If this is
    the case, subclasses should override the start() and done() methods with 
    initializing and clean-up code, respectively. Why should state set-up code
    be put in start() instead of __init__()? To answer that, we need to 
    explain the current life cycle of aggregators:
        
    * Be created, once, in the initial process of the data-generator ('the 
      mothership').
    * If data-generation is parallelized (i.e., in multi-process mode) then
      there will be a number of data-generator workers, all running in different
      processes. Each worker will receive a copy of the created aggregator.
    * Each worker calls start() on each aggregator before generating data.
    * Batches of rows are fed to each aggregator through the 
      map_reduce_row_list() method and the aggregate results collected.
    * When data-generation is finished, the done() method of each aggregator
      is called-- and the return value (if any) is ignored.
    
    NOTE THAT THIS WORKFLOW MAY CHANGE. Again, we strongly advise that
    aggregators be stateless, so that they won't be broken by workflow changes.
    But if you need stateful aggregators, bear in mind the following gotchas:
    
    * The constructor will only be called once. This is unsurprising in single-
      process mode, but might be an unexpected fact in multi-process mode. 
      In multi-process mode, the aggregators are created by the 'mothership'
      and copies are sent to each worker process via the usual python 
      multiprocess mechanism. This means: DO NOT HAVE THE CONSTRUCTOR DO ANY
      WORK OR SET UP ANY STATE THAT SHOULD NOT BE SHARED ACROSS MULTIPLE 
      PROCESSES. Example: if the aggregator is going to write rows to files, do 
      not open the file in the constructor. If you do that, then the various 
      workers will all be trying to write to the same file. Big mess. 
      
      Instead, do this work (that is, open these files) in start(). That method 
      will be called once by each data-generating process. Note that start()
      will need to be written in such a way that these possibly-multiple
      processes don't conflict. (For example, start() should uniquify file names
      so that these processes all open different files.) But the design of the
      system ensures that start() is called by each process indivudally, which
      may not necessarily be the case for __init__().
      
    * If at all possible, map(), reduce(), reduce_row_list() and 
      map_reduce_row_list() should be pure functions (i.e., they do not change
      the internal state of the aggregator). If you choose to violate this, 
      then please bear in mind that your aggregator will break if the workflow
      of the data-generator changes. Also please bear in mind that, in 
      multiprocess mode, there is no guarantee that any one copy of the 
      aggregator will see all of the rows. Or even any given fraction of them.
      The only guarantee that can be relied upon is that some copy of the
      aggregator will see an 'average' number of rows or higher.

    Another note: In an ideal world, the aggregators would notice when they are
    used 'out of order' (done() called before start(), start() called multiple
    times, map() called before start(), etc.) and throw an exception. However, 
    some of the aggregators are bottlenecks. For performance reasons, therefore,
    we have chosen to live dangerously and *not* perform these checks in the
    base aggregator. Subclasses are free to perform these checks if they choose.
    Otherwise, aggergator authors are encouraged to code their aggregators
    under the assumption that the above workflow is respected and to let 
    exceptions occur as a natural result of workflow violations.

    """

    __metaclass__ = abc.ABCMeta
    
    def start(self):
        """
        Perform any initial, state-setting work. Currently, this will be called
        once per data-generating process, before any data is generated. Any
        return value will be ignored. Example usage: opening files or network
        connections for data-writing aggregators. Note that the implementation
        of this method should be written in a way that respects/enforces the
        necessary process separation. If the aggreator is to open a file in this
        method, for example, care must be taken when writing this method so that
        no file is opened by more than one process at a time.
        
        """
        pass


    @abc.abstractmethod
    def fields_needed(self):
        """
        Return the fields of the row actually used/neede by this aggregator.
        For efficiency reasons, we would like DataGeneratorEngines to 
        generate the fewest fields possible, so it is essential to know
        which fields are actually needed for run in question. Hence, each
        aggregator should expose the fields it needs.
        
        The return value should be an interatable (list, set, generator, etc.).
        Ideally, this return value should not return or contain redundant
        values (e.g., a set() or a list with no duplicates) but duplicate 
        values will be handled gracefully.
        """
        pass
    
    @abc.abstractmethod
    def map(self, row_dict):
        """
        Process row-dictionary, return result of aggregator-specific 
        aggregate-value type.
        
        (Note: return values of None no longer receive special handling, and
        will now be passed to reduce()).
        """
        pass
    
    @staticmethod
    @abc.abstractmethod
    def reduce(result1, result2):
        """
        Combine two aggreate-result values into one aggregate-result value.
        
        Notes to implementors: 
        
        * This method must guarantee that reduce(x,y) == reduce(y,x).
        
        * For the purposes of optimization, however, the implementor can
        rely on the guarantee that in the call reduce(x,y), x will be 'larger'
        than y-- meaning that x was created by reducing more rows than y. 
        
        * This method *should* be static if at all possible, so as to enforce
        that reduce(x,y) depends only on x & y, and not attributes of the 
        object/class.
        
        * map-values of None no longer receive special handling. If map() 
        returns None, then reduce() should be able to handle an input of None.
        """
        pass
    
    def done(self):
        """
        
        Any clean-up code that should be run when we no longer need the
        aggregator. Close files, flush buffers, etc. Any return value is 
        ignored.
        
        """
        pass
    
    
    def reduce_list(self, map_vals):
        """
        A high-level function to take a list of map() or reduce() results 
        and to reduce them into a single result. Note that this base class 
        provides the straightforward implementation, but subclasses may wish
        to provide optimized implementations. Will raise AssertionError if 
        the list of map_vals is empty.
        """
        assert len(map_vals) >= 1
        return reduce(self.reduce, map_vals)
    
    def map_reduce_row_list(self, row_list):
        """
        A high-level function to take a list of rows, map them, and reduce the
        results. This has a straightforward default implementation, but
        exists in the Aggregator API so that sub-classes can provide 
        optimized implementations. Will raise an AssertionError if 
        row_list is empty.
        """
        assert len(row_list) >= 1
        map_vals = map(self.map, row_list)
        reduce_val = self.reduce_list(map_vals) 
        return reduce_val
