# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Generate a rows of data according to distributions
#                      from learn_distributions
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Sept 2012  jch            Original file
#  30 April 2013 jch            Factored workers & mothership out into
#                                   separate file.
# *****************************************************************

"""
This module contains the entry-point into data-generation. Defines a number
of 'options' classes which can specify the paramters of the data-generation,
and the all-important Worker class. A Worker instance will actually manage the
execution of rows by either generating the data itself (single-process mode) 
or farming them out to other Worker instances (multi-process mode). Note
that the Worker instances do not generate the rows or feed them to aggregators
themselves, but instead hold instances of DataGeneratorEngine to do that
for them. The 'top level' Worker instance will, however, be responsible
for aggregating the results of the aggregators' reduce() methods.
"""



import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import multiprocessing
import itertools
import datetime

import spar_python.data_generation.data_generator_engine\
       as data_generator_engine
import spar_python.common.spar_random as spar_random
from spar_python.common.enum import Enum
import Queue
from spar_python.data_generation.progress_reporters import \
    RowAggregatorProgressReporter
import traceback

    
    
    
def _call_reduce_list(aggregator, batch_level_results):
    """
    Returns aggregator.reduce_list(batch_level_results). Note that this function
    must be at the top level (and hence pickleable) for the parallelization of
    aggregation in Worker.reduce_batch_results().
    """
    return aggregator.reduce_list(batch_level_results)


    
    
class DataGeneratorOptions(object): #pylint: disable-msg=R0903
    '''
    A 'container' object to hold options for data-generation. The list
    of options is still in flux, so see the arguments to __init__ for the 
    current list.
    '''
    
    def __init__(self,
                 random_seed = 1,
                 num_processes = 1,
                 num_rows = 100,
                 verbose = False,
                 aggregators = None,
                 batch_size = 5):
        '''
        Constructor. Current arguments (and valid options for data-generation)
        include:
        
        * random_seed

        * num_processes

        * num_rows

        * verbose : if True, data-generation will provie more feedback on 
          terminal

        * aggregators : This should be a list of Aggregator instances.
        
        * batch_size : The number of rows sent from mothership to worker
          in a single message. The larger this number, the less inter-process
          communication ad the longer it takes to get feedback from the 
          workers. Also, if/when we implement the resumption protocol, this 
          number will govern the number of rows (per worker) that
          will be lost in a crash. The Right Value for this parameter should
          be determined through experimentation.
                
          
        '''

        # Note: the following is needed because of a quirk about
        # providing mutable objects as default values and the fact
        # that lists are mutable values. If we had put 
        #
        # aggregators = []
        #
        # in the argument-list, then changes to aggregators would be
        # seen across *all* instances of this class. Bad bad bad.
        if aggregators is None:
            self.aggregators = []
        else: 
            self.aggregators = aggregators
            
        
        self.random_seed = random_seed
        self.num_processes = num_processes
        self.num_rows = num_rows
        self.verbose = verbose
        self.batch_size = batch_size



class Worker(object):
    """
    Class of data-generator workers. If user requested single-process mode,
    then a single instance of this class generates all rows itself. If user
    requested multi-process mode, then the initial instance of this class
    switches to 'mothership' mode, spawns the requested number of other 
    workers, and manages them as they generate the rows in 'spawned' mode.
    """
    
    
    #
    # Functions used by __init__ to create the row-id/seed generator
    #


        
            
    
    # This file uses two different types of 'chunks'. The first is 
    # a virtual chunking, used only in the generation of row-IDs. The second is 
    # how we batch up rows for processing by the worker processes in 
    # multiprocessing mode. We will call the first 'striping' and the second
    # 'batching'. 
    
    STRIPE_SIZE = 1000



    def _row_id_generator(self, num_rows):
        """
        Generates row-IDs. For this release, these IDs will be 64-bit
        integers.  The first hald of the bits will a a chunk identifier,
        which will be randomly ordered but the same for all rows in a
        chunk. The second half of the bits will be unique and randomly
        ordered within a chunk. (And the order changes from chunk to
        chunk.)
        """
        num_chunks = (num_rows / self.STRIPE_SIZE) + 1
        chunk_id_ints = [x for x in xrange(num_chunks)]
        within_chunk_id_ints = [x for x in xrange(self.STRIPE_SIZE)]
        spar_random.shuffle(chunk_id_ints)
        
        # Note: this next line used to be in the for-loop immediately below
        # it. In that case, the within-chunk IDs would be shuffled for
        # each chunk individually. This tripped a bug in single-process
        # mode, however, in which the workers would overwrite the mothership's
        # RNG state, and the row-IDs in single-process mode and multi-process
        # mode would be different. By moving this line here, we eliminate
        # that conflict. We also reduce the entropy of row-IDs slightly.
        # Another option considered would be for this generator
        # to store the mothership's RNG state after each shuffle and to 
        # restore it before the next. This was rejected as being to complex
        # given the schedule at that time. It might be worth re-considering
        # in the future.
        spar_random.shuffle(within_chunk_id_ints) 
        for chunk_id_int in chunk_id_ints:
            for within_chunk_id_int in within_chunk_id_ints:
                # create rowid as a 64-bit int with the high order bits
                # comfing from chunk_id_int and the low-order bits coming
                # from within_chunk_id_int
                row_id = (chunk_id_int << 32) + within_chunk_id_int
                yield row_id

    @staticmethod
    def _seed_generator(start_seed):
        """
        Generates a sequence of RNG seeds, given a starting point.  For
        this release, the start_seed *must* be an integer of None. If
        None, all seeds will be None (which seeds the RNG with the current
        time, as described in the documentation for the random module). If
        integer, the 'evolution' process is simply increment.
        """
        if start_seed is None:
            return itertools.repeat(None)
        else:
            return itertools.count(start_seed + 1)
    
    
    
    def _make_id_seed_generator(self, start_seed, num_rows):
        '''
        Make a generator for all the (row_id, seed) pairs for this run.
        '''
        seed = int(start_seed)
        # Seed the RNG. Will need this when generating row IDs. Note: if
        # the user does not set this, it defaults to 0. 
        spar_random.seed(seed)
    
        id_seed_generator = \
            itertools.izip(self._row_id_generator(num_rows),
                           self._seed_generator(seed))
        return itertools.islice(id_seed_generator, num_rows)
    


    

    def __init__(self, options, logger, dist_holder):
        self.options = options
        self.logger = logger
        self.dist_holder = dist_holder
        self.id_seed_generator = \
            self._make_id_seed_generator(self.options.random_seed,
                                         self.options.num_rows)



    
        
    #
    # Top-level / entry point
    #

        
    def start(self):
        """ 
        Generate the requested rows. This simpley calls either
        _generate_rows_single_process or _generate_rows_multi_process, depending
        on the number of processes requested by the user. Either way the batch
        level results are obtained, reduced, and returned
        """
        
        if self.options.num_processes == 1:
            return self._generate_rows_single_process()
        
        else:
            batch_result_tally = self._generate_rows_multi_process()                 
            return self._reduce_batch_results(batch_result_tally)
    # 
    # Single-processor mode
    #


    def _generate_rows_single_process(self):
        '''
        Generate all rows in single-process mode.
        '''
                
        # Note: when we figure out what we want to do with respect to
        # intermediate errors, graceful restarting, etc., we will
        # need to revisit this function and insert the proper machinery.
        
        
        self.logger.info("Generating rows in single-processor mode")
        engine = data_generator_engine.DataGeneratorEngine(self.options,
                                                           self.dist_holder)
        
        ripr = RowAggregatorProgressReporter(self.logger, 
                                           self.options.num_rows)
        

        batches = self._make_multiprocessing_batches(self.id_seed_generator,
                                                     self.options.batch_size)

        batch_result_tally = None
        
        for batch in batches:
            batch_result = engine.generate_and_aggregate_rows(batch)
            batch_result_tally = self._record_batch_results(batch_result_tally,
                                                             batch_result)
            ripr.add(len(batch))
            
        ripr.done()
        results = self._reduce_batch_results(batch_result_tally)
        engine.done()
        return results

        
    


    #
    # Multiprocessing
    # ---------------
    #
    # Okay, here's how multiprocessing works: the main process, called the
    # mothership, will directly spawn a number of worker processes, called
    # workers, to generate the rows. Communication between the workers and the
    # mothership takes place over three queues:
    #
    # * A task queue, over which the mothership sends tasks to the workers,
    #
    # * A results queue, where the workers send back to the mothership the
    # results of task processing, and
    #
    # * An errors queue, where the workers send any errors/exceptions back to
    # the mothership.
    #
    # Likewise, there are five kinds of messages to go over these queues:
    #
    # * A BATCH message, which contains a batch of rows for workers to generate.
    # This message travels over the task queue. Also, the message contains two
    # things: The batch itself, as an explicit list of row-id/row-seed pair, and
    # a batch ID, which is used in the resulting results message.
    # 
    # * A GENERATED message, which travels over the results queue. This message
    # contains a batch-id, inidicating that the named batch has been
    # fully generated without errors, and the aggregate results for that batch.
    #
    # * A DONE message, which travels over the tasks queue. This message
    # indicates to the worker that it is to terminate gracefully.
    #
    # * A DYING message, which travels from worker to mothership over the
    # results queue. This message contains the id of the worker, indicates that
    # the given worker is in a state where it can die gracefully. Due to
    # problems with earlier versions of this engine, a worker will both attempt
    # to terminate itself *and* the mothership will attempt to terminate workers
    # who have sent this message.
    #
    # * An EXCEPTION message, which travels over the errors queue. This message 
    # results from an exception in a worker process, and holds information about
    # the exception itself. 
    #
    # Workers are pretty simple: they loop endlessly, taking tasks from the task
    # queue and processing them. If the task is a BATCH message, the worker
    # generates the rows and sends back a GENERATED message over the results
    # queue. (The GENERATED message will hold the same batch ID as the BATCH
    # message.) If the task was the DONE message, the worker terminates
    # gracefully. And if an exception if raised on the worker process (including
    # a KeyboardInterrupt) the worker will trap it, embed it in an EXCEPTION
    # message, send the EXCEPTION message over the errors queue, and then
    # terminates gracefully.
    #
    # The mothership, on the other hand, has a little more to do. It starts by
    # creating the queues and filling the task queue with some initial batches.
    # It then creates a mapping called outstanding_batches, holding all the
    # batches which are currently 'outstanding': put into the task queue but
    # not yet received back through the results queue. (Batches are indexed by
    # their batch- id.) This mapping serves two purposes: it helps the
    # mothership to know when the workers are done, and it will come in handy if
    # we ever want to implement intermediate failures and graceful restarts.
    #
    # Anyway, once the mothership has put inital tasks into the task queue and
    # the outstanding_batches mapping, it spawns the worker processes and starts
    # them. It also creates a RowAggregatorProgressReporter (ripr) object to
    # keep the user appraised of the progress. It then monitors the results
    # queue and the errors queue. If it ever receives a message over the errors
    # queue, it terminates all the workers and re-raises the exception it
    # received. If it receives a GENERATED message, on the other hand, it
    # updates the ripr, removes the finished batch from outstanding_batches, 
    # puts another task into the task queue. (Generally, the mothership will try
    # to keep the task queue and outstanding_batches at about three tasks per
    # worker process.) The mothership will then aggreate the results from the
    # GENERATED message into its internal running 'tally' of aggregate results.
    # 
    # This continues until all batches are confirmed to be processed or the
    # mothership receives any messages over the error queue. If all batches are
    # confirmed to be done, then the mothership sends the DONE message to all
    # workers. THe workers clean up any open files, subprocesses, etc., send
    # back a DYING message to the mothership, and terminate. The mothership,
    # upon receiving a DYING message, attempts to terminate the worker as well,
    # in the spirit of belt *and* suspenders. 
    # 
    # 
    # As said, any exception in a worker will be sent back to the mothership,
    # and the mothership handles it using the same code that it uses for its own
    # exceptions. This allows for nice, uniform central handling of all errors.
    # Currently, the error handling proceedure is: the mothership terminates all
    # workers (they do not get a chance to call cleanup-code) and the mothersip
    # re-raises the exceptions for the benefit of the user.
    #
    # This design has been benchmarked against other leading brands (such as
    # multiprocessing.Pool) and has been found to be both faster and easier to
    # debug.

    
    SIGNALS = Enum('BATCH', 'GENERATED', 'DYING', 'EXCEPTION', 'DONE')
    
    @staticmethod
    def _make_multiprocessing_batches(itr, size):
        '''
        Return generator which breaks iterator itr nto sub-lists of the 
        given size, 
        where the last sub-list is rounded down. That is, 
        make_batches([1,2,3,4,5], 2) should return a generator which produces
        [1,2], [3,4], and [5].
        
        '''
        first_iterator = itertools.chain(itr)
        while True:
            return_me = list(itertools.islice(first_iterator, size))
            if return_me:
                yield return_me
            else:
                raise StopIteration
            
    @staticmethod
    def extract_batch_bounds(batch):
        '''
        Extracts the first and last tuple from a batch and returns in tuple
        format. That is, extract_batch_bounds([(1,2), (3,4), (5,6)]) should return
        ((1,2), (4,5)). This will be useful in multiprocessing mode where we will
        want a compact (and hashable!) way to identify a batch.
        '''
        return (batch[0], batch[-1])
    
    
    
    @staticmethod
    def _spawned_worker(options, 
                        dist_holder, 
                        tasks_queue, 
                        results_queue, 
                        errors_queue):
        """
        Function to be executed by worker processes in multi-processing mode. 
        Will loop over tasks in the task_queue. If the task is a batch to 
        generate, will generate and aggregate the batch. If the task is the DONE
        signal, will clean up and exit. If exceptions/errors occur during either,
        will capture the exception and send over the errors_queue.
        """
        
        return_code = 0 
        engine = data_generator_engine.DataGeneratorEngine(options,
                                                           dist_holder)
        done_attempted = False
        try:
            while True:
                # Note: the following line will block.
                task = tasks_queue.get()
                (signal, payload) = task
                if signal == Worker.SIGNALS.BATCH:
                    (batch_id, batch) = payload
                    # track whether we've already tried to call engine.done(),
                    # so that we don't call it for a second time in the except:
                    # clause
                    aggr_results = engine.generate_and_aggregate_rows(batch)
                    msg = (Worker.SIGNALS.GENERATED, batch_id, aggr_results)
                    results_queue.put( msg )
                else:
                    assert signal == Worker.SIGNALS.DONE
                    # Clean up code goes here.
                    if engine:
                        done_attempted = False
                        engine.done()
                    results_queue.put( (Worker.SIGNALS.DYING, os.getpid()) )
                    break
        except BaseException:

            # An exception or interrupt occured somewhere. Capture,
            # Send back to mothership over error_queue, and exit.
            # Note we use BaseException instead of Exception so as to
            # capture KeyboardInterrupt too.
            
            exception_type, value, _ = sys.exc_info()
            # It would be nice to send the traceback object itself back to the
            # mothership so that the exception could be re-raised in its
            # original form. Unfortunately, though, traceback objects cannot be
            # pickled and therefore cannot be put in the queue. So, we do the
            # best we can: we get the traceback information as a string and send
            # that instead.
            tb_str = traceback.format_exc()
            msg =  (Worker.SIGNALS.EXCEPTION, (exception_type, value, tb_str))
            errors_queue.put( msg )
            
            # Don't call done() if already attempted-- you're already dealing
            # with an exception from it.
            if not done_attempted:
                engine.done()
            return_code = 1
        finally:
            # Note: the following while-loops were added in an attempt to 
            # debug/eliminate a deadlock condition.
            while not tasks_queue.empty():
                pass
            while not results_queue.empty():
                pass
            while not errors_queue.empty():
                pass
        
            tasks_queue.close() 
            results_queue.close() 
            errors_queue.close()
            sys.exit(return_code)
    
    
    
    def _generate_rows_multi_process(self):
        '''
        The code run by the mothership in multi-process mode. Returns
        the non-reduced batch level results
        '''
        self.logger.info("Generating rows in multiprocessor mode")
    
    
    
        unqueued_batches = \
            self._make_multiprocessing_batches(self.id_seed_generator,
                                               self.options.batch_size)
    
        # Queue for sending batches to workers:
        tasks_queue = multiprocessing.Queue()
         
        # Queue for receiving batch-results from workers:
        results_queue = multiprocessing.Queue()
         
        # Queue for receiving error/exceptions/interrupts from workers:
        errors_queue = multiprocessing.Queue()
         
    
        # Mothership will keep track of outstanding batches: batches which have
        # been sent to workers but have *not* been confirmed to be generated by
        # workers. In particular, the mothership will use a batch_id -> batch
        # mapping to do so.
        outstanding_batches = {}


        # Maintain a running record of batch-level aggregate 
        # results sent back in GENERATED messages.
        batch_result_tally = None

        
        # Fill both the task queue and the dictionary of outstanding
        # batches with initial tasks
        self.logger.debug("Filling task queue with initial batches")
    
        # Put in four tasks per work. After each process takes a
        # task, this should maintain a steady state of about three
        # tasks per worker.
        num_initial_batches = 4 * self.options.num_processes
        for (_, batch) in itertools.izip(xrange(num_initial_batches),
                                         unqueued_batches):
            batch_id = self.extract_batch_bounds(batch)
            task = (self.SIGNALS.BATCH, (batch_id, batch))
            tasks_queue.put(task)
            outstanding_batches[batch_id] = batch
    
        # Start the pool of workers
        self.logger.debug("Task queue filled. Starting pool of workers.")
        
        process_list = \
            [multiprocessing.Process(target = Worker._spawned_worker,
                                     args = (self.options,
                                             self.dist_holder,
                                             tasks_queue,
                                             results_queue,
                                             errors_queue))\
             for _ in xrange(self.options.num_processes)]
            
        for proc in process_list:
            proc.daemon = True
            proc.start()
            
            
        # Now, get results from results_queue and exceptions from errors_queue
        ripr = RowAggregatorProgressReporter(self.logger, self.options.num_rows)
        try:
            while outstanding_batches:
                
                # Give exceptions priority and check the errors_queue first
                try:
                    self.check_errors_queue(errors_queue)
        
                except Queue.Empty:
                    # No errors to deal with. Get results from the result queue.
                    try:
                        # Don't want to get hung waiting for results when
                        # an error arrives on the other queue in the meantime.
                        # So, time-out after one second.
                        msg = results_queue.get(True, 1)
                        (signal, batch_id, batch_results) = msg
                        assert signal == self.SIGNALS.GENERATED
                        batch = outstanding_batches[batch_id]
                        self.logger.debug('Received results for batch %s', 
                                          batch_id)
    
                        # process received batch
                        ripr.add_list(batch)
                        del outstanding_batches[batch_id]

                        batch_result_tally = \
                                self._record_batch_results(
                                        batch_result_tally,
                                        batch_results)
    
                        # place a new tasks in the tasks queue
                        try:
                            new_batch = unqueued_batches.next()
                            new_batch_id = self.extract_batch_bounds(new_batch)
                            self.logger.debug('Now queuing batch %s', 
                                              new_batch_id)
                            new_task = (self.SIGNALS.BATCH, 
                                        (new_batch_id, new_batch))
                            tasks_queue.put(new_task)
                            outstanding_batches[new_batch_id] = new_batch
                        except StopIteration:
                            # No more batches left to be generated by 
                            # unqueued_batches
                            self.logger.debug('All batches have been queued.')
                    
                    except Queue.Empty:
                        # Not a sign of a problem, just that there are no
                        # results yet. Loop again, just to check for errors.
                        continue
                    # Note: all other exceptions propogate out to the try:
                    # around the while-loop
        except:
            # There was an exception while executing the while-loop. Either
            # in the while-loop itself, or in a worker and sent back to the
            # mothership. IN either case, terminate all of the processes and
            # re-raise the exception for the benefit of the user.

            self.logger.debug("Exception somewhere. Shutting down workers.")

            for proc in process_list:
                proc.terminate()
            self.flush_queues([tasks_queue, errors_queue, results_queue])
            for proc in process_list:
                proc.join()
            self.logger.debug("re-raising exception.")

            raise
            
        else:
            # No exception raised in the workers or the mothership. Graceful 
            # termination.
            #
            # At this point, the results queue should be empty. Send the DONE
            # signal to each worker. Get back a DYING message
            # from each worker, and wait for it to die. If it does not die in
            # a given amount of time, kill it.
            ripr.done()

            self.logger.debug("Attempting to shut down workers")

            for _ in process_list:
                tasks_queue.put( (self.SIGNALS.DONE, None) )

            self.logger.debug("Done signals sent. ")

            live_processes = {process.pid : process for process in process_list}

            minutes_since_last_message = 0
            
            while live_processes:
                self.logger.debug("Waiting to hear back from: %s", 
                                  live_processes)
                try:
                    # TODO(njhwang) this was lengthened since 5 seconds didn't
                    # appear long enough for aggregators to finalize (especially
                    # if flushing a large amount of data?), so just lengthened
                    # this to a minute. Generally, it's fine if this timeout
                    # expires and there are no errors in the queue.
                    # TODO(njhwang) update...it looks like even 60 seconds isn't
                    # sufficient here. if the workers have tons of aggregators
                    # that are chewing on stuff, timing out here will end data
                    # generation and not give them a chance to finish. seems
                    # like we need to block indefinitely here, and manually kill
                    # if needed after checking to see how many rows got
                    # generated and whether query data was flushed to
                    # files/results databases.
                    msg = results_queue.get(True, 60)
                    minutes_since_last_message = 0
                except Queue.Empty:
                    minutes_since_last_message += 1
                    
                    # There aren't enough DYING messages. Go check the errors 
                    # queue
                    try:
                        self.check_errors_queue(errors_queue)
                        # Note: the above call will never return-- only 
                        # raise exceptions
                    except Queue.Empty:
                        # No error messages. Maybe we haven't waited long enough
                        # Log it, but try again
                        self.logger.debug("Waiting for DYING messages from "
                                          "processes %s. No response from "
                                          "them, but no errors from them "
                                          "either. Minutes since last message "
                                          "reception: %s.",
                                          live_processes.keys(),
                                          minutes_since_last_message)
                        continue
        

                self.logger.debug("Received message: %s", msg)      

                (signal, pid) = msg
                assert signal == Worker.SIGNALS.DYING
                assert pid in live_processes, (pid, live_processes)

                del live_processes[pid]

            for proc in process_list:
                proc.terminate()

            self.flush_queues([tasks_queue, errors_queue, results_queue])
            
            for proc in process_list:
                proc.join()            
        
            return batch_result_tally
        finally:
            # When we're ready to deal with 
            # intermediate failures, progress-logging and
            # graceful restarts, etc., we may want to check
            # results_queue for any finished but un-logged batches.
            # In the meantime, just close the queues().

            tasks_queue.close()
            errors_queue.close()
            results_queue.close()

    def check_errors_queue(self, errors_queue):
        '''
        Check the errors queue and raise any exception message
        found there. Will never return: either raises the 
        found exception, or Queue.Empty if no error is found.
        '''
        msg = errors_queue.get_nowait()
        (signal, payload) = msg
        assert signal == self.SIGNALS.EXCEPTION
        (exception_type, value, tb_str) = payload
        self.logger.error(tb_str)
        raise exception_type, value



    def flush_queues(self, queues):
        for queue in queues:
            while not queue.empty():
                _ = queue.get()
        return
        

    def _record_batch_results(self, running_list, batch_result):
        """
        Add a batch-level result to the running list of batch-level results.
        This running tally has been unzipped from the batch-level results.
        That is, a list of batch-level results would look like:
        
           [ [a1, a2, a3], [a1, a2, a3], ... [a1, a2, a3] ]
        
        where a1 is a batch-level result for aggregator 1, etc. The running
        tally of results is stored in the format
        
           [ [a1, a1, a1,... a1], [a2, a2, a2... a2], [a3, a3, a3, ... a3] ]

        This will speed up the final aggregation.
        """
        if running_list is None:
            running_list = [ [] for _ in batch_result]
        else:
            assert len(running_list) == len(batch_result)
            
        for (agg_level_tally, agg_batch_result) in zip(running_list,
                                                       batch_result):
            agg_level_tally.append(agg_batch_result)
        return running_list

    def _reduce_batch_results(self, batch_level_results):
        '''
        Helper method for the mothership to use to reduce together
        the running list of batch-level results. The batch-level result list
        should be in the format produced by record_batch_results.
        Note: this step is parallelized with each aggregator being handled by 
        a single process. It should only be called in multi-processor mode.
        '''
        assert len(self.options.aggregators) == len(batch_level_results)
        start_time = datetime.datetime.today()
        self.logger.info("Starting to reduce batch-level results: %s",
                         str(start_time))
        
        agg_tuples = zip(self.options.aggregators, batch_level_results)
        num_aggs = len(agg_tuples)
        
        top_level_results = []
        
        curr_aggregator = 1
        for (agg, agg_batch_results) in agg_tuples:
            self.logger.info("Starting batch-level aggregation for number %d out of %d: %s",
                             curr_aggregator,
                             num_aggs,
                             datetime.datetime.today())
            curr_result = agg.reduce_list(agg_batch_results)
            top_level_results.append(curr_result)
            self.logger.info("Finished batch-level aggregation for number %d out of %d: %s",
                             curr_aggregator,
                             num_aggs,
                             datetime.datetime.today())
            curr_aggregator += 1
        
        
#        # We allocated a pool in __init__(). Let's use that.
#        pool = self.aggregation_pool
#        
#        agg_tuples = zip(self.options.aggregators, batch_level_results)
#        num_aggs = len(agg_tuples)
#        
#        
#        async_results = [pool.apply_async(_call_reduce_list, 
#                                          args = args_tuple) 
#                         for args_tuple in agg_tuples]
#                        
#        pool_done = False
#        while not pool_done:
#            time.sleep(1)
#            finished_jobs = [1 for ar in async_results if ar.ready()]
#            num_finished = len(finished_jobs)
#            if num_finished != num_aggs:
#                self.logger.info("%s: Finished %s of %s aggregators", 
#                                 str(datetime.datetime.today()),
#                                 num_finished,
#                                 num_aggs)
#            else:
#                pool_done = True
#                
#        top_level_results = [ar.get() for ar in async_results]
#        pool.close()
#        pool.join()

        end_time = datetime.datetime.today()
        self.logger.info("Finished reducing batch-level results: %s",
                         str(end_time))
        
        return top_level_results

