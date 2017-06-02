# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A analysis input class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Sep 2013   SY             Original version
# *****************************************************************

# SPAR imports:
import spar_python.report_generation.ta1.ta1_config as config
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_test_database as t1tdb

class Input(dict):
    """Represents an input object"""

    @property
    def test_db(self):
        """Gives a test database object with the specified database number of
        records and record size"""
        return t1tdb.TestDatabase(
            db_num_records=self.get(t1s.DBF_NUMRECORDS),
            db_record_size=self.get(t1s.DBF_RECORDSIZE),
            short_database_names=config.SHORT_DATABASE_NAMES)

    def get_constraint_list(self):
        """Returns a constraint list based on the given arguments."""
        desired_constraints_list = [
            (t1s.DBF_TABLENAME, t1s.DBF_NUMRECORDS),
            (t1s.DBF_TABLENAME, t1s.DBF_RECORDSIZE),
            (t1s.DBF_TABLENAME, t1s.DBF_CAT),
            (t1s.DBF_TABLENAME, t1s.DBF_SUBCAT),
            (t1s.DBF_TABLENAME, t1s.DBF_SUBSUBCAT),
            (t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
            (t1s.DBA_TABLENAME, t1s.DBA_FIELD)]
        constraint_list = []
        for (table, field) in desired_constraints_list:
            if self.get(field):
                constraint_list.append((table, field, self.get(field)))
        return constraint_list
