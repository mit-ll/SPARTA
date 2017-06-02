# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        The class that handles the computation of the correntness
#                      information
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Oct 2013   SY             Original Version
# *****************************************************************

# general imports:
from __future__ import division
import logging
import copy

# SPAR imports:
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.correctness_getter as correctness_getter

# LOGGER:
LOGGER = logging.getLogger(__name__)
    
class CircuitCorrectnessGetter(correctness_getter.CorrectnessGetter):
    """This class computes the correctness metrics (precision and recall) for
    the circuit evaluation process.
    
    Additional Attributes:
        num_failed: the number of circuit evaluations with FAILED messages
    """
    def __init__(self, results_db=None, constraint_list=None):
        """Initializes the CircuitCorrectnessGetter with a results database and
        a constraint list.

        All of the computation is done at initialization."""
        super(CircuitCorrectnessGetter, self).__init__(results_db,
                                                       constraint_list)
        self.num_failed = 0 # number of failed queries
        # we do not think in terms of 'positives' and 'negatives' for evaluation
        # correctness, so attempting to do any arithmetic (addition, etc) with
        # the counters will throw an error:
        self.num_truepos = None
        self.num_falsepos = None
        self.num_falseneg = None
        self.populate()

    def __add__(self, other):
        new_correctness_getter = super(
            CircuitCorrectnessGetter, self).__add__(other)
        attrs = ["num_failed"]
        for attr in attrs:
            new_val = getattr(self, attr) + getattr(other, attr)
            setattr(new_correctness_getter, attr, new_val)
        return new_correctness_getter

    def populate(self):
        """
        Args:
            update_db: A boolean value

        Populates the _num_truepos, _num_falsepos, _num_falseneg, and other
        values.
        If update_db is True, updates the results database with correctness
        information.
        """
        if self.results_db == None:
            return
        # retrieve lists of query values:
        fields = [(t2s.PEREVALUATION_TABLENAME, "ROWID"),
                  (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_OUTPUT),
                  (t2s.INPUT_TABLENAME, t2s.INPUT_CORRECTOUTPUT),
                  (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_STATUS),
                  (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_CORRECTNESS)]
        [evaluation_ids,
         evaluation_outputs, # the outputs of the evaluations
         evaluation_groundtruths, # the correct evaluation results
         statuses, # failed messages
         correctnesses, # contains a boolean indicating evaluation correctness
         ] = self.results_db.get_values(
             fields, constraint_list=self.constraint_list)
        num_evaluations = len(evaluation_ids)
        val_lists_and_names = [
            (evaluation_outputs, "evaluation outputs"),
            (evaluation_groundtruths, "evaluation ground truth"),
            (statuses, "failed messages"),
            (correctnesses, "correctness booleans")]
        for (val_list, name) in val_lists_and_names:
            assert len(val_list) == num_evaluations, ("wrong number of %s"
                                                      % name)
        # iterate through all of the relevent evaluations, incrementing the
        # running counters as we go:
        for (evaluation_id, evaluation_output, evaluation_groundtruth,
             status, stored_is_correct) in zip(
                 evaluation_ids, evaluation_outputs, evaluation_groundtruths,
                 statuses, correctnesses):
            if status:
                self.num_failed += 1
                # if the query failed, continue on to the next query - do not
                # execute the rest of the analysis
                continue
            self.count += 1
            if evaluation_groundtruth == evaluation_output:
                self.num_correct += 1

    def get_num_failed(self):
        """Returns the number of failed queries."""
        return self.num_failed

    def get_evaluation_accuracy(self):
        """Returns the evaluation_accuracy."""
        if not self.count:
            return 1
        return float(self.num_correct) / float(self.count)
