# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA2 percentile getter
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Oct 2013   SY             Original Version
# *****************************************************************

# SPAR imports:
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.percentiles as percentiles

class Ta2PercentileGetter(percentiles.PercentileGetter):
    """This is the class that handles TA2 percentile analysis.
    
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
        self._fields = [
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_IID),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_ENCRYPTIONLATENCY),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_EVALUATIONLATENCY),
            (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_DECRYPTIONLATENCY)]
        performer_values = results_db.get_values(
            self._fields, constraint_list=performer_constraint_list)
        self._performer_ids = performer_values[0]
        self._performer_latencies = [
            enclat + evallat + declat for (enclat, evallat, declat) in
            zip(*performer_values[1:])]
        baseline_values = results_db.get_values(
            self._fields, constraint_list=baseline_constraint_list)
        self._baseline_ids = baseline_values[0]
        self._baseline_latencies = [
            enclat + evallat + declat for (enclat, evallat, declat) in
            zip(*baseline_values[1:])]
        super(Ta2PercentileGetter, self).__init__(results_db,
                                                  performer_constraint_list,
                                                  baseline_constraint_list)
