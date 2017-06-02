# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Simple wrapper, in case we want to switch
#                      the RNG
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Nov 2011   omd            Original Version
#  27 Sept 2021  jch            Set to stdlib random
#  05 Def  2012  sy             Added gauss and sample, changed seed
# 16 Jun 2013    jch            replaced stdlib.random with numpy
# *****************************************************************

import numpy.random
import copy

shuffle = numpy.random.shuffle
seed = numpy.random.seed
bytes = numpy.random.bytes
triangle = numpy.random.triangular
rand = numpy.random.rand
random = numpy.random.random

randint = numpy.random.random_integers

def choice(seq): 
    if not seq:
        raise IndexError
    else:
        x = randint(0, len(seq)-1)
        return seq[x]

def gauss(mu, sigma):
    z = numpy.random.standard_normal()
    return (z * sigma) + mu


def sample(population, k):
    pop_size = len(population)
    indicies = range(pop_size)
    numpy.random.shuffle(indicies)
    selected_indicies = indicies[0:k]
    return [population[i] for i in selected_indicies]

def randbit():
    return choice([0,1])

