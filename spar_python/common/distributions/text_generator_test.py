# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Tests for text_generator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2011   omd            Original Version
# 23 Sept 2012   jch            updated to use SparTestCase
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import collections


from spar_python.common.distributions.text_generator \
    import TextGenerator
from StringIO import StringIO
import spar_python.common.spar_random as spar_random
import time
import unittest

class TextGeneratorTest(unittest.TestCase):

    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

    def test_construction_single_file(self):
        """Very simple test that just makes sure constructing the
        object with a single file doesn't crash."""
        f = StringIO('This is the file. It has tokens in it')
        gen = TextGenerator((f,))

    def test_construction_multiple_files(self):
        """Same as the above but with multiple files."""
        f1 = StringIO('This is the file. It has tokens in it')
        f2 = StringIO('This is the  2nd file.')
        gen = TextGenerator((f1, f2))

    def test_basic_generation(self):
        """Given a very small sample of text that can only generate a
        single known sequence make sure that is in fact what we get."""
        sentence = 'This is it'
        f = StringIO(sentence)
        gen = TextGenerator((f,))
        gened_text = gen.generate(len(sentence) + 1)
        # Note: leading space is intentional-- due to the way we add
        # the last three words, there will always be a space before the 
        # third-to-last word.
        goal_words = [' ', 'This', ' ', 'is', ' ', 'it', '.']
        goal_stems = [None, 'THI', None, 'IS', None, 'IT', None]
        goal_uppers = [' ', 'THIS', ' ', 'IS', ' ', 'IT', '.']
        self.assertListEqual(gened_text.word_list, goal_words, self.seed_msg)
        self.assertListEqual(gened_text.stem_list, goal_stems, self.seed_msg)
        self.assertListEqual(gened_text.upper_word_list, goal_uppers, self.seed_msg)

    def test_to_string(self):
        """Given a very small sample of text that can only generate a
        single known sequence make sure that is in fact what we get."""
        sentence = 'This is it'
        f = StringIO(sentence)
        gen = TextGenerator((f,))
        generated = gen.generate( len(sentence) + 1)
        generated_string = str(generated)
        self.assertEqual(generated_string, ' This is it.', self.seed_msg)


    def test_basic_generation2(self):
        """Given 'this is this. this is that.' a 4 token sequence
        would have to be either 'this is this.' or 'this is that.'"""
        f = StringIO('This is this. This is that.')
        gen = TextGenerator((f,))
        gened_text = gen.generate(13)

        # Note: leading spaces are expected (due to the last-three-words
        # mechanism.
        goal1_words = [' ', 'This', ' ' , 'is', ' ', 'this', '.']
        goal1_stems = [None, 'THI', None , 'IS', None, 'THI', None]
        goal1_uppers = [' ', 'THIS', ' ' , 'IS', ' ', 'THIS', '.']
        
        
        goal2_words = [' ', 'This', ' ' , 'is', ' ', 'that', '.']
        goal2_stems = [None, 'THI', None , 'IS', None, 'THAT', None]
        goal2_uppers = [' ', 'THIS', ' ' , 'IS', ' ', 'THAT', '.']
        

        if gened_text.word_list[5] == 'this':
            self.assertListEqual(gened_text.word_list, goal1_words, self.seed_msg)
            self.assertListEqual(gened_text.stem_list, goal1_stems, self.seed_msg)
            self.assertListEqual(gened_text.upper_word_list, goal1_uppers, self.seed_msg)
        else:
            self.assertListEqual(gened_text.word_list, goal2_words, self.seed_msg)
            self.assertListEqual(gened_text.stem_list, goal2_stems, self.seed_msg)
            self.assertListEqual(gened_text.upper_word_list, goal2_uppers, self.seed_msg)

    def test_multi_sentence(self):
        sentence = 'This is it'
        f = StringIO(sentence)
        gen = TextGenerator((f,))
        length = 2* len(sentence) + 3

        gened_text = gen.generate(length)

        goal_words = [ 'This', ' ', 'is', ' ', 'it', '.', ' ', 'This', 
                      ' ', 'is', ' ', 'it', '.']
        goal_uppers = [ 'THIS', ' ', 'IS', ' ', 'IT', '.', ' ', 'THIS', 
                      ' ', 'IS', ' ', 'IT', '.']
        goal_stems = [ 'THI', None, 'IS', None, 'IT', None, None,
                      'THI', None, 'IS', None,'IT', None]

        self.assertListEqual(gened_text.word_list, goal_words, self.seed_msg)
        self.assertListEqual(gened_text.stem_list, goal_stems, self.seed_msg)
        self.assertListEqual(gened_text.upper_word_list, goal_uppers, self.seed_msg)

    def test_long_generation(self):
        """Test various properties about longer sentences to make sure
        they seem correct."""
        f = StringIO('This is the sentence one.\n\nThis is the second '
                     'sentence. This is the third sentence!')
        gen = TextGenerator((f,))
        # Since this will generate several possible sentences we'll generate
        # lots of sentences and make sure only valid ones are produced. We'll
        # also check that in a run of 1000 all of the valid sentences are
        # produced at least once as that should pretty much always happen.
        generated_sentences = set()
        for i in xrange(1000):
            generated = gen.generate(60)
            generated_string = str(generated)
            generated_sentences.add(generated_string)
        
        # Here are all the valid sentences one could produce given the above:
        valid_sentences = set(
                ('This is the sentence one.',
                 'This is the second sentence.',
                 'This is the third sentence!'))

        # Since we are generating more than one sentence, we need
        # to check valid sentences against prefixes of generated
        # text
        
        def prefixes_some_sentence(valid, gens):
            for sentence in gens:
                if sentence.startswith(valid):
                    return True
            return False
                
        for s in valid_sentences:
            self.assertTrue( prefixes_some_sentence(s, generated_sentences),
                    'The following sentence was not observed:\n' 
                    + s
                    + '\n' + self.seed_msg)

        def prefixed_by_valid_sentence(gened, valids):
            for valid in valids:
                if gened.startswith(valid):
                    return True
            return False
                

        for s in generated_sentences:
            self.assertTrue( prefixed_by_valid_sentence(s, valid_sentences),
                    'The following invalid sentence was observed:\n' + s
                    + '\n' + self.seed_msg)
                            
    def test_basic_trigram(self):
        """
        Given a very small sample of text that can only generate a
        single known sequence, make sure we can only generate the 
        correct trigram.
        """
        sentence = 'Running is discouraged'
        f = StringIO(sentence)
        gen = TextGenerator((f,))
        generated = gen.generate_trigram(0,0.5)
        goal = "Running is discouraged"
        self.assertEqual(generated, goal, self.seed_msg)
                                    
    def test_trigram(self):
        """
        Given a very small sample of text that can only generate a
        single known sequence, make sure we can only generate the 
        correct trigram.
        """
        sentence = 'Running is discouraged. Running is discouraged. Running is encouraged.'
        f = StringIO(sentence)
        gen = TextGenerator((f,))
        generated = gen.generate_trigram(0,0.33)
        goal = "Running is encouraged"
        self.assertEqual(generated, goal, self.seed_msg)
    
       
    def test_basic_stemming(self):
        """
        Given a very small sample of text that can only generate a
        single known sequence, me sure we get the expected stems.
        """
        sentence = 'Running is discouraged'
        f = StringIO(sentence)
        gen = TextGenerator((f,))
        gened_text = gen.generate( len(sentence) + 1)
        goal_words = [' ', 'Running', ' ', 'is', ' ', 'discouraged', '.']
        goal_uppers = [' ', 'RUNNING', ' ', 'IS', ' ', 'DISCOURAGED', '.']
        goal_stems = [None, 'RUN', None, 'IS', None, 'DISCOURAG', None]
        self.assertListEqual(gened_text.word_list, goal_words, self.seed_msg)
        self.assertListEqual(gened_text.stem_list, goal_stems, self.seed_msg)
        self.assertListEqual(gened_text.upper_word_list, goal_uppers, self.seed_msg)
    
    def test_basic_anti_stemming(self):
        """Test the basic anti_stemming functionality. Given a small set of 
        possible stems, make sure that it generates the right ones
        """
        num_rows = 1000
        f = StringIO("Running is trusted")
        gen = TextGenerator((f,))
        observed_words = {'RUNNING': 0, 'IS': 0, 'TRUSTED':0}
        observed_stems = {'RUN' : 0, 'TRUST' : 0}
        for _ in xrange(num_rows):
            (stem, generated) = gen.generate_antistem(7,0,1)
            self.assertIn(generated, observed_words)
            self.assertIn(stem, observed_stems)
            observed_words[generated] += 1
            observed_stems[stem] += 1
        
        
        # Note: becuase of the way we weight words based on sentence position,
        # we exepct a 2-to-1 ratio between 'run' and 'trust' 
        self.assertLess(observed_words['RUNNING'], num_rows * 0.7, observed_words)
        self.assertGreater(observed_words['RUNNING'], num_rows * 0.3, observed_words)
        self.assertLess(observed_words['TRUSTED'], num_rows * 0.7, observed_words)
        self.assertGreater(observed_words['TRUSTED'], num_rows * 0.3, observed_words)
        self.assertLess(observed_stems['RUN'], num_rows * 0.7, observed_stems)
        self.assertGreater(observed_stems['RUN'], num_rows * 0.3, observed_stems)
        self.assertLess(observed_stems['TRUST'], num_rows * 0.7, observed_stems)
        self.assertGreater(observed_stems['TRUST'], num_rows * 0.3, observed_stems)
        self.assertEqual(observed_words['IS'],0)
                
    def test_basic_stem_generation(self):
        """Stem Generation: Given a small sample of text that can
        only generate a single stem, check to make sure that is what
        we get and associated cardinality functions work"""
        f = StringIO("Runs running run")
        gen = TextGenerator((f,))
        observed = {'RUN': 0 }
        for _ in xrange(100):
            generated = gen.generate_stem(3,0,1)
            observed[generated]+=1
            
        self.assertEqual(observed['RUN'], 100, self.seed_msg)        
 
    def test_corner_stem_generation(self):
        """Given a standard input, see corner case behavior on stem
        generation given a len not previously seen"""
        f = StringIO('Runs, running, run')
        gen = TextGenerator((f,))
        self.assertRaises(KeyError, gen.generate_stem,0,0,1)
        self.assertRaises(KeyError, gen.generate_stem,-1,0,1) 
        
    def test_basic_stem_cardinality(self):
        """Stem Cardinality: Given a small sample of text that has a few
        stems of different lengths, check to make sure that is what
        we get and associated cardinality functions work"""
        f = StringIO("Yoda run is")
        gen = TextGenerator((f,))
        self.assertEqual(gen.stem_cardinality(), 3, self.seed_msg)
        self.assertEqual(gen.stem_cardinality(1), 0, self.seed_msg)
        self.assertEqual(gen.stem_cardinality(2), 1, self.seed_msg)
        self.assertEqual(gen.stem_cardinality(3), 1, self.seed_msg)    
        self.assertEqual(gen.stem_cardinality(4), 1, self.seed_msg) 
        
    def test_corner_word_generation(self):
        """Given a standard input, see corner case behavior on word
        generation given a len not previously seen"""
        f = StringIO('Runs, running, run')
        gen = TextGenerator((f,))
        self.assertRaises(KeyError, gen.generate_word,0,0,1)
        self.assertRaises(KeyError, gen.generate_word,-1,0,1)   
                
    def test_basic_word_generation(self):
        """Word Generation: Given a small sample of text that can only
        generate a small set of words, check to make sure that we have
        the right distributions"""
        f = StringIO('This is it. This was it.')
        gen = TextGenerator((f,))
        observed = {'THIS': 0, 'IS': 0, 'IT': 0, 'WAS': 0}
        
        for _ in xrange(600):
            value = gen.generate_word(2,0,1)
            observed[value]+=1
            value = gen.generate_word(3,0,1)
            observed[value]+=1
            value = gen.generate_word(4,0,1)
            observed[value]+=1
        
        print observed
        self.assertGreater(observed['IS'], 250, self.seed_msg)
        self.assertLess(observed['IS'], 350, self.seed_msg)
        self.assertGreater(observed['IT'], 250, self.seed_msg)
        self.assertLess(observed['IT'], 350, self.seed_msg)
        self.assertEqual(observed['THIS'], 600, self.seed_msg)
        self.assertEqual(observed['WAS'],600,self.seed_msg)
        
    def test_basic_word_cardinality(self):
        """Word Cardinality: Given a small sample of text that has a few
        wordss of different lengths, check to make sure that is what
        we get and associated cardinality functions work"""
        f = StringIO("Yoda run is")
        gen = TextGenerator((f,))
        self.assertEqual(gen.word_cardinality(), 3, self.seed_msg)
        self.assertEqual(gen.word_cardinality(1), 0, self.seed_msg)
        self.assertEqual(gen.word_cardinality(2), 1, self.seed_msg)
        self.assertEqual(gen.word_cardinality(3), 1, self.seed_msg)    
        self.assertEqual(gen.word_cardinality(4), 1, self.seed_msg)

