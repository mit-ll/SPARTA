# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for text_distribution
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Sep 2012   jch            Original Version
# *****************************************************************
from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import collections


from spar_python.common.distributions.text_generator \
    import TextGenerator
from spar_python.common.distributions.text_distribution \
    import TextDistribution
from StringIO import StringIO
import spar_python.common.spar_random as spar_random
import time
import unittest

class TextDistributionTest(unittest.TestCase):

    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

    def test_construction_single_file(self):
        """Very simple test that just makes sure constructing the object with a
        single file doesn't crash."""
        f = StringIO('This is the file. It has tokens in it')
        gen = TextGenerator((f,))
        dist = TextDistribution(gen, 10, 100)


    def test_basic_generation(self):
        """Given a very small sample of text that can only generate a single
        known sequence make sure we get what we expect."""
        f = StringIO('This is it')
        gen = TextGenerator((f,))
        dist = TextDistribution(gen, 11, 11)
        gened_text = dist.generate()       
        goal_words = [' ', 'This', ' ', 'is', ' ', 'it', '.']
        goal_stems = [None, 'THI', None, 'IS', None, 'IT', None]
        goal_uppers = [' ', 'THIS', ' ', 'IS', ' ', 'IT', '.']
        self.assertListEqual(gened_text.word_list, goal_words, self.seed_msg)
        self.assertListEqual(gened_text.stem_list, goal_stems, self.seed_msg)
        self.assertListEqual(gened_text.upper_word_list, goal_uppers, self.seed_msg)

    def test_basic_generation_range(self):
        """Check that we get a string in the range we expect."""
        f = StringIO('This is it')
        gen = TextGenerator((f,))
        dist = TextDistribution(gen, 11, 22)
        for i in xrange(20):
            generated = dist.generate()
            generated_str = str(generated)
            self.assertLessEqual(len(generated_str), 22, self.seed_msg)


    def test_respect_word_boundaries(self):
        """Check that we only get entire words"""
        f = StringIO('this is it')
        gen = TextGenerator((f,))
        dist = TextDistribution(gen, 200, 300)
        valid_words = set(['this', 'is', 'it', ' ', "."])
        for i in xrange(20):
            generated = dist.generate()
            seen = set()
            for word in generated.word_list:
                seen.add(word)
        
            self.assertSetEqual(seen, valid_words, self.seed_msg)


    def test_dont_generate_alarm_words(self):
        str = 'This is the file. It has tokens in it. ' * 1000
        f = StringIO('This is the file. It has tokens in it')
        gen = TextGenerator((f,))
        dist = TextDistribution(gen, 1000, 2000)
        self.assertFalse(dist.alarmwords_enabled())


    def test_generate_alarm_words(self):
        str = 'This is the file. It has tokens in it. ' * 1000
        f = StringIO('This is the file. It has tokens in it')
        gen = TextGenerator((f,))
        dist = TextDistribution(gen, 1000, 2000, add_alarmwords = True)

        self.assertTrue(dist.alarmwords_enabled())
        
        alarmwords =  dist.alarmwords()
        
        self.assertGreaterEqual(len(alarmwords), 2)

        # WIll count the number of generated texts containing 
        # 0 alarmwrods, 1 alarmword, etc.
        num_alarmwords_counts = collections.Counter()
        
        # Will count the nubmer of generated texts that have 2 alarmwords with
        # 0 characters between them, 2 alarmwords with distance 1 between them,
        # etc.
        distance_counter = collections.Counter()
        
        # For each alarmword, count the number of generated-texts which 
        # (1) have an alarmword, and (2) have that alarmword *first*
        first_alarmwords = collections.Counter()
        
        num_iterations = 10000
        
        for _ in xrange(num_iterations):
            
            generated_text = dist.generate()
            generated_str = generated_text.str()
            
            num_alarmwords = 0
            
            # update num_alarmwords_counts
            alarm_words_list = []
            for alarmword in alarmwords:
                if alarmword in generated_str: 
                    num_alarmwords += 1
                    alarm_words_list.append(alarmword)
            for alarmword in alarm_words_list:
                if any([alarmword in word and alarmword != word 
                                    for word in alarm_words_list]):
                    num_alarmwords -= 1
            num_alarmwords_counts[num_alarmwords] += 1
            
            
            if num_alarmwords >= 1:
                
                indices_and_words = \
                    [ (generated_str.find(aw), aw) for aw in alarmwords]
                indices_and_words = filter(lambda (x,_) : x >= 0, 
                                             indices_and_words)
                indices_and_words.sort() # will sort by first component 
                                            # of the contained tuples
                
                # update first_alarmwords
                (_, first_alarmword) = indices_and_words[0]
                first_alarmwords[first_alarmword] += 1


                if num_alarmwords >= 2:
                    
                    # update distance_counter                 
                    for n in range(len(indices_and_words) - 1):
                        (first_index, alarmword) = indices_and_words[n]
                        (second_index, _) = indices_and_words[n + 1]
                        distance = second_index - first_index - len(alarmword)
                        distance_counter[distance] += 1
                        
        
        # Okay, now check the distributions we just measures.
        
        # The values in observed_alarmword_counts should correspond
        # to the constants for AlarmWordsDistribution.dist1
        observed_alarmword_counts = set(num_alarmwords_counts.keys())
        self.assertSetEqual(observed_alarmword_counts, set([0,1,2]))
        
        for (num_alarmwords, expected_proportion) in [(0, 0.8),
                                                      (1, 0.1),
                                                      (2, 0.1)]:
            
            observed_proportion = \
                num_alarmwords_counts[num_alarmwords] / num_iterations
            self.assertGreater(observed_proportion, expected_proportion * 0.5)
            self.assertLess(observed_proportion, expected_proportion * 1.5)

        ## This is commented out because the distribution is no longer uniform
        ## which means as a result there is no easy way to compare the alarm
        ## word set which is now over 400 words 
        """
        # The values in first_alarmwords should match the distribution of
        # AlarmWordsDistribution.dist2 (currently a uniform distribution
        observed_first_alarmwords = set(first_alarmwords.keys())
        self.assertSetEqual(observed_first_alarmwords,
                            set(dist.alarmwords()))
        

        alarmword_row_count = sum([num_alarmwords_counts[1],
                                   num_alarmwords_counts[2]])

        for alarmword in dist.alarmwords():
            expected_proportion = 1 / len(dist.alarmwords())
            observed_proportion = \
                first_alarmwords[alarmword] / alarmword_row_count
            self.assertLess(observed_proportion, expected_proportion * 1.5)
            self.assertGreater(observed_proportion, expected_proportion * 0.5)
        """       
        # The values in distance_counter should correspond (roughly) to the
        # constants for AlarmWordsDistribution.dist3
        for (max_distance, expected_proportion) in [(25, 0.25),
                                                    (50, 0.5),
                                                    (100, .75),
                                                    (200, 1)]:
            
            under_max_distance = 0
            for n in range(max_distance+1):
                under_max_distance += distance_counter[n]
            
            observed_proportion = under_max_distance / num_alarmwords_counts[2]
 
            self.assertLess(observed_proportion, expected_proportion * 1.5)
            self.assertGreater(observed_proportion, expected_proportion * 0.5)
            
        

