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
import sys

# SPAR imports:
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.common.correctness_getter as correctness_getter

# LOGGER:
LOGGER = logging.getLogger(__name__)
    
class QueryCorrectnessGetter(correctness_getter.CorrectnessGetter):
    """This class computes the correctness metrics (precision and recall) for
    the query process.
    
    Additional Attributes:
        num_badhash: the number of incorrect record hashes for true positives
        num_goodhash: the number of correct record hashes for true positives
        num_bad_rankings: the number of incorrectly ranked P9 queries
        num_rankings: the number of P9 queries
        num_failed: the number of queries with FAILED messages
    """
    def __init__(self, results_db=None, constraint_list=None, update_db=False):
        """Initializes the QueryCorrectnessGetter with a results database and
        a where clause.

        All of the computation is done at initialization."""
        super(QueryCorrectnessGetter, self).__init__(results_db,
                                                     constraint_list)
        # keep running coutners of the following:
        self.num_badhash = 0 # number of bad hashes (for true positives)
        self.num_goodhash = 0 # number of good hashes (for true positives)
        self.num_bad_rankings = 0 # number of bad rankings for P9
        self.num_rankings = 0 # number of P9 queries
        self.num_failed = 0 # number of failed queries
        self.populate(update_db)

    def __add__(self, other):
        new_correctness_getter = super(
            QueryCorrectnessGetter, self).__add__(other)
        attrs = ["num_badhash", "num_goodhash", "num_bad_rankings",
                 "num_rankings", "num_failed"]
        for attr in attrs:
            new_val = getattr(self, attr) + getattr(other, attr)
            setattr(new_correctness_getter, attr, new_val)
        return new_correctness_getter

    def populate(self, update_db):
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
        fields = [(t1s.DBP_TABLENAME, "ROWID"),
                  (t1s.DBP_TABLENAME, t1s.DBP_FQID),
                  (t1s.DBF_TABLENAME, t1s.DBF_CAT),
                  (t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT),
                  (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
                  (t1s.DBF_TABLENAME, t1s.DBF_MATCHINGRECORDIDS),
                  (t1s.DBF_TABLENAME, t1s.DBF_MATCHINGRECORDHASHES),
                  (t1s.DBP_TABLENAME, t1s.DBP_RETURNEDRECORDIDS),
                  (t1s.DBP_TABLENAME, t1s.DBP_RETURNEDRECORDHASHES),
                  (t1s.DBF_TABLENAME, t1s.DBF_P9MATCHINGRECORDCOUNTS),
                  (t1s.DBP_TABLENAME, t1s.DBP_CURRENTPOLICIES),
                  (t1s.DBP_TABLENAME, t1s.DBP_STATUS)]
        [performer_query_ids,
         full_query_ids,
         query_cats, # the query categories
         correctness, # contains a boolean indicating row correctness
         selection_cols, # contains 'id' or '*' for every query
         matching_record_ids, # contains the matching record ids for each query
         matching_record_hashes, # contains the matching record hashes for each
                                 # query
         returned_record_ids, # contains the returned record ids for each query
         returned_record_hashes, # contains the returned record hashes for each
                                 # query
         p9_matching_record_counts, # number of records matching each clause for
                                # p9
         policies, # the policies
         statuses # failed messages
         ] = self.results_db.get_query_values(
             fields, constraint_list=self.constraint_list)
        num_queries = len(performer_query_ids)
        val_lists_and_names = [
            (full_query_ids, "qids"), (query_cats, "query_categories"),
            (correctness, "correctness booleans"),
            (selection_cols, "selection_cols"),
            (matching_record_ids, "matching record id lists"),
            (matching_record_hashes, "matching record hash lists"),
            (returned_record_ids, "returned record id lists"),
            (returned_record_hashes, "returned record hash lists"),
            (p9_matching_record_counts, "p9 matching record counts"),
            (policies, "current policies"),
            (statuses, "failed messages")]
        for (val_list, name) in val_lists_and_names:
            assert len(val_list) == num_queries, "wrong number of %s" % name
        # iterate through all of the relevent queries, incrementing the running
        # counters as we go:
        for (pqid, fqid, cat, stored_is_correct,
             scols, mris, mrhs, rris, rrhs, mrcs, policy, status) in zip(
            performer_query_ids, full_query_ids, query_cats, correctness,
            selection_cols, matching_record_ids, matching_record_hashes,
            returned_record_ids, returned_record_hashes,
            p9_matching_record_counts, policies, statuses):
            if len(mrhs) != len(mris) and (scols == '*'):
                LOGGER.error("Bad ground truth hashes for query %s"
                             % str(fqid))
            if (scols == '*') and (len(rrhs) != len(rris)):
                LOGGER.warning("Wrong number of hashes returned for query %s"
                               % str(fqid))
            if status:
                self.num_failed += 1
                # if the query failed, continue on to the next query - do not
                # execute the rest of the analysis
                continue
            if policy:
                # we do not count queries with policy enforcement for query
                # correctness metrics
                continue
            self.count += 1
            truepos = []
            falsepos = []
            falseneg = []
            badhash = []
            badly_ranked = False
            if not rrhs:
                # for the zip, create dummy returned record hashes:
                rrhs = [None for idx in xrange(len(rris))]
            mrisandhs = zip(mris, mrhs) # so as not to rezip many times
            for (rri, rrh) in zip(rris, rrhs):
                if rri in mris:
                    truepos.append(rri)
                    # hashes are only checked for true positives:
                    if scols == '*':
                        if (rri, rrh) not in mrisandhs:
                            badhash.append(rri)
                else:
                    falsepos.append(rri)
            for mri in mris:
                if mri not in truepos:
                    falseneg.append(mri)
            # ranking correctness:
            if cat == t1s.CATEGORIES.to_string(t1s.CATEGORIES.P9):
                if sum(mrcs) != len(mris):
                    LOGGER.error("Bad ranking ground truth for query %s"
                                 % str(fqid))
                else:
                    self.num_rankings += 1
                    ranking_idx = 0
                    for mrc in mrcs:
                        if (set(mris[ranking_idx:ranking_idx + mrc])
                            != set(rris[ranking_idx:ranking_idx + mrc])):
                            badly_ranked = True
                            break
                        ranking_idx += mrc
            # logging:
            if falsepos:
                LOGGER.info("Query %s erroneously returned records with the "
                            "following ids: %s" % (
                                str(fqid),
                                ", ".join([str(ri) for ri in falsepos])))
            if falseneg:
                LOGGER.info("Query %s should have returned records with the "
                            "following ids: %s" % (
                                str(fqid),
                                ", ".join([str(ri) for ri in falseneg])))
            if badhash:
                LOGGER.info("Query %s had bad hashes for records with the "
                            "following ids: %s" % (
                                str(fqid),
                                ", ".join([str(ri) for ri in badhash])))
            if badly_ranked:
                LOGGER.info("Query %s was incorrectly ranked" % str(fqid))
            if update_db:
                if (falsepos or falseneg or badhash or status):
                    is_correct = False
                else:
                    is_correct = True
                if is_correct != stored_is_correct:
                    self.results_db.update(
                        t1s.DBP_TABLENAME, t1s.DBP_ISCORRECT, is_correct,
                        constraint_list=[(t1s.DBP_TABLENAME, "ROWID", pqid)])
            if badly_ranked:
                self.num_bad_rankings += 1
            self.num_truepos += len(truepos)
            self.num_falsepos += len(falsepos)
            self.num_falseneg += len(falseneg)
            self.num_badhash += len(badhash)
            self.num_goodhash += len(truepos) - len(badhash)
            if not (badly_ranked or falsepos or falseneg or badhash):
                self.num_correct += 1

    def get_badhash_fraction(self):
        """Returns the fraction of hashes returned as true positives that were
        incorrect."""
        if not (self.num_badhash + self.num_goodhash):
            return 0
        return self.num_badhash / (self.num_badhash + self.num_goodhash)

    def get_num_bad_rankings(self):
        """Returns the number of bad P9 rankings."""
        return self.num_bad_rankings

    def get_num_failed(self):
        """Returns the number of failed queries."""
        return self.num_failed

    def is_perfect(self):
        """Returns True if correctness is perfect, and False otherwise."""
        return (super(QueryCorrectnessGetter, self).is_perfect()
                and self.get_badhash_fraction() == 0.0
                and self.get_num_bad_rankings() == 0)
    
class PolicyCorrectnessGetter(correctness_getter.CorrectnessGetter):
    """This class computes the correctness metrics (precision and recall) for \
    the policy enforcement process.
    """
    def __init__(self, results_db=None, constraint_list=None):
        """Initializes the PolicyCorrectnessGetter with a results database and
        a where clause.

        All of the computation is done at initialization."""
        super(PolicyCorrectnessGetter, self).__init__(results_db,
                                                      constraint_list)
        self.populate()

    def populate(self):
        """
        Populates the _num_truepos, _num_falsepos, _num_falseneg, and other
        values.
        """
        if self.results_db == None:
            return
        # retrieve four lists:
        fields = [(t1s.DBF_TABLENAME, t1s.DBF_REJECTINGPOLICIES),
                  (t1s.DBP_TABLENAME, t1s.DBP_CURRENTPOLICIES),
                  (t1s.DBF_TABLENAME, t1s.DBF_MATCHINGRECORDIDS),
                  (t1s.DBP_TABLENAME, t1s.DBP_RETURNEDRECORDIDS)]
        [rejecting_policies, # contains lists of the policies by which each
                             # query is rejected
         current_policies, # contains the current policy for each query
         matching_record_ids, # contains the returned record ids for each query
         returned_record_ids # contains the matching record ids for each query
         ] = self.results_db.get_query_values(
             fields, constraint_list=self.constraint_list)
        num_queries = len(rejecting_policies)
        val_lists_and_names = [
            (current_policies, "current policies"),
            (returned_record_ids, "returned record ids"),
            (matching_record_ids, "matching record ids")]
        for (val_list, name) in val_lists_and_names:
            assert len(val_list) == num_queries, "wrong number of %s" % name
        # iterate through all of the relevent queries, incrementing the running
        # counters as we go:
        for query_index in xrange(num_queries):
            if not matching_record_ids[query_index]:
                # nothing can be determined about a query which is not supposed
                # to match any records, so it will not be counted.
                continue
            # determine whether there are any policies:
            if not current_policies[query_index]:
                # queries without policy enforcement are not counted
                continue
            self.count += 1 
            # determine whether the index-th query was rejected:
            if not returned_record_ids[query_index]:
                # the record was rejected.
                was_rejected = True
            else:
                # the record was not rejected.
                was_rejected = False
            # determine whether the index-th query was supposed to be rejectd:
            if (set(rejecting_policies[query_index])
                & set(current_policies[query_index])):
                # the query should have been rejected
                should_be_rejected = True
            else:
                # the query should not have been rejected
                should_be_rejected = False
            if was_rejected and should_be_rejected:
                self.num_truepos += 1
            elif was_rejected and not should_be_rejected:
                self.num_falsepos += 1
            elif not was_rejected and should_be_rejected:
                self.num_falseneg += 1
            if was_rejected == should_be_rejected:
                self.num_correct += 1
            
