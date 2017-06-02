# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Tests for generated_text
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  01 Oct 2013   jch            Initial file
# *****************************************************************
from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import unittest
import collections
import copy
import re

from spar_python.common.distributions.generated_text import GeneratedText

class GeneratedTextTest(unittest.TestCase):

    def setUp(self):
        self.word_list = ['It', ' ', 'was', ' ', 'the', ' ', 'best', ' ', 'of', ' ', 'times', '.']
        self.stem_list = ['it', None, 'was', None, 'the', None, 'best', None, 'of', None, 'time', None]
        self.upper_word_list = [word.upper() for word in self.word_list]
        self.generated_text = GeneratedText(self.word_list,
                                            self.stem_list,
                                            self.upper_word_list)
        


    def test_to_string(self):
        goal_string = 'It was the best of times.'

        generated_string = str(self.generated_text)
        self.assertEqual(generated_string, goal_string)

        generated_string = self.generated_text.str()
        self.assertEqual(generated_string, goal_string)

    def test_to_upper_string(self):
        generated_string = self.generated_text.upper()
        goal_string = 'IT WAS THE BEST OF TIMES.'
        self.assertEqual(generated_string, goal_string)

    def test_contains_stem(self):
        self.assertTrue(self.generated_text.contains_stem("it"))
        self.assertTrue(self.generated_text.contains_stem("was"))
        self.assertTrue(self.generated_text.contains_stem("best"))
        self.assertTrue(self.generated_text.contains_stem("time"))
        self.assertFalse(self.generated_text.contains_stem("now"))
        self.assertFalse(self.generated_text.contains_stem("times"))
        self.assertFalse(self.generated_text.contains_stem("season"))
        self.assertFalse(self.generated_text.contains_stem("discontent"))

    def test_contains_upper(self):
        self.assertTrue(self.generated_text.contains_upper("IT"))
        self.assertTrue(self.generated_text.contains_upper("WAS"))
        self.assertTrue(self.generated_text.contains_upper("BEST"))
        self.assertTrue(self.generated_text.contains_upper("TIMES"))
        self.assertFalse(self.generated_text.contains_upper("It"))
        self.assertFalse(self.generated_text.contains_upper("time"))
        self.assertFalse(self.generated_text.contains_upper("the"))
        self.assertFalse(self.generated_text.contains_upper("discontent"))

        
        
    def test_word_set(self):
        generated_word_set = self.generated_text.word_set
        goal_set = set(['It', 'was', 'the', 'best', 'of', 'times'])
        self.assertSetEqual(generated_word_set, goal_set)
        
    def test_upper_set(self):
        generated_word_set = self.generated_text.upper_set
        goal_set = set(['IT', 'WAS', 'THE', 'BEST', 'OF', 'TIMES'])
        self.assertSetEqual(generated_word_set, goal_set)
        
    def test_stem_set(self):
        generated_word_set = self.generated_text.stem_set
        goal_set = set(['it', 'was', 'the', 'best', 'of', 'time'])
        self.assertSetEqual(generated_word_set, goal_set)
        
    def test_add_single_alarmword(self):
        
        num_trials = 5000
        counts = collections.Counter()
        alarmword = "quadge"
        
        word_list = ['It', ' ', 'was', ' ', 'the', ' ', 'best', ' ', 
                     'of', ' ', 'times', '.', ' ', 'It', ' ', 'was', ' ', 
                     'the', ' ', 'worst', ' ', 'of', ' ', 'times', '.']
        stem_list = ['it', None, 'was', None, 'the', None, 'best', None, 
                     'of', None, 'time', None, None,  'it', None, 'was', 
                     None, 'the', None, 'worst', None, 'of', None, 'time', 
                     None]
        upper_word_list = [word.upper() for word in word_list]
        
        
        possible_sentences = \
            [
             "It was the quadge  best of times. It was the worst of times.",
             "It was the  quadge best of times. It was the worst of times.",
             "It was the best quadge  of times. It was the worst of times.",
             "It was the best  quadge of times. It was the worst of times.",
             "It was the best of quadge  times. It was the worst of times.",
             "It was the best of  quadge times. It was the worst of times.",
             "It was the best of times quadge . It was the worst of times.",
             "It was the best of times. quadge  It was the worst of times.",
             "It was the best of times.  quadge It was the worst of times.",
             "It was the best of times. It quadge  was the worst of times.",
             "It was the best of times. It  quadge was the worst of times.",
             "It was the best of times. It was quadge  the worst of times.",
             "It was the best of times. It was  quadge the worst of times.",
             "It was the best of times. It was the quadge  worst of times.",
             "It was the best of times. It was the  quadge worst of times.",
             ]
        num_sentences = len(possible_sentences)
                
        for _ in xrange(num_trials):
            word_list_copy = copy.copy(word_list)
            stem_list_copy = copy.copy(stem_list)
            upper_word_list_copy = copy.copy(upper_word_list)
        
            generated_text = GeneratedText(word_list_copy,
                                           stem_list_copy,
                                           upper_word_list_copy)

            generated_text.add_single_alarmword(alarmword)
            self.assertListEqual(generated_text.alarmwords, ['quadge'])
            self.assertIsNone(generated_text.alarmword_distances)

            generated_str = str(generated_text)
            self.assertIn(generated_str, possible_sentences)
            
            counts[generated_str] += 1
            
        for (sentence, count) in counts.items():
            proportion = count / num_trials
            expected_proportion = 1 / num_sentences
            self.assertLessEqual(proportion, expected_proportion * 1.5)
            self.assertGreaterEqual(proportion, expected_proportion * 0.5)


    def test_add_two_alarmwords(self):
        
        num_trials = 1000
        counts = collections.Counter()
        alarmword1 = "quadge"
        alarmword2 = "splonk"
        distance = 7

        word_list = ['It', ' ', 'was', ' ', 'the', ' ', 'best', ' ', 
                     'of', ' ', 'times', '.', ' ', 'It', ' ', 'was', ' ', 
                     'the', ' ', 'worst', ' ', 'of', ' ', 'times', '.']
        stem_list = ['it', None, 'was', None, 'the', None, 'best', None, 
                     'of', None, 'time', None, None,  'it', None, 'was', 
                     None, 'the', None, 'worst', None, 'of', None, 'time', 
                     None]
        upper_word_list = [word.upper() for word in word_list]
        
        possible_sentences = \
            [
             "It was the quadge  best splonk  of times. It was the worst of times.",
             "It was the  quadge best  splonk of times. It was the worst of times.",
             "It was the best quadge  of  splonk times. It was the worst of times.",
             "It was the best  quadge of  splonk times. It was the worst of times.",
             "It was the best of quadge   splonk times. It was the worst of times.",
             "It was the best of  quadge times splonk . It was the worst of times.",
             "It was the best of times quadge . It  splonk was the worst of times.",
             "It was the best of times. quadge  It  splonk was the worst of times.",
             "It was the best of times.  quadge It  splonk was the worst of times.",
             "It was the best of times. It quadge  was  splonk the worst of times.",
             "It was the best of times. It  quadge was  splonk the worst of times.",
             "It was the best of times. It was quadge  the  splonk worst of times.",
             "It was the best of times. It was  quadge the  splonk worst of times.",
             "It was the best of times. It was the quadge   splonk worst of times.",
             "It was the best of times. It was the  quadge  splonk worst of times.",
             ]
        num_sentences = len(possible_sentences)
        
        dist_finding_re = re.compile("quadge(.*)splonk")
        
        for _ in xrange(num_trials):
            word_list_copy = copy.copy(word_list)
            stem_list_copy = copy.copy(stem_list)
            upper_word_list_copy = copy.copy(upper_word_list)
        
            generated_text = GeneratedText(word_list_copy,
                                           stem_list_copy,
                                           upper_word_list_copy)

            generated_text.add_two_alarmwords(alarmword1, alarmword2, distance)
            self.assertListEqual(generated_text.alarmwords, 
                                 ['quadge', 'splonk'])
            self.assertEqual(len(generated_text.alarmword_distances),
                             1)
            actual_dist = generated_text.alarmword_distances[0]
            self.assertLessEqual(actual_dist, distance)
            
            generated_str = str(generated_text)
            self.assertIn(generated_str, possible_sentences)
            
            match_obj = dist_finding_re.search(generated_str)
            self.assertIsNotNone(match_obj, generated_str)
            chars_between = match_obj.group(1)
            self.assertEqual(len(chars_between), actual_dist, (actual_dist,
                                                               chars_between,
                                                               generated_str))
            
            counts[generated_str] += 1
            
        for (sentence, count) in counts.items():
            proportion = count / num_trials
            expected_proportion = 1 / num_sentences
            self.assertLess(proportion, expected_proportion * 1.5)
            self.assertGreater(proportion, expected_proportion * 0.5)


    def test_add_two_alarmwords_error(self):
        
        self.assertRaises(AssertionError, 
                          self.generated_text.add_two_alarmwords,
                          'quadge', 'splonk', 100)
        
