# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Simple wrapper, in case we want to switch
#                      the stemmer
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
# 30 May 2013    JCH            Orignal file, using snowballstemmer
# 12 Aug 2013    JCH            moved to porter stemmer
# *****************************************************************

import spar_python.external.porterstemmer.stemmer as stemmer

stemmer_instance = stemmer.PorterStemmer()


def stem_word(word):
    return stemmer_instance.stem(word, 0, len(word)-1)