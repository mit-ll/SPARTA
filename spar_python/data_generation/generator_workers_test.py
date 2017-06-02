# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for generate_data
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Sep 2012   jch            Original version
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import StringIO as stringio
import unittest
import logging
import tempfile
import multiprocessing
import time

import spar_python.data_generation.generator_workers as gw
import spar_python.common.aggregators.counts_aggregator as ca
from spar_python.common.distributions.distribution_holder import *
from spar_python.common.distributions.base_distributions import *
from spar_python.common.distributions.bespoke_distributions import *
import spar_python.data_generation.spar_variables as sv
import spar_python.common.spar_random as spar_random
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import spar_python.data_generation.learn_distributions as learn_distributions
import spar_python.common.aggregators.base_aggregator \
    as base_aggregator

###############################################################
#
# The following classes are used in the unit tests below.
# They need to be defined at the top level of the module, though,
# so they can be pickled and send to multiprocess.Pools
#
#################################################################

class _DieDuringMap(base_aggregator.BaseAggregator):
    def __init__(self, batch_size, fields_needed):
        self.fields = fields_needed
        self._rows_left = spar_random.randint(1, batch_size-1)

    def fields_needed(self):
        return self.fields
        
    def map(self, row):
        if self._rows_left > 0:
            self._rows_left -= 1
        else:
            raise KeyboardInterrupt

    def done(self):
        pass

    @staticmethod
    def reduce(result1, result2):
        pass


class _DieDuringReduce(base_aggregator.BaseAggregator):
        
    def __init__(self, fields_needed):
        self.fields = fields_needed
        
    def map(self, row):
        return 1

    def done(self):
        pass
                            
    def fields_needed(self):
        return self.fields

    @staticmethod
    def reduce(result1, result2):
        raise KeyboardInterrupt


class _DieDuringDone(base_aggregator.BaseAggregator):
        
        
    def __init__(self, fields):
        self.fields = fields
        
    def map(self, row):
        return None
    
    def fields_needed(self):
        return self.fields

    def done(self):
        raise KeyboardInterrupt

    @staticmethod
    def reduce(result1, result2):
        # Note: will never be called
        pass


class _CountMultiples(ca.CountsAggregator):
        
    def __init__(self, multiple):
        super(_CountMultiples, self).__init__()
        self.multiple = multiple
        
        
    def map(self, row):
        return self.multiple

# Needed for test_mothership_death, below
#
#class _DieDuringLastReduce(base_aggregator.BaseAggregator):
#        
#        
#    def __init__(self, rows, fields):
#        self.rows = rows
#        self.fields = fields
#        
#    def map(self, row):
#        return 1
#
#    def fields_needed(self):
#        return self.fields
#
#    def done(self):
#        pass
#    
#    def reduce(self, result1, result2):
#        total = result1 + result2
#        if total == self.rows:
#            raise KeyboardInterrupt
#        else:
#            return total

class _CheckShared(base_aggregator.BaseAggregator):
        
    def __init__(self, fields):
        super(_CheckShared, self).__init__()
        self.map_call_counter = 0
        self.reduce_call_counter = 0
        self.fields = fields
        
    def map(self, row):
        self.map_call_counter += 1
        return 1

    def fields_needed(self):
        return self.fields

    def done(self):
        pass
    
    def reduce(self, result1, result2):
        self.reduce_call_counter += 1
        return result1 + result2



class _RowCollector(base_aggregator.BaseAggregator):
        
    def __init__(self):
        super(_RowCollector, self).__init__()
        return
        
    def map(self, row):
        row_id = row[sv.VARS.ID]
        row_values = (row[sv.VARS.FIRST_NAME],
                      row[sv.VARS.LAST_NAME],
                      row[sv.VARS.AGE])
        return {row_id : row_values }
        
        
    def fields_needed(self):
        return set([sv.VARS.ID,
                    sv.VARS.FIRST_NAME,
                    sv.VARS.LAST_NAME,
                    sv.VARS.AGE
                    ])

    def done(self):
        pass
    
    def reduce(self, result1, result2):
        result1.update(result2)
        return result1




################################################################################
#
# The actual unit tests
#
##############################################################################


class GenerateDataTest(unittest.TestCase):

    def setUp(self):
        
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

        class Object(object):
            pass

        
        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())
        self.dummy_object = Object()

        self.num_rows = 100
        self.options = gw.DataGeneratorOptions(random_seed = self.seed,
                                               num_processes = 2,
                                               num_rows = self.num_rows,
                                               verbose = False,
                                               aggregators = [],
                                               batch_size = 5)

        # Build the distribution-holder
        learner_options = Object()

        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(learner_options,
                                                 self.dummy_logger,
                                                 pums_files)
            
        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_male_first_names)),
             ('female_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_female_first_names)),
             ('last_names.txt', 
              stringio.StringIO(mock_data_files.mock_last_names))]
        names_dict = \
            learn_distributions.learn_name_dists(learner_options,
                                                 self.dummy_logger,
                                                 names_files)

        zipcode_files = \
            [('mock_zipcodes', 
              stringio.StringIO(mock_data_files.mock_zipcodes))]
        zipcode_dict = \
            learn_distributions.learn_zipcode_dists(learner_options,
                                                    self.dummy_logger,
                                                    zipcode_files)
        
        text_files = \
            [('mock_text', 
              stringio.StringIO(mock_data_files.mock_text_files))]
        text_engine = \
            learn_distributions.train_text_engine(learner_options, 
                                                  self.dummy_logger, 
                                                  text_files)
        streets_files = \
            [('mock street file', 
              stringio.StringIO(mock_data_files.mock_street_names))]
        address_dict = \
                learn_distributions.learn_street_address_dists(learner_options, 
                                                               self.dummy_logger, 
                                                               streets_files)

   
        
        self.dist_holder = \
            learn_distributions.make_distribution_holder(learner_options,
                                                         self.dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)


        self.worker = gw.Worker(self.options, 
                                self.dummy_logger,
                                self.dist_holder)


    def test_make_batches(self):
        l = [1,2,3,4,5]
        l2 = self.worker._make_multiprocessing_batches(l, 2)
        self.assertEqual(l2.next(), [1,2])
        self.assertEqual(l2.next(), [3,4])
        self.assertEqual(l2.next(), [5])
        self.assertRaises(StopIteration, l2.next)
         
        l3 = self.worker._make_multiprocessing_batches([], 2)
        self.assertRaises(StopIteration, l3.next)

        g4 = iter([1,2,3,4,5])
        g5 = self.worker._make_multiprocessing_batches(g4, 2)
        self.assertEqual(g5.next(), [1,2])
        self.assertEqual(g5.next(), [3,4])
        self.assertEqual(g5.next(), [5])
        self.assertRaises(StopIteration, l2.next)


    def test_extract_batch_bounds(self):
        batch = [(1,2), (3,4), (5,6), (7,8)]
        bounds = self.worker.extract_batch_bounds(batch)
        right_bounds = ((1,2), (7,8))
        self.assertEqual(bounds, right_bounds)
        
        batch2 = [(1,2)]
        bounds2 = self.worker.extract_batch_bounds(batch2)
        right_bounds2 = ((1,2), (1,2))
        self.assertEqual(bounds2, right_bounds2)


    def test_seed_generator(self):
        base_seed = 120
        seed_generator = self.worker._seed_generator(base_seed)
        for x in xrange(10):
            seed = seed_generator.next()
            self.assertEqual(seed, base_seed + x + 1)

    def _make_id_dictionary(self, id_list):
        '''
        Helper function for test_row_id_generator and 
        test_make_id_seed_generator to (a) break each row-id into
        the stripe id and within-stripe-id, and (b) make a dictionary
        where the stripe-ids are the keys (after calling str() on them) and
        each value is a list of all within-stripe id found.
        '''
        id_dict = {}
        for id in id_list:
            stripe_id = id >> 32
            stripe_id_str = str(stripe_id)            
            within_stripe = id - (stripe_id << 32)

            try:
                curr_list = id_dict[stripe_id_str]
                curr_list.append(within_stripe)
            except KeyError:
                curr_list = [within_stripe]
            id_dict[stripe_id_str] = curr_list
        return id_dict
        

            
    def test_row_id_generator(self):
        num_stripes = 3
        num_rows = self.worker.STRIPE_SIZE * num_stripes
        row_id_generator = self.worker._row_id_generator(num_rows)
        row_ids = [x for x in row_id_generator]
                
        # Are there enough row-ids?
        self.assertLessEqual(num_rows, len(row_ids))
        
        # Now, are the row-ids in the right format?
        id_dict = self._make_id_dictionary(row_ids)
        
        for stripe in id_dict:
            id_set = set(id_dict[stripe])
            self.assertEqual(len(id_set), self.worker.STRIPE_SIZE)

        num_stripes_out = len(id_dict.keys())
        self.assertLessEqual(num_stripes, num_stripes_out)


    def test_make_id_seed_generator(self):
        num_stripes_in = 3
        random_seed = 10
        num_rows = self.worker.STRIPE_SIZE * num_stripes_in
        num_rows_out =  self.worker.STRIPE_SIZE * num_stripes_in
        
        id_seed_generator = \
            self.worker._make_id_seed_generator(random_seed,
                                                num_rows)
        
        id_seeds = [x for x in id_seed_generator]
        
        self.assertEqual(len(id_seeds), num_rows_out) 

        ids = []
        seeds = []
        for (id, seed) in id_seeds:
            ids.append(id)
            seeds.append(seed)
            
        self.assertEqual( len(set(ids)),  num_rows_out)
        self.assertEqual( len(set(seeds)),  num_rows_out)

        id_dict = self._make_id_dictionary(ids)
        
        self.assertLessEqual(num_stripes_in, len(id_dict.keys()))
        
        for stripe_list in id_dict.values():
            self.assertEqual(len(stripe_list), len(set(stripe_list)))
            self.assertLessEqual(len(stripe_list), self.worker.STRIPE_SIZE)
            
            

    def test_generate_aggregate_results(self):
                
        self.options.aggregators = [ca.CountsAggregator()]

        for num_processes in [1,2]:
    
            self.options.num_processes = num_processes
    
            self.worker = gw.Worker(self.options, 
                                                   self.dummy_logger,
                                                   self.dist_holder)
    
            result = self.worker.start()
            
            correct_result = [self.num_rows]
            
            self.assertListEqual(result, correct_result)
        
        
        
    def test_aggregator_death1(self):

        fields_needed = self.dist_holder.var_order

        for num_processes in [1,2]:

            batch_size = 100
            num_rows = batch_size * num_processes
    
    
            self.options.aggregators = [_DieDuringMap(batch_size,
                                                      fields_needed)]
                
            self.options.num_processes = num_processes
            self.options.num_rows = num_rows
            
            self.worker = gw.Worker(self.options, 
                                    self.dummy_logger,
                                    self.dist_holder)
            with self.assertRaises(KeyboardInterrupt):
                self.worker.start()
    


    def test_aggregator_death2(self):

        fields_needed = self.dist_holder.var_order


        self.options.aggregators = [_DieDuringReduce(fields_needed)]

        for num_processes in [1,2]:

            self.options.num_processes = num_processes
            
            self.worker = gw.Worker(self.options, 
                                    self.dummy_logger,
                                    self.dist_holder)
    
            with self.assertRaises(KeyboardInterrupt):
                self.worker.start()
    


    def test_aggregator_death3(self):

        fields_needed = self.dist_holder.var_order


        self.options.aggregators = [_DieDuringDone(fields_needed)]

        for num_processes in [1,2]:

            self.options.num_processes = num_processes
            
            self.worker = gw.Worker(self.options, 
                                    self.dummy_logger,
                                    self.dist_holder)
            with self.assertRaises(KeyboardInterrupt):
                self.worker.start()
    



    def test_aggregation_multiproc(self):

        batch_size = 10
        num_processes = 2

        self.options.num_processes = num_processes
        num_rows = batch_size * num_processes * 2


        counts_agg = ca.CountsAggregator()
        self.options.aggregators = [counts_agg]

        self.options.num_rows = num_rows
        self.options.batch_size = batch_size
        
        self.worker = gw.Worker(self.options, 
                                self.dummy_logger,
                                self.dist_holder)

        x = self.worker.start()
        self.assertListEqual(x, [num_rows])


    def test_aggregation_singleproc(self):
        batch_size = 10
        num_processes = 1
        aggregator_name = 'counts_aggregator'

        self.options.num_processes = num_processes
        num_rows = batch_size * num_processes * 4

        self.options.aggregators = [ca.CountsAggregator()]

        self.options.num_rows = num_rows
        self.options.batch_size = batch_size
        
        self.worker = gw.Worker(self.options, 
                                self.dummy_logger,
                                self.dist_holder)

        x = self.worker.start()
        self.assertListEqual(x, [num_rows])

# Test currently breaks, but I have hope of being able to fix it in the future
#
#    def test_mothership_death(self):
#
#        batch_size = 10
#        num_processes = 2
#        num_rows = batch_size * num_processes * 2
#
#
#        fields_needed = self.dist_holder.var_order
#
#
#        self.options.aggregators = [_DieDuringLastReduce(num_rows,
#                                                         fields_needed)]
#
#        self.options.num_processes = num_processes
#        self.options.num_rows = num_rows
#        self.options.batch_size = batch_size
#        
#        self.worker = gw.Worker(self.options, 
#                                self.dummy_logger,
#                                self.dist_holder)
#
#        with self.assertRaises(KeyboardInterrupt):
#            x = self.worker.start()
#            print x

    def test_aggregators_not_shared(self):

        batch_size = 10
        num_processes = 2
        num_rows = batch_size * num_processes * 10


        fields_needed = self.dist_holder.var_order


        top_level_aggregator = _CheckShared(fields_needed)

        self.options.aggregators = [top_level_aggregator]

        self.options.num_processes = num_processes
        self.options.num_rows = num_rows
        self.options.batch_size = batch_size
        
        self.worker = gw.Worker(self.options, 
                                self.dummy_logger,
                                self.dist_holder)

        x = self.worker.start()

        # How many times did any CheckShared aggregator get called?
        self.assertListEqual(x, [num_rows])
        
        # How many times did the *top-level* CheckShared.map get called?
        # IF a single aggregator was shared, it would be 200
        # If the mothership's aggregator is not shared with the workers,
        # it should be zero.
        self.assertEqual(top_level_aggregator.map_call_counter, 0)
        
        # How many times did the *top-level* CheckShared.reduce get called?
        # IF a single aggregator was shared, it would be 199. 
        # If the mothership's aggregator is not shared with the workers,
        # it should be 19.
        self.assertEqual(top_level_aggregator.reduce_call_counter, 19)



    def test_aggregator_order_preserved(self):

        batch_size = 10
        num_processes = 2
        num_rows = batch_size * num_processes * 10

        self.options.aggregators = [_CountMultiples(-1),
                                    _CountMultiples(0),
                                    _CountMultiples(0.5),
                                    _CountMultiples(1),
                                    ca.CountsAggregator(),
                                    _CountMultiples(10)]

        self.options.num_processes = num_processes
        self.options.num_rows = num_rows
        self.options.batch_size = batch_size
        
        self.worker = gw.Worker(self.options, 
                                self.dummy_logger,
                                self.dist_holder)

        x = self.worker.start()
        goal_results = [-num_rows, 0, num_rows/2, 
                        num_rows, num_rows, 10*num_rows]

        self.assertListEqual(x, goal_results)
        
    
    
    def test_id_repeatability(self):
        # THis is in response to a bug that made row-IDs not repeatable
        # The purposw of this test is to ensure that the generator will
        # generate the same rows, with the same row-ids, in both
        # single-processor and multi-processor modes.
        #
        # Note that this test is *LONG*. Unfortunately, it seems to take
        # a very long run to trip the bug, probably becuase it takes a while
        # for workers and mothership to get 'out of synch' in multiprocessing
        # mode.
        
        self.maxDiff = None 
                  
            
        self.options.random_seed = 10
        self.options.batch_size = 5
        num_batches = 225
        self.options.num_rows = self.options.batch_size * num_batches


        # Run 1
        
        self.options.aggregators = [ _RowCollector() ]
        self.options.num_processes = 1        
        self.worker = gw.Worker(self.options, 
                                self.dummy_logger,
                                self.dist_holder)
        result_list = self.worker.start()

        dict1 = result_list[0]
        self.assertEqual(len(dict1), self.options.num_rows)

        # Run 2
        self.options.aggregators = [ _RowCollector() ]
        self.options.num_processes = 2        
        self.worker = gw.Worker(self.options, 
                                self.dummy_logger,
                                self.dist_holder)
        result_list = self.worker.start()

        dict2 = result_list[0]
        self.assertEqual(len(dict2), self.options.num_rows)


        self.assertDictEqual(dict1, dict2)

        
