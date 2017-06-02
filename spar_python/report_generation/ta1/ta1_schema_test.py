# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests ta1_schema.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  5 Aug 2013    SY             Original Version
# *****************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.report_generation.ta1.ta1_schema as t1s

class Ta1SchemaTest(unittest.TestCase):

    def test_process_to_database(self):
        schema = t1s.Ta1ResultsSchema()
        tablename = t1s.DBF_TABLENAME
        field_simple = t1s.DBF_FQID
        value_simple = 7
        field_list_int = t1s.DBF_MATCHINGRECORDIDS
        value_list_int_db = "1|2|34"
        value_list_int_use = [1, 2, 34]
        field_list_str = t1s.DBF_MATCHINGRECORDHASHES
        value_list_str_db = "hash1|hash2|hash3"
        value_list_str_use = ["hash1", "hash2", "hash3"]
        self.assertEqual(
            schema.process_to_database(
                tablename, field_simple, value_simple),
            value_simple)
        self.assertEqual(
            schema.process_to_database(
                tablename, field_list_int, value_list_int_use),
            value_list_int_db)
        self.assertEqual(
            schema.process_to_database(
                tablename, field_list_str, value_list_str_use),
            value_list_str_db)

    def test_process_to_database(self):
        schema = t1s.Ta1ResultsSchema()
        tablename = t1s.DBF_TABLENAME
        field_simple = t1s.DBF_FQID
        value_simple = 7
        field_list_int = t1s.DBF_MATCHINGRECORDIDS
        value_list_int_db = "1|2|34"
        value_list_int_use = [1, 2, 34]
        field_list_str = t1s.DBF_MATCHINGRECORDHASHES
        value_list_str_db = "hash1|hash2|hash3"
        value_list_str_use = ["hash1", "hash2", "hash3"]
        self.assertEqual(
            schema.process_from_database(
                tablename, field_simple, value_simple),
            value_simple)
        self.assertEqual(
            schema.process_from_database(
                tablename, field_list_int, value_list_int_db),
            value_list_int_use)
        self.assertEqual(
            schema.process_from_database(
                tablename, field_list_str, value_list_str_db),
            value_list_str_use)

    def test_get_create_table_command(self):
        schema = t1s.Ta1ResultsSchema()
        desired_F2A_sql_cmd = "".join([
            "CREATE TABLE IF NOT EXISTS %s (" % t1s.F2A_TABLENAME,
            "%s INTEGER NOT NULL, " % t1s.F2A_FQID,
            "%s INTEGER NOT NULL, " % t1s.F2A_AQID,
            "FOREIGN KEY (%s) REFERENCES %s (ROWID), " %
            (t1s.F2A_FQID, t1s.DBF_TABLENAME),
            "FOREIGN KEY (%s) REFERENCES %s (ROWID))" %
            (t1s.F2A_AQID, t1s.DBA_TABLENAME)])
        self.assertEquals(
            schema.get_create_table_command(t1s.F2A_TABLENAME),
            desired_F2A_sql_cmd)
