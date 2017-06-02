# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        The code that handles the generation of the percentiles
#                      numbers for the final report
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  29 Jul 2013   SY             Original Version
#  24 Oct 2013   SY             Added TA2 support
# *****************************************************************

# SPAR imports:
import spar_python.report_generation.common.percentile_finder as pf

class PercentileGetter(object):
    """This is the class that handles percentile analysis.
    
    Attributes:
        results_db: A results database object.
        performer_constraint_list: a list of tuples of the form (table, field,
            value), where all relevent performer queries must have
            table.field=value for all of these tuples.
        baseline_constraint_list: a list of tuples of the form (table, field,
            value), where all relevent baseline queries must have
            table.field=value for all of these tuples.
    """
    def __init__(self, results_db,
                 performer_constraint_list,
                 baseline_constraint_list):
        """Initializes the PercentilesGetter with a results database,
        a performer_constraint_list and a baseline_constraint_list."""
        self._results_db = results_db
        self._performer_constraint_list = performer_constraint_list
        self._baseline_constraint_list = baseline_constraint_list
        # we only care about the values on the same queries:
        common_ids = list(set(self._performer_ids) & set(self._baseline_ids))
        performer_latencies = [
            this_lat for (this_id, this_lat) in zip(self._performer_ids,
                                                    self._performer_latencies)
            if this_id in common_ids]
        baseline_latencies = [
            this_lat for (this_id, this_lat) in zip(self._baseline_ids,
                                                    self._baseline_latencies)
            if this_id in common_ids]
        # compute the percentiles:
        self._performer_percentiles = [
            pf.PercentileFinder(performer_latencies).getPercentile(index)
            for index in xrange(1, 101)]
        self._baseline_percentiles = [
            pf.PercentileFinder(baseline_latencies).getPercentile(index)
            for index in xrange(1, 101)]

    def get_performer_percentiles(self):
        """Returns the performer percentiles."""
        return self._performer_percentiles

    def get_baseline_percentiles(self):
        """Returns the baseline percentiles."""
        return self._baseline_percentiles

    def has_values(self):
        """Returns True if the percentile getter has values, and False
        otherwise."""
        return ((None not in self.get_performer_percentiles())
                and (None not in self.get_baseline_percentiles()))

    def _is_met(self, percentile, a, b):
        """Returns True if at the indicated percentile, the performer does at
        least as well as a + bx, where x is the baseline value at the same
        percentile. Otherwise, returns False."""
        performer_percentile = self._performer_percentiles[percentile-1]
        baseline_percentile = self._baseline_percentiles[percentile-1]
        return performer_percentile <= a + (b*baseline_percentile)

    def get_all_met(self, a, b):
        """Returns a list of percentiles at which the performer does at least as
        well as ax + b, where x is the baseline value at the same percentile."""
        return [percentile for percentile in xrange(1, 101)
                if self._is_met(percentile, a, b)]
