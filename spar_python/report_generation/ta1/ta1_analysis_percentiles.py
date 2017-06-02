# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA1 percentile getter
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Oct 2013   SY             Original Version
# *****************************************************************

import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.common.percentiles as percentiles

class Ta1PercentileGetter(percentiles.PercentileGetter):
    """This is the class that handles TA1 percentile analysis.
    
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
        self._fields = [(t1s.DBP_TABLENAME, t1s.DBP_FQID),
                        (t1s.DBP_TABLENAME, t1s.DBP_QUERYLATENCY)]
        [self._performer_ids,
         self._performer_latencies] = results_db.get_query_values(
            self._fields, constraint_list=performer_constraint_list)
        [self._baseline_ids,
         self._baseline_latencies] = results_db.get_query_values(
            self._fields, constraint_list=baseline_constraint_list)
        super(Ta1PercentileGetter, self).__init__(results_db,
                                                  performer_constraint_list,
                                                  baseline_constraint_list)
