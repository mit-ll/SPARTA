# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        TextGenerator class
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Nov 2011   omd            Original Version
# *****************************************************************

#import os
#import sys
#this_dir = os.path.dirname(os.path.abspath(__file__))
#base_dir = os.path.join(this_dir, '..', '..')
#sys.path.append(base_dir)


from spar_python.common.distributions.base_distributions\
     import SimpleIndependentDistribution
from spar_python.common.distributions.base_distributions\
     import CompactIndependentDistribution
from spar_python.data_generation.file_iterators\
     import FileTokenIterator
from spar_python.common.distributions.generated_text import GeneratedText
from cStringIO import StringIO
import spar_python.common.spar_stemming as spar_stemming


# This C-struct will store, for every word, whetehr it is a start-token and
# how long it is. This saves us from needing to re-calculate these during
# text-generation.
cdef struct TokenMetadata:
    bint is_start_token
    int length


cdef class TextGenerator(object):
    """
    Generates random text that looks like valid English. More specifically, will
    return a *list* of pairs, where each pair is either:
    
    * a (word, stem) pair, where both `word` and `stem` are strings, `word` is
    an English word and `stem` is the stem of `word`, or
    
    * a (non-word, None) pair where `non_word` is a string holding some non-word
    text (space, punctuation, etc).

    To use, initialize one of these objects with an array of files containing
    example text. Files from Project Guttenberg, for example, make a great
    training set. The class then learns a simple model of bigram distributions
    and the distribution of words that follow any bigram. It also stems every
    word seen, and maintains a word->stem mapping.
    
    Sentence generation begins with the generation of a bigram. This bigram will
    follow the distribution of bigrams that begin sentences in the training
    corpus. Once we have a bigram we look at the distribution of words that
    follow that bigram and generate a new word according to that distribution.
    We now have a new bigram (the last word from the previous one plus the newly
    generated word) so we repeat the procedure. Each time a word is generated,
    its stem is retrieved from the mapping to include in the (word, stem) pair.

    This holds true until the last three words in the sentence, which are 
    generated from the same distribution as the starting bigram. A third
    word is then chosen using that starting bigram to make up the last 
    three words within the sentence. These are appended with a starting space
    to the end of the last sentence along with a final period. This creates 
    several generation cases in which there will be a sentence that starts
    with a leading space (in the case where the sentence is comprised of only
    enough characters for three words) or double space (if the last thing 
    appended to the sentence is a space). This is reflected in the unit
    tests for text_generation. 
    
    Sample use:

    gen = TextGenerator((file1, file2, file3))
    almost_1000_bytes_of_random_text = gen.generate(1000)
    
    """
    
    # This next line tells cython that the following names have the type 
    # 'python object'
    cdef object __tuple_dist, __tuple_to_word_dist, __stem_upper_mapping
    cdef object __metadata, __stem_to_word
    cdef object __word_dist, __stem_dist, __tri_card
    
    # These tokens indicate the start of a sentence.
    START_TOKENS = set(['.', '!', '?', ';', ',', '-'])

    
    def __init__(self, corpus_files):
        """Constructor for the TextGenerator.

        Args:
            corpus_files: An iterable containing open file-like objects that
            should be read to determine the proper word distributions for
            generating text.
        """
        # Distribution of the tuples themselves. This is only really need to
        # start a new string of text as after that everything flows from the
        # distribution of words that follow tuples.
        self.__tuple_dist = SimpleIndependentDistribution()
        # Map from tuple to distribution of words following that tuple.
        self.__tuple_to_word_dist = {}
        self.__stem_upper_mapping = {}
        # distribution of words and stems seen in training corpus
        self.__word_dist = {}
        self.__stem_dist = {}
        # will map words to TokenMetadata structs.
        self.__metadata = {}
        self.__stem_to_word = {}
        self.__tri_card = None
        self.__process_files(corpus_files)


    def __process_files(self, corpus_files):
        for f in corpus_files:
            self.__process_file(f)
        # Make sure we have at least 1 starting place.
        assert(self.__tuple_dist.size() > 0)

    def __process_file(self, corpus_file):
        """Process corpus_file discovering the appropriate distributions."""
        cdef TokenMetadata metadata
        
        tokens_found = 0
        # We only consider starting a text generation step with tuples that
        # begin a sentence. This is the number of tokens we've put in cur_tuple
        # since a sentence start.
        since_sentence_start = 0
        
        # start with a tuple of TUPLE_SIZE empty strings
        cur_tuple = ('','')
        for tok in FileTokenIterator(corpus_file):
            
            if tok in self.START_TOKENS:
                metadata.is_start_token = True
            else:
                metadata.is_start_token = False
            metadata.length = len(tok)
            self.__metadata[tok] = metadata
            
            tokens_found += 1
            if tokens_found > 2:
                if not cur_tuple in self.__tuple_to_word_dist:
                    self.__tuple_to_word_dist[cur_tuple] = \
                        SimpleIndependentDistribution()
                self.__tuple_to_word_dist[cur_tuple].add(tok)


            # Now create a new tuple by shifting the current tuple left
            # removing any exisiting items and adding the new token.
            cur_tuple = cur_tuple[1:] + (tok,)

            if tok in self.START_TOKENS:
                since_sentence_start = 0
            else:
                since_sentence_start += 1

            if since_sentence_start == 2:
                # Do not add sentence-starting tuples which themselves
                # start with a start-token
                if cur_tuple[0] not in self.START_TOKENS:
                    self.__tuple_dist.add(cur_tuple)
                
            
            # Lastly, update the word -> stem mapping on tok, unless tok is
            # punctuation
            tok_length = len(tok)
            weight = int(round(10000 / (since_sentence_start + 1)))
            if tok not in self.START_TOKENS:
                if tok not in self.__stem_upper_mapping:
                    ## NOTE that the stemmer stems all caps differently than all 
                    ## lowercase, thus the word that is stemmed cannot be in uppercase
                    tok_lowercase = tok.lower()
                    tok_uppercase = tok.upper()
                    stem = spar_stemming.stem_word(tok_lowercase).upper()
                    self.__stem_upper_mapping[tok] = (stem, tok_uppercase)
                    self.__stem_to_word[stem] = tok_uppercase
                    try: 
                        self.__stem_dist[tok_length].add(stem, weight)
                    except KeyError:
                        self.__stem_dist[tok_length] = CompactIndependentDistribution() 
                        self.__stem_dist[tok_length].add(stem, weight)
            try: 
                self.__word_dist[tok_length].add(tok.upper(), weight)
            except KeyError:
                self.__word_dist[tok_length] = CompactIndependentDistribution() 
                self.__word_dist[tok_length].add(tok.upper(), weight)
                    

    # Developer's note: both of the following methods, __add_start_token
    # and __add_word, used to be combined into one method: __add_word, which
    # would immediately branch on whether or not the input was a start token. 
    # But it turns out that calling code always knew, already, whether the
    # 'word' in question was a start token or not. So, for optimization
    # reasons, it maked sense to split __add_work into a (real) __add_word
    # and __add_start_token and eliminate an unneeded test.

    # (Note: the 'except -1' at the end allows this C function to raise
    # exceptions by returning -1)

    cdef int __add_start_token(self, 
                               object start_token, 
                               object word_list,
                               object stem_list,
                               object upper_list,
                               int prev_chars_generated, 
                               int max_characters) except -1:
        """
        Add start-token to the existing (word,stem)-pair list. 
        
        Args:
            start_token: The token to add to the buffer.
            word_list: The word list to which we should add
                            the start token.
            stem_list: The list of stems corresponding to word_list.
            upper_list: The list of uppercase-strings corresponding to word_list.
            prev_chars_generated: the number of characters already in
                                  word_stem_list
            max_characters: the maximum number of characters that can be in 
                            word_stem_list
            
            
        Returns:
            The number of characters in word_stem_list after addition.
            
        Raises:
            StopIteration, if adding word would raise word_stem_list over
            max_characters

        """
        cdef int new_length 
        # No spaces before a punctuation character.
        new_length = prev_chars_generated + 1 
        if new_length > max_characters:
            raise StopIteration
        word_list.append(start_token)
        stem_list.append(None)
        upper_list.append(start_token)
        return new_length


    # (Note: the 'except -1' at the end allows this C function to raise
    # exceptions by returning -1)
    cdef int __add_word(self, 
                        object word, 
                        object stem,
                        object upper,
                        int word_length,
                        object word_list, 
                        object stem_list, 
                        object upper_list, 
                        int prev_chars_generated, 
                        int max_characters) except -1:
        """
        Add word to the existing (word,stem)-pair list. Do not call when
        'word' is a start-token. Use __add_start_token instead.
        
        Args:
            word: The word to add to the buffer.
            word_list: The word list to which we should add
                            the start token.
            stem_list: The list of stems corresponding to word_list.
            upper_list: The list of uppercase-strings corresponding to word_list.
            prev_chars_generated: the number of characters already in
                                  word_stem_list
            max_characters: the maximum number of characters that can be in 
                            word_stem_list
            
            
        Returns:
            The number of characters in word_stem_list after addition.
            
        Raises:
            StopIteration, if adding word would raise word_stem_list over
            max_characters

        """
        cdef int new_length
        
        new_length = prev_chars_generated + 1
        if new_length > max_characters:
            raise StopIteration
        word_list.append(' ')
        stem_list.append(None)
        upper_list.append(' ')
        new_length += word_length
        if new_length > max_characters:
            raise StopIteration
        word_list.append(word)
        stem_list.append(stem)
        upper_list.append(upper)
        return new_length


    def generate(self, int max_characters):
        """
        Generate text (that follows the expected distribution) of length <=
        max_characters.
        
        Args:
            max_characters: cap on the number of characters to generate.

        Returns:
            A triple of lists:
            * A list of words,
            * A list of stems, and
            * A list of upper-case words.
            
            For all i, it will be the case that stem[i] is the stem of
            word[i], and upper[i] will be word[i].upper().
        
        """
        
        # Developer notes: this function turns out to be the bottleneck in data-
        # generation, taking (before optimization) 94% of the running time.
        # Generating any given word is easy, but a full run generates 180
        # billion words. So, it poys to optmize the heck out of this method. The
        # following code is pretty darn hard to read, but is the result of
        # focused optimization (where profiling has been used to verify the
        # effectiveness of each optimization).
        
        
        cdef int characters_generated 
        cdef TokenMetadata first_word_metadata, second_word_metadata, word_metadata
        
        assert(max_characters > 0)

        generated_words = []
        generated_stems = []
        generated_uppers = []

        # According to http://wiki.python.org/moin/PythonSpeed/PerformanceTips
        # it takes time to resolve the '.' operation in 'self.anything',
        # and that we might try speeding things up by factoring
        # out such function look-ups:
        __metadata = self.__metadata
        __tuple_dist_generate = self.__tuple_dist.generate
        __stem_upper_mapping = self.__stem_upper_mapping
        __tuple_to_word_dist = self.__tuple_to_word_dist


        # Select and add the first bi-gram. Note: special logic so we can
        # remove the extraneous space at the beginning of the list.
        characters_generated = 0

        # Generate the last three words of the sentence from a known 
        # distribution, then add those values to characters_generated
        last_three_words = []
        cur_tuple = __tuple_dist_generate()
        (third_last_word, second_last_word) = cur_tuple
        last_word = self.__tuple_to_word_dist[(third_last_word,second_last_word)].generate()
        (third_last_stem, third_last_upper) = __stem_upper_mapping[third_last_word]
        (second_last_stem, second_last_upper) = __stem_upper_mapping[second_last_word]
        try:
            (last_stem, last_upper) = __stem_upper_mapping[last_word]
        except KeyError:
            last_stem = None
            last_upper = last_word.upper()
        characters_generated += len(third_last_word) + len(second_last_word) + \
                                len(last_word) + 4
                        
        # Exception handling is fast, so we are actually going to use that
        # to escape the following loop when we've generated enough words

        try:
            
            cur_tuple = __tuple_dist_generate()
            (first_word, second_word) = cur_tuple
            # Note: assuming that sentence-starting bi-grams don't start with 
            # a sentence-ending token. This should be enforced in _process_file,
            # above
            first_word_metadata = __metadata[first_word]
            (first_stem, first_upper) = __stem_upper_mapping[first_word]
            characters_generated = self.__add_word(first_word,
                                              first_stem,
                                              first_upper,
                                              first_word_metadata.length, 
                                              generated_words,
                                              generated_stems,
                                              generated_uppers,
                                              characters_generated,
                                              max_characters)
                
            # At this point, __add_word should have added an initial space.
            # Let's remove it.
            generated_words.pop(0)
            generated_stems.pop(0)
            generated_uppers.pop(0)
            characters_generated -= 1
            
            # Now, add the second word as usual.
            second_word_metadata = __metadata[second_word]
            if second_word_metadata.is_start_token:
                last_token_was_sentence = True
                characters_generated = self.__add_start_token(second_word, 
                                                         generated_words,
                                                         generated_stems,
                                                         generated_uppers,
                                                         characters_generated,
                                                         max_characters)
            else:
                last_token_was_sentence = False
                (second_stem, second_upper) = __stem_upper_mapping[second_word]
                characters_generated = self.__add_word(second_word,
                                                  second_stem,
                                                  second_upper,
                                                  second_word_metadata.length, 
                                                  generated_words,
                                                  generated_stems,
                                                  generated_uppers,
                                                  characters_generated,
                                                  max_characters)                    
            
    
    
            # And now, keep adding words until we hit our limit.
        
            # Run until __add_word or __add_start_token raises StopIteration,
            # indicating that we have hit max_characters
            while True:

                if last_token_was_sentence:
                    cur_tuple = __tuple_dist_generate()
                    (first_word, second_word) = cur_tuple
                    # Note: assuming that sentence-starting bi-grams don't start
                    # with a sentence-ending token. This should be enforced in 
                    # _process-file, above.
                    first_word_metadata = __metadata[first_word]
                    (first_stem, first_upper) = __stem_upper_mapping[first_word]
                    characters_generated = \
                        self.__add_word(first_word, 
                                   first_stem,
                                   first_upper,
                                   first_word_metadata.length,     
                                   generated_words,
                                   generated_stems,
                                   generated_uppers,
                                   characters_generated,
                                   max_characters)
                        
                    second_word_metadata = __metadata[second_word]
                    if second_word_metadata.is_start_token:
                        last_token_was_sentence = True
                        characters_generated = \
                            self.__add_start_token(second_word, 
                                              generated_words,
                                              generated_stems,
                                              generated_uppers,
                                              characters_generated,
                                              max_characters)
                    else:
                        last_token_was_sentence = False
                        (second_stem, second_upper) = __stem_upper_mapping[second_word]
                        characters_generated = \
                            self.__add_word(second_word,
                                       second_stem,
                                       second_upper,
                                       second_word_metadata.length, 
                                       generated_words,
                                       generated_stems,
                                       generated_uppers,
                                       characters_generated,
                                       max_characters)                    
                    
                    
                else:
                    try:
                        dist_for_tuple = __tuple_to_word_dist[cur_tuple]
                    except KeyError:
                        last_token_was_sentence = True
                        characters_generated = \
                            self.__add_start_token('.', 
                                              generated_words,
                                              generated_stems,
                                              generated_uppers,
                                              characters_generated,
                                              max_characters)
                    else:
                        word = dist_for_tuple.generate()
                        word_metadata = __metadata[word]
                        if word_metadata.is_start_token:
                            last_token_was_sentence = True
                            characters_generated = \
                                self.__add_start_token(word, 
                                                  generated_words,
                                                  generated_stems,
                                                  generated_uppers,
                                                  characters_generated,
                                                  max_characters)
                        else:
                            last_token_was_sentence = False
                            (stem, upper) = __stem_upper_mapping[word]
                            characters_generated = \
                                self.__add_word(word,
                                           stem,
                                           upper,
                                           word_metadata.length, 
                                           generated_words,
                                           generated_stems,
                                           generated_uppers,
                                           characters_generated,
                                           max_characters)                    
                            # Remove the left-most word from the tuple and 
                            # add the new word.
                            cur_tuple = cur_tuple[1:] + (word,)
                    

        except StopIteration:
            generated_words.append(' ')
            generated_stems.append(None)
            generated_uppers.append(' ')
            
            generated_words.append(third_last_word)
            generated_stems.append(third_last_stem)
            generated_uppers.append(third_last_upper)

            generated_words.append(' ')
            generated_stems.append(None)
            generated_uppers.append(' ')

            generated_words.append(second_last_word)
            generated_stems.append(second_last_stem)
            generated_uppers.append(second_last_upper)

            generated_words.append(' ')
            generated_stems.append(None)
            generated_uppers.append(' ')

            generated_words.append(last_word)
            generated_stems.append(last_stem)
            generated_uppers.append(last_upper)
            
            if last_word!='.':
                generated_words.append('.')
                generated_stems.append(None)
                generated_uppers.append('.')

            return GeneratedText(generated_words, 
                                 generated_stems, 
                                 generated_uppers)
        
    def generate_trigram(self, minim, maxim):
        """
        Generate starting trigram that follow the expected distribution
        
        Args:
            min: miminum pdf value
            max: maximum pdf value
            
        Returns:
            A random trigram.
        """
        (fword, sword) = self.__tuple_dist.generate_pdf(minim, maxim)
        tword = self.__tuple_to_word_dist[(fword,sword)].generate_pdf(minim, maxim)
        return fword + " " + sword + " " + tword
        
    def generate_antistem(self, len, min, maxim):
        """
        Returns the a word that stems to the passed in stem
        """
        stem = self.generate_stem(len, min, maxim)
        return (stem, self.__stem_to_word[stem])
    
    def generate_stem(self, len, min, maxim):
        """
        Generate stem of length len that follow the expected distribution.
        
        Args:
            len: the length of the desired stem, will throw a KeyError
            if the length has not previously been seen
            
        Returns:
            A random stem from the distribution.
        
        """
        
        return self.__stem_dist[len].generate_pdf(min,maxim)
    
    def generate_word(self, len, min, maxim):
        """
        Generate stem of length len that follow the expected distribution.
        
        Args:
            len: the length of the desired word, will throw a KeyError
            if the length has not previously been seen
            
        Returns:
            A random word from the distribution.
        
        """
        return self.__word_dist[len].generate_pdf(min,maxim)
    

    def stem_cardinality(self, len = None):
        """
        Supplies the total count from the underlying stem distribution for 
        length len
        
        Args:
           len: the length of the desired cardinality, will return 0 if
           a not previously seen len, if no len is specified will return 
           the total count for all lens
         
        Returns:
            The total count (weight) for the specified distribution
        """
        
        if len is not None:
            try:
                card = self.__stem_dist[len].size()
            except KeyError:
                card = 0
        else:
            card = 0
            for x in self.__stem_dist.values():
                card += x.size()
        return card
        
    def word_cardinality(self, len = None):
        """
        Supplies the total count from the underlying word distribution for 
        length len
        
        Args:
           len: the length of the desired cardinality, will return 0 if
           a not previously seen len, if no len is specified will return 
           the total count for all lens
         
        Returns:
            The total count (weight) for the specified distribution
        """
        
        if len is not None:
            try:
                card = self.__word_dist[len].size()
            except KeyError:
                card = 0
        else:
            card = 0
            for x in self.__word_dist.values():
                card += x.size()
        return card        
    
    def trigram_cardinality(self):
        '''
        Returns the cardinality of the starting and ending trigrams
        ''' 
        if self.__tri_card is None:
            self.__tri_card = sum(dist.size() for dist in self.__tuple_to_word_dist.values())
        return self.__tri_card
    

