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
import collections

# LOGGER:
LOGGER = logging.getLogger(__name__)

# SPAR imports:
import spar_python.report_generation.ta1.ta1_schema as t1s

# a class representing a modification instance:
Mod = collections.namedtuple(
    'Mod', ['pmid', 'mid', 'mstime', 'mrtime', 'mlatency', 'mstatus',
            'mcat', 'mrid'])

# a class representing a modification query instance:
Query = collections.namedtuple(
    'Query', ['pqid', 'qid', 'qstime', 'qrtime', 'qlatency', 'rris', 'rrhs',
              'qselectioncols', 'qstatus'])

# a class representing the analysis of a query with respect to a modification:
QueryCheck = collections.namedtuple(
    'QueryCheck', ['correct_ids', 'correct_hashes', 'slatency', 'rlatency',
                   'modoccurred'])

Analysis = collections.namedtuple(
    'ModAnalysis', [
        'nummods', 'numfailedmods', 'nummodsbadinfo',
        'nummodswrongpostqueries', 'numgoodmods',
        'min_correct_slatencies', 'min_correct_rlatencies',
        'max_wrong_slatencies', 'max_wrong_rlatencies'])

class ModificationGetter(object):
    """This is class that handles all modification metric computations.
    
    Attributes:
        config: A configruation object.
        count: the number of items
    """

    def __init__(self, config):
        """Initializes the CorrectnessGetter with a configuration object."""
        self.config = config
        self._query_fields = [
            (t1s.DBP_TABLENAME, "ROWID"),
            (t1s.DBP_TABLENAME, t1s.DBP_FQID),
            (t1s.DBP_TABLENAME, t1s.DBP_SENDTIME),
            (t1s.DBP_TABLENAME, t1s.DBP_RESULTSTIME),
            (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY),
            (t1s.DBP_TABLENAME, t1s.DBP_RETURNEDRECORDIDS),
            (t1s.DBP_TABLENAME, t1s.DBP_RETURNEDRECORDHASHES),
            (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
            (t1s.DBP_TABLENAME, t1s.DBP_STATUS)]
        self._query_constraint_list = self.config.get_constraint_list(
            require_correct=False, mod=True)
        self._mods_fields = [
            (t1s.PMODS_TABLENAME, "ROWID"),
            (t1s.PMODS_TABLENAME, t1s.PMODS_MID),
            (t1s.PMODS_TABLENAME, t1s.PMODS_SENDTIME),
            (t1s.PMODS_TABLENAME, t1s.PMODS_RESULTSTIME),
            (t1s.PMODS_TABLENAME, t1s.PMODS_MODLATENCY),
            (t1s.PMODS_TABLENAME, t1s.PMODS_STATUS),
            (t1s.MODS_TABLENAME, t1s.MODS_CATEGORY),
            (t1s.MODS_TABLENAME, t1s.MODS_RECORDID)]
        self._mod_constraint_list = [
            (t1s.PMODS_TABLENAME, t1s.PMODS_PERFORMER,
             self.config.performername)]
        # populate the following in pre-processing:
        self._mods = []
        self._min_time = 0
        self._max_time = 0
        # populate the following during the analysis:
        self.analyses = {} # maps mod_cat to analysis object
        # perform the pre-processing:
        self._pre_process()
            
    def _pre_process(self):
        """Performs some pre-processing. Returns True if pre-processing indicates that
        analysis can be performed, and False otherwise."""
        # retrieve lists of all mod values:
        unsorted_mods = [
            Mod(*tup) for tup in zip(*self.config.results_db.get_values(
                fields=self._mods_fields,
                constraint_list=self._mod_constraint_list))]
        self._mods = sorted( # sort by send time
            unsorted_mods, key=lambda mod: mod.mstime)
        # retrieve lists of mod query values:
        unsorted_queries = [
            Query(*tup) for tup in zip(*self.config.results_db.get_query_values(
                simple_fields=self._query_fields,
                constraint_list=self._query_constraint_list))]
        queries = sorted( # sort by send time
            unsorted_queries, key=lambda query: query.qstime)
        # set the minimum and maximum time values:
        if not self._mods:
            LOGGER.error("No modifications found.")
        for (attr_name, func) in [("_min_time", min), ("_max_time", max)]:
            if not (self._mods or queries):
                setattr(self, attr_name, None)
            else:
                setattr(self, attr_name, func(
                    [func([mod.mstime for mod in self._mods]),
                     func([query.qstime for query in queries])]))
    
    def _get_queries(self, stime, etime):
        """Returns query objects for all the queries sent between stime and
        etime."""
        queries = [Query(*tup) for tup in zip(*
            self.config.results_db.get_query_values(
                simple_fields=self._query_fields,
                constraint_list=self._query_constraint_list,
                non_standard_constraint_list=[
                    (t1s.DBP_TABLENAME, t1s.DBP_SENDTIME,
                     "%s.%s >= " + str(stime)),
                    (t1s.DBP_TABLENAME, t1s.DBP_SENDTIME,
                     "%s.%s <= " + str(etime))]))]
        return queries

    def _check_query(self, query, mod, modoccurred):
        """
        Args:
            query: a query object
            mod: a modificationobject
            modoccurred: a boolean indicating whether or not the modification
                has already ocurred.

        Returns a querycheck object.
        """
        if modoccurred: # this is a POST query
            m2mq_fields = [
                (t1s.M2MQ_TABLENAME, t1s.M2MQ_POSTIDS),
                (t1s.M2MQ_TABLENAME, t1s.M2MQ_POSTHASHES)]
        else: # this is a PRE query
            m2mq_fields = [
                (t1s.M2MQ_TABLENAME, t1s.M2MQ_PREIDS),
                (t1s.M2MQ_TABLENAME, t1s.M2MQ_PREHASHES)]
        m2mq_values = self.config.results_db.get_values(
            fields=m2mq_fields,
            constraint_list=[
                (t1s.M2MQ_TABLENAME, t1s.M2MQ_QID, query.qid),
                (t1s.M2MQ_TABLENAME, t1s.M2MQ_MID, mod.mid)])
        if not m2mq_values[0]:
            # the query does not correspond to the modification under
            # consideration, so continue.
            return "NOTAPPLICABLE"
        [[mris], [mrhs]] = m2mq_values
        if query.qstatus:
            # the query failed, sp continue.
            self.num_failed_queries += 1
            return "FAILED"
        correct_ids = mris == query.rris
        if query.qselectioncols == "*":
            correct_hashes = mrhs == query.rrhs
        else:
            correct_hashes = True
        if modoccurred:
            slatency = query.qstime - mod.mrtime
            rlatency = query.qrtime - mod.mrtime
        else:
            slatency = None
            rlatency = None
        return QueryCheck(correct_ids, correct_hashes, slatency, rlatency,
                          modoccurred)

    def _weed_query_checks(self, query_checks):
        """
        Args:
            query_checks: a list of query check objects

        Returns a list of query check objects with the "FAILED" and "NOTAPPLICABLE"
        query checks excluded. Increments self.numfailedqueries appropriately.
        """
        weeded_query_checks = []
        for query_check in query_checks:
            if query_check == "FAILED":
                self.numfailedqueries += 1
            elif query_check == "NOTAPPLICABLE":
                pass
            else:
                weeded_query_checks.append(query_check)
        return weeded_query_checks

    def get_analysis(self, mod_cat):
        """
        Args:
            mod_cat: a modification category (insert, delete or update).

        Performs all the necessary analyses if necessary, and returns an
        Analysis object corresponding to the modification category.
        """
        if mod_cat not in self.analyses.keys():
            self.analyses[mod_cat] = self._perform_analysis(mod_cat)
        return self.analyses[mod_cat]
        
    def _perform_analysis(self, mod_cat):
        """
        Args:
            mod_cat: a modification category (insert, delete or update).

        Performs all the necessary analysis, and returns a Analysis object.
        """
        assert mod_cat in t1s.MOD_CATEGORIES.values_list(), (
            "invalid category: %s" % str(mod_cat))
        total_nummods = len(self._mods) # number of all modifications
        nummods = 0 # number of modifications of this type
        numfailedmods = 0
        nummodsbadinfo = 0
        nummodswrongpostqueries = 0
        numgoodmods = 0
        min_correct_slatencies = []
        min_correct_rlatencies = []
        max_wrong_slatencies = []
        max_wrong_rlatencies = []
        for (m_idx, mod) in zip(range(total_nummods), self._mods):
            if mod.mcat != mod_cat:
                # do not consider modifications of the wrong type
                continue
            nummods += 1
            if mod.mstatus:
                # do not further consider failed modifications
                numfailedmods += 1
                continue
            # find the previous and next send times:
            if m_idx == 0:
                prev_stime = self._min_time
            else:
                prev_stime = self._mods[m_idx - 1].mstime
            if m_idx == total_nummods - 1:
                next_stime = self._max_time
            else:
                next_stime = self._mods[m_idx + 1].mstime
            # get the pre-queries (all queries occurring between the previous
            # and this modification) and check them:
            pre_queries = self._get_queries(stime=prev_stime, etime=mod.mstime)
            allprequerychecks = [
                self._check_query(pre_query, mod, False)
                for pre_query in pre_queries]
            prequerychecks = self._weed_query_checks(allprequerychecks)
            wrong_prequery = False
            for query_check in prequerychecks:
                if not (query_check.correct_ids and query_check.correct_hashes):
                    wrong_prequery = True
            if ((not prequerychecks) or wrong_prequery):
                # the pre-queries were wrong; do not consider this modification
                # further
                nummodsbadinfo += 1
                continue
            # get the post-queries (all queries occurring between this and the
            # next modification) and check them:
            post_queries = self._get_queries(stime=mod.mstime, etime=next_stime)
            allpostquerychecks = []
            for post_query in post_queries:
                allpostquerychecks.append(self._check_query(post_query, mod, True))
            postquerychecks = self._weed_query_checks(allpostquerychecks)
            if not postquerychecks:
                # we do not have post-query information; do not consider this
                # modification further
                nummodsbadinfo += 1
                continue                
            correctquerychecks = []
            wrongquerychecks = []
            for query_check in postquerychecks:
                if (query_check.correct_ids and query_check.correct_hashes):
                    correctquerychecks.append(query_check)
                else:
                    wrongquerychecks.append(query_check)
            if wrongquerychecks:
                nummodswrongpostqueries += 1
            else:
                numgoodmods += 1
            if correctquerychecks:
                min_correct_slatencies.append(min(
                    [query_check.slatency for query_check in correctquerychecks
                     if query_check.slatency != None]))
                min_correct_rlatencies.append(min(
                    [query_check.rlatency for query_check in correctquerychecks
                     if query_check.rlatency != None]))
            if wrongquerychecks:
                max_wrong_slatencies.append(max(
                    [query_check.slatency for query_check in wrongquerychecks
                     if query_check.slatency != None]))
                max_wrong_rlatencies.append(max(
                    [query_check.rlatency for query_check in wrongquerychecks
                     if query_check.rlatency != None]))
        return Analysis(
            nummods=nummods, numfailedmods=numfailedmods,
            nummodsbadinfo=nummodsbadinfo,
            nummodswrongpostqueries=nummodswrongpostqueries,
            numgoodmods=numgoodmods,
            min_correct_slatencies=min_correct_slatencies,
            min_correct_rlatencies=min_correct_rlatencies,
            max_wrong_slatencies=max_wrong_slatencies,
            max_wrong_rlatencies=max_wrong_rlatencies)
