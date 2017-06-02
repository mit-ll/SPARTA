# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        A wrapper around a TextGenerator to provide an alternate
#                      semantics for generate()
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Sept 2012  jch            Original Version
# *****************************************************************


import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import collections
import re
import logging

from spar_python.common.distributions.text_generator \
    import TextGenerator
import spar_python.common.spar_random as spar_random
import text_generator
import spar_python.common.distributions.base_distributions as base_distributions
from spar_python.common.enum import Enum


LOGGER = logging.getLogger(__name__)

ALARMWORDFILE = os.path.join(this_dir, 'alarm_words.txt')

ALARMWORDSPEC = Enum('NO_ALARMWORDS', 'ONE_ALARMWORD', "TWO_ALARMWORDS")

#The weight of the various alarm words out of 10
SPEC_WEIGHT = {ALARMWORDSPEC.NO_ALARMWORDS : 8,
               ALARMWORDSPEC.ONE_ALARMWORD : 1,
               ALARMWORDSPEC.TWO_ALARMWORDS : 1}

def word_weight():
    '''
    Returns a weight for a word somewhere between 1 and
    100
    '''
    weights = [1, 1, 1, 1, 1, 1, 1, 10, 10, 100]
    return spar_random.choice(weights)

# It is important that all of these named-tuples provide a 'spec_type' field
NoWordSpec = collections.namedtuple('NoWordSpec', ['spec_type'])
OneWordSpec = collections.namedtuple('OneWordSpec', ['spec_type', 
                                                   'alarmword'])
TwoWordSpec = collections.namedtuple('TwoWordSpec', ['spec_type', 
                                                   'first_alarmword',
                                                   'second_alarmword',
                                                   'distance'])


class AlarmWordsDistribution(object):
    """
    This distribution encapsulates the random distribution by which a 
    TextDistribution object will generate a GeneratedText object containing 
    alarm-words. Each call to AlarmWordsDistribution.generate() will return
    one of three things:
    
    * a NoWordSpec, which is interpreted as meaning 'no alarmwords',

    * a OneWordSpec, which is interpreted as 'put the alarm word alarmword in
    the generated text', and
        
    * a TwoWordSpec, which is interpreted as 'insert the two alarmwords into the
    generated text with at most max_distance characters between the end of the
    first alarm-word and the beginning of the second.'
        
    Note: internally, this class has been written to allow the most natural
    kind of tweaking, but future developers should depend only on the API 
    described above and not any particular feature of the internal 
    implementation.
    """
    
    def __init__(self):
        """
        Define a mapping from alarmwords to alarmwords, and three 
        sub-distributions:
        
        * spec_dist returns an element of ALARMWORDSPEC according to some
        distribution,

        * alarm_dist returns a random alarmword.
        
        * dist_dist takes in two alarmwords and returns a max-distance. (Currently,
        this distribution's output is actually independent of the input, but
        we want to allow future modifications which make the distance between
        two alarmwords dependent on the alarmwords.)
        """
        
        self.spec_dist = base_distributions.SimpleIndependentDistribution()
        for (spec, weight) in SPEC_WEIGHT.iteritems():
            self.spec_dist.add(spec, weight)


        # Now, build up the lexicon of alarmwords and relevant structures        
        self.alarmwords = []
        with open(ALARMWORDFILE, 'r') as alarm_word_file: 
            word_regexp = re.compile("^[a-zA-Z]+$")
            for line in alarm_word_file:
                word = line.rstrip() 
                # check that the line contains a single word
                match_obj = word_regexp.match(word)
                if match_obj:
                    self.alarmwords.append(word)
                else:
                    LOGGER.warning("Skipping non-word in alarm_words.txt: %s", 
                                   word)
        
        self.next_alarmword_mapping = {}
        self.alarm_dist = base_distributions.SimpleIndependentDistribution()
        
        # Update alarm_dist
        for word in self.alarmwords:
            self.alarm_dist.add(word, weight=word_weight())

        # Make next_alarmword_mapping
        word_pairs = [tuple(self.alarmwords[i:i+2]) 
                      for i in range(0, len(self.alarmwords), 2)]
        for word_pair in word_pairs:
            try:
                (first_word, second_word) = word_pair
            except ValueError:
                # Some tuple had less than two words, probably because
                # self.alarmwords had an odd number of words
                continue
            self.next_alarmword_mapping[first_word] = second_word
            self.next_alarmword_mapping[second_word] = first_word
             

        # Now, the 'distance' distribution.
        self.dist_dist = base_distributions.SimpleIndependentDistribution()
        # Note: these distances should be kept well below 100, as 
        # notes3 values might only be 100 characters max.
        self.dist_dist.add(25, weight = 1)
        self.dist_dist.add(50, weight = 1)
        self.dist_dist.add(100, weight = 1)
        
        
        
    def generate(self, *args, **kwargs):
        #
        # The basic design:
        #
        # Call spec_dist to determine if we add alarmwords.
        #
        # If so, call alarm_dist to get the first alarmword.
        # 
        # If spec_dist specified 2 alarmwords, use the map to get the second
        # alarmword and use dist_dist to get the distance.
        
        alarmword_spec = self.spec_dist.generate()
        
        if alarmword_spec == ALARMWORDSPEC.NO_ALARMWORDS:
            return NoWordSpec(alarmword_spec)
        else:
            alarmword = self.alarm_dist.generate()
            if alarmword_spec == ALARMWORDSPEC.ONE_ALARMWORD:
                return OneWordSpec(alarmword_spec, alarmword)
            else:
                assert alarmword_spec == ALARMWORDSPEC.TWO_ALARMWORDS
                second_alarmword = self.next_alarmword_mapping[alarmword]
                ind_vars = {'first_word' : alarmword,
                            'second_word' : second_alarmword}
                
                distance = self.dist_dist.generate(ind_vars)
                return TwoWordSpec(alarmword_spec, alarmword, 
                                   second_alarmword, distance)
    
    def generate_pdf(self, minim, maxim):
        '''
        Generates an alarm word pair as a tuple 
        '''
        first_word = self.alarm_dist.generate_pdf(minim, maxim)
        second_word = self.next_alarmword_mapping[first_word]
        return (first_word, second_word)


class TextDistribution(object):
    """
    Generates random english text with a length likely to be between
    user-given bounds. More specifically, will return a GeneratedText object.
    If the user requests (via an argument to the constructor) then this 
    GeneratedText object will contain alarm words with a probability goverened
    by an AlarmWordDistribution object.
    
    This class is a simple wrapper around a TextGenerator object, re-defining
    the meaning of generate(). In TextGenerator, generate() takes a manditory
    length argument. This class takes a max-length and a min-length argument at
    initialization, and then calls the generate() method of a TextGenerator
    instance with a randomly-chosen length argument between the max and min.
    Thus, this class provides a clean generate() method which can be used by
    DataGeneratorEngine.

    At the time of this writing, there is no guarantee that the returned string
    will be longer than the min-length, but it will almost always be the case so
    long as min-length and max-length are sufficiently far apart. We intend to
    include this guarantee in a future release.



    """

    def __init__(self, text_generator, min_length, max_length, 
                 add_alarmwords = False):
        self.__generator = text_generator
        self.__min_length = min_length
        self.__max_length = max_length
        self._add_alarmwords = add_alarmwords 
        if self._add_alarmwords:
            self._alarmword_dist = AlarmWordsDistribution()


    def generate(self, *args):
        """
        Returns a randomly-generated string from the underlying
        TextGenerator close in length to a randomly-chosen target
        between min-length and max-length. Note that the string
        returned is guaranteed not to end in the middle of a word, but
        not necessarily at the end of a sentence. Also, the returned
        string *may* be less than min_length, and (if add_alarmwords 
        was set to True in the constructor) may contain one or two 
        alarmwords.
        """
        
        target = spar_random.randint(self.__min_length,
                                     self.__max_length)
        
        if not self._add_alarmwords:
            # No alarmwords. Proceed normally.
            return self.__generator.generate(target)
        else:
            # Maybe add alarmwords. Check to see:
            alarmword_spec = self._alarmword_dist.generate()
            alarmword_spec_type = alarmword_spec.spec_type
            
            if alarmword_spec_type == ALARMWORDSPEC.NO_ALARMWORDS:
                # No alarmwords. Proceed normally.
                return self.__generator.generate(target)
            
            elif alarmword_spec_type == ALARMWORDSPEC.ONE_ALARMWORD:
                alarmword = alarmword_spec.alarmword
                alarmword_length = len(alarmword)
                
                # The extea '2' are for the spaces on either side of the
                # alarmword
                new_target = target - alarmword_length - 2
                
                generated_text = self.__generator.generate(new_target)

                generated_text.add_single_alarmword(alarmword)
                
                return generated_text
            
            else:
                assert alarmword_spec_type == ALARMWORDSPEC.TWO_ALARMWORDS
                
                first_alarmword = alarmword_spec.first_alarmword
                second_alarmword = alarmword_spec.second_alarmword
                
                combined_lengths = sum([len(first_alarmword),
                                        len(second_alarmword)])
                
                # the +4 is for the spaces on either side of the alarmwords
                # this always needs to remain true for the baseline to correctly
                # parse the alarm words. 
                new_target = target - (combined_lengths + 4)
                
                generated_text = self.__generator.generate(new_target)

                distance = alarmword_spec.distance

                generated_text.add_two_alarmwords(first_alarmword,
                                                  second_alarmword,
                                                  distance)
                
                
                return generated_text

    
    
    
    
    def generate_trigram(self, min=0.0, maxim=1.0):
        """
        Wrapper function for generate_trigram in text_generator
        """
        return self.__generator.generate_trigram(min, maxim) 
    
    def trigram_cardinality(self):
        """
        Wrapper function for the trigram_cardinality function
        """
        return self.__generator.trigram_cardinality()
    
    def generate_word(self, len, min=0.0, maxim=1.0):
        """
        Wrapper function for generate_word function in text_generator
        """
        return self.__generator.generate_word(len, min, maxim)
    
    def generate_stem(self, len, min=0.0, maxim=1.0):
        """
        Wrapper function for generate_stem function in text_generator
        """
        return self.__generator.generate_stem(len, min, maxim)
    def generate_antistem(self, len, min=0.0, maxim=1.0):
        '''
        Wrapper function for generate_stem function in text_generator
        '''
        return self.__generator.generate_antistem(len, min, maxim)
    def generate_alarmword(self, minim, maxim):
        '''
        Wrapper function for generate_pdf in alarmword distribution
        '''
        return self._alarmword_dist.generate_pdf(minim, maxim)
    @staticmethod  
    def to_string(generate_output):        
        '''    
        This takes the output of generate() and converts it to a string ready to
        print to a line-raw or csv file. Remember, this is a list of
        (word,stem) pairs where stem is None when word is space, punctuation, 
        etc. So, this operation boils down to joining a long list of strings.
        '''
        return text_generator.TextGenerator.to_string(generate_output)

    def alarmwords_enabled(self):
        """
        Returns True iff this distribution object has the alarmword-addition
        mechanism enabled.
        """
        return self._add_alarmwords

    def alarmwords(self):
        """
        Returns list of possible alarmwords. If alarmwords are not enabled,
        will return empty list.
        """
        if self._add_alarmwords:
            return self._alarmword_dist.alarmwords
        else:
            return []


