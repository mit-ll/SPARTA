# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        The code that handles the generation of the correntness
#                      section of the final report
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  29 Jul 2013   SY             Original Version
# *****************************************************************

# general imports:
from __future__ import division
import logging
import copy

# LOGGER:
LOGGER = logging.getLogger(__name__)

class CorrectnessGetter(object):
    """This is the superclass of all correctness computers.
    The classes subclassing CorrectnessGetter return the correctness metrics
    (precision and recall) for various functionalities tested.
    
    Attributes:
        results_db: A results database object.
        constraint_list: a list of tuples of the form (table, field, value),
            where query values are returned only if table.field=value for
            all of the tuples.
        num_truepos: the number of true positives
        num_falsepos: the number of false positives
        num_falseneg: the numger of false negatives
        num_correct: the number of correct items
        count: the number of items
    """

    def __init__(self, results_db=None, constraint_list=None):
        """Initializes the CorrectnessGetter with a results database and a
        where clause."""
        self.results_db = results_db
        self.constraint_list = constraint_list
        # keep running counters of the following:
        self.num_truepos = 0 # number of true positives
        self.num_falsepos = 0 # number of false negatives
        self.num_falseneg = 0 # number of false positives
        self.num_correct = 0 # number of correct queries
        self.count = 0 # the number of queries considered

    def get_count(self):
        """Returns the number of executions of the functionality under
        consideration"""
        return self.count

    def get_precision(self):
        """Returns the precision for the functionality in question."""
        if not (self.num_truepos + self.num_falsepos):
            return 1
        return round(self.num_truepos /
                     (self.num_truepos + self.num_falsepos), 3)

    def get_recall(self):
        """Returns the recall for the functionality in question."""
        if not (self.num_truepos + self.num_falseneg):
            return 1
        return round(self.num_truepos /
                     (self.num_truepos + self.num_falseneg), 3)

    def is_perfect(self):
        """Returns True if correctness is perfect, and False otherwise."""
        return self.get_num_correct() == self.get_count()

    def get_num_correct(self):
        """Returns True if some queries were correct, and False otherwise"""
        return self.num_correct

    def __add__(self, other):
        """Adds the two correctness getters.
        Note that the resulting object will NOT have an associated constraint
        list or results db."""
        assert type(other) == type(self)
        attrs = ['num_truepos', 'num_falsepos', 'num_falseneg', 'num_correct',
                 'count']
        new_correctness_getter = copy.copy(self)
        new_correctness_getter.constraint_list = None
        new_correctness_getter.results_db = None
        for attr in attrs:
            new_val = getattr(self, attr) + getattr(other, attr)
            setattr(new_correctness_getter, attr, new_val)
        return new_correctness_getter
