# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A TA2 results database
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  16 Oct 1013   SY             Original version
# **************************************************************

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta2.ta2_schema as t2s
import spar_python.report_generation.common.results_database as results_database

# LOGGER:
LOGGER = logging.getLogger(__file__)

class Ta2ResultsDB(results_database.ResultsDB):
    """
    A TA2 results database, containing per-evaluation information.
    """

    def __init__(self, db_path):
        """
        Initializes the database with a location (db_path) and a logger.
        """
        schema = t2s.Ta2ResultsSchema()
        super(Ta2ResultsDB, self).__init__(
            db_path, schema)        

    def _get_next_id(self, table_name, id_field_name):
        """Returns the next value of the given field in the given table."""
        all_ids = self.get_values(fields=[(table_name, id_field_name)])[0]
        if not all_ids:
            next_id = 1
        else:
            next_id = max(all_ids) + 1
        return next_id

    def get_next_params_id(self):
        """Returns the next params id."""
        return self._get_next_id(t2s.PARAM_TABLENAME, t2s.PARAM_PID)

    def get_next_circuit_id(self):
        """Returns the next circuit id."""
        return self._get_next_id(t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_CID)

    def get_next_input_id(self):
        """Returns the next input id."""
        return self._get_next_id(t2s.INPUT_TABLENAME, t2s.INPUT_IID)
