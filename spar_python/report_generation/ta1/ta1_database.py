# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A TA1 results database
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  Earlier       NH             Original Version
#  13 May 2013   SY
#  5 June 2013   MZ             Updated to new schema
#  5 Aug 1013    SY             Added some functionality
# **************************************************************

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.common.results_database as results_database

# LOGGER:
LOGGER = logging.getLogger(__file__)

class Ta1ResultsDB(results_database.ResultsDB):
    """
    A TA1 results database, containing per-query information.
    """

    def __init__(self, db_path):
        """
        Initializes the database with a location (db_path) and a logger.
        """
        schema = t1s.Ta1ResultsSchema()
        super(Ta1ResultsDB, self).__init__(db_path, schema)        

    def get_unique_query_values(self, simple_fields=None,
                                atomic_fields_and_functions=None,
                                full_fields_and_functions=None,
                                constraint_list=None,
                                non_standard_constraint_list=None):
        """
        Args:
            simple_fields: a list of tuples of the form (table, field), where
                table is either the full queries or the performer queries table.
            atomic_fields_and_functions: a list of tuples of the form
                (field, function), where field should be in the atomic queries
                table
            full_fields_and_functions: a list of tuples of the form
                (field, function), where field should be in the full queries
                table
            constraint_list: a list of tuples of the form (table, field, value),
                where query values are returned only if table.field=value for
                all of the tuples.
            non_standard_constraint_list: a list of tuples of the form (table,
                field, constraint_template), where constraint_template is a
                string with two instances of %s; one for table, and one for
                field.
                This should be used for constraints that can't re represented as
                table.field=value.

        Returns:
            A list of all the unique values of the fields in question where the
            constraint holds.
        """
        if not full_fields_and_functions: full_fields_and_functions = []
        if not atomic_fields_and_functions: atomic_fields_and_functions = []
        if not simple_fields: simple_fields = []
        num_fields = sum([len(simple_fields), len(atomic_fields_and_functions),
                          len(full_fields_and_functions)])
        assert num_fields > 0, (
            "cannot retreive unique values when no fields are specified")
        output = self._process_query_cmd(
            simple_fields, atomic_fields_and_functions,
            full_fields_and_functions, constraint_list,
            non_standard_constraint_list)
        output = list(set(output))
        output = self.sort(output, simple_fields + [
            (t1s.DBA_TABLENAME, field) for (field, function)
            in atomic_fields_and_functions] + [
            (t1s.DBF_TABLENAME, field) for (field, function)
            in full_fields_and_functions])
        if num_fields == 1:
            output = [elt[0] for elt in output]
        return output
    
    def get_query_values(self, simple_fields,
                         atomic_fields_and_functions=None,
                         full_fields_and_functions=None,
                         constraint_list=None,
                         non_standard_constraint_list=None):
        """
        Args:
            simple_fields: a list of tuples of the form (table, field), where
                table is either the full queries or the performer queries table.
            atomic_fields_and_functions: a list of tuples of the form
                (field, function), where field should be in the atomic queries
                table
            full_fields_and_functions: a list of tuples of the form
                (field, function), where field should be in the full queries
                table
            constraint_list: a list of tuples of the form (table, field, value),
                where query values are returned only if table.field=value for
                all of the tuples.
            non_standard_constraint_list: a list of tuples of the form (table,
                field, constraint_template), where constraint_template is a
                string with two instances of %s; one for table, and one for
                field.
                This should be used for constraints that can't re represented as
                table.field=value.

        Returns:
            A two-dimensional list, with one sub-list corresponding to each
            field.
        """
        values_list = self.to_values_list(self._process_query_cmd(
            simple_fields,
            atomic_fields_and_functions,
            full_fields_and_functions,
            constraint_list=constraint_list,
            non_standard_constraint_list=non_standard_constraint_list))
        if not simple_fields: simple_fields = []
        if not atomic_fields_and_functions: atomic_fields_and_functions = []
        if not full_fields_and_functions: full_fields_and_functions = []
        num_fields = (len(simple_fields) +
                      len(atomic_fields_and_functions) +
                      len(full_fields_and_functions))
        if not values_list: values_list = [[] for field_idx
                                           in xrange(num_fields)]
        return values_list
        

    def _process_query_cmd(self, simple_fields=None,
                           atomic_fields_and_functions=None,
                           full_fields_and_functions=None,
                           constraint_list=None,
                           non_standard_constraint_list=None):
        """
        Args:
            simple_fields: a list of tuples of the form (table, field), where
                table is either the full queries or the performer queries table.
            atomic_fields_and_functions: a list of tuples of the form
                (field, function), where field should be in the atomic queries
                table
            full_fields_and_functions: a list of tuples of the form
                (field, function), where field should be in the full queries
                table
            constraint_list: a list of tuples of the form (table, field, value),
                where query values are returned only if table.field=value for
                all of the tuples.
            non_standard_constraint_list: a list of tuples of the form (table,
                field, constraint_template), where constraint_template is a
                string with two instances of %s; one for table, and one for
                field.
                This should be used for constraints that can't re represented as
                table.field=value.

        Returns:
            A list of tuples containing the desired values
        """
        if not simple_fields: simple_fields = []
        if not atomic_fields_and_functions: atomic_fields_and_functions = []
        if not full_fields_and_functions: full_fields_and_functions = []
        if not constraint_list: constraint_list = []
        if not non_standard_constraint_list: non_standard_constraint_list = []
        assert not (atomic_fields_and_functions and full_fields_and_functions),(
            "cannot include both atomic and full sub-queries")
        constraint_tables = [table for (table, field, thing)
                             in constraint_list + non_standard_constraint_list]
        functions = [
            self._schema.get_complex_function(table, field, False)
            for (table, field) in simple_fields] + [
            function for (field, function)
            in atomic_fields_and_functions] + [
            function for (field, function)
            in full_fields_and_functions]
        atomic_fields = [field for (field, function)
                         in atomic_fields_and_functions]
        full_fields = [field for (field, function)
                       in full_fields_and_functions]
        sql_cmd = self.build_pquery_query_cmd(
            simple_fields, atomic_fields, full_fields,
            constraint_list, non_standard_constraint_list)
        if atomic_fields_and_functions or full_fields_and_functions:
            values_list = self._process_complex_query_cmd(sql_cmd, functions)
        else:
            values_list = self._process_simple_query_cmd(sql_cmd, simple_fields)
        if not values_list:
            LOGGER.warn("No items were found with the constraint %s."
                        % self.build_constraint(constraint_list,
                                                non_standard_constraint_list))
        return values_list

    def _process_simple_query_cmd(self, sql_cmd, simple_fields):
        """
        Args:
            sql_cmd: an sql command
            simple_fields: a list of tuples of the form (table, field), where
                table is either the full queries or the performer queries table.

        Returns:
            A list of tuples, each tuple corresponding to the desired values
            for a single performer query

        Executes the given sql command and returns the desired values.
        """
        num_fields = len(simple_fields)
        output = []
        self._execute(sql_cmd)
        row = self._fetchone()
        while row != [] and row != None:
            assert len(row) == num_fields
            row_values = tuple([
                self._schema.process_from_database(
                    table, field, row_elt)
                for ((table, field), row_elt) in zip(simple_fields, row)])
            output.append(row_values)
            row = self._fetchone()
        return output

    def _process_complex_query_cmd(self, sql_cmd, functions):
        """
        Args:
            sql_cmd: an sql command
            functions: a list of functions to be applied to the retreived
                values

        Returns:
            A list of tuples, each tuple corresponding to the desired values
            for a single performer query

        Given an sql command and a list of functions, uses junction tables
        to associate lists of values with each performer query id, and executes
        the given functions on those lists of values.
        """
        num_fields = len(functions)
        self._execute(sql_cmd)
        
        # vals: Temporary storage for the valies.
        # Each full query id maps to a list of value tuples.
        vals = {}
        # p2f: A map of performer query ids to full query ids,
        # for proper ordering
        p2f = {}
        
        row = self._fetchone()
        while row != [] and row != None:
            jid = int(row[0]) # junction id
            pqid = int(row[1]) # performer query id
            fqid = int(row[2]) # full query id
            p2f[pqid] = fqid
            other_vals = row[3:]
            assert len(other_vals) == num_fields
            if pqid not in vals:
                vals[pqid] = {}
            vals[pqid][jid] = tuple(other_vals)
            row = self._fetchone()
        # output: the list of tuples to be returned
        output = []
        pqids = p2f.keys()
        pqids.sort()
        # Populate output:    
        for pqid in pqids:
            processed_vals = []
            for field_index in xrange(num_fields):
                function = functions[field_index]
                jids = vals[pqid].keys()
                jids.sort()
                field_input_vals = [vals[pqid][jid][field_index]
                                      for jid in jids]
                field_processed_vals = function(field_input_vals)
                processed_vals.append(field_processed_vals)
            output.append(tuple(processed_vals))
        return output

    def build_pquery_query_cmd(self, fields,
                               atomic_fields=None, full_fields=None,
                               constraint_list=None,
                               non_standard_constraint_list=None):
        """
        Args:
            fields: a list of tuples of the form
                (table, field), where table is either
                the full queries or the performer queries table.
                If the data in question is only for atomic queries, then the
                atomic queries table can be listed here as well.
            atomic_fields: a list of fields in the atomic
                query database to be process as a sub atomic query field.
            full_fields: a list of fields in the full
                query database to be process as a sub full query field.
            constraint_list: a list of tuples of the form (table, field, value),
                where query values are returned only if table.field=value for
                all of the tuples.
            non_standard_constraint_list: a list of tuples of the form (table,
                field, constraint_template), where constraint_template is a
                string with two instances of %s; one for table, and one for
                field.
                This should be used for constraints that can't re represented as
                table.field=value.
                
        Returns:
            An sql command that retreives the values of the fields where the
            constraint holds.
        """
        if not constraint_list: constraint_list = []
        if not non_standard_constraint_list: non_standard_constraint_list = []
        # get values from the performer and full tables:
        these_fields = fields[:]
        # update the fields as needed:
        if atomic_fields or full_fields:
            assert not (atomic_fields and full_fields), (
                "cannot support a full-to-atomic and a full-to-full query "
                "simultaneously")
            if atomic_fields:
                additional_fields = atomic_fields
                join_tablename = t1s.F2A_TABLENAME
                target_tablename = t1s.DBA_TABLENAME
            else:
                additional_fields = full_fields
                join_tablename = t1s.F2F_TABLENAME
                target_tablename = t1s.DBF_ALIAS2
            these_fields = [
                (join_tablename, "ROWID"), # for proper ordering
                (t1s.DBP_TABLENAME, "ROWID"), # for proper ordering
                (t1s.DBP_TABLENAME, t1s.DBP_FQID)
                ] + these_fields + [
                    (target_tablename, field) for field in additional_fields]
        # update the override_tablename_to_joins as needed:
        override_tablename_to_joins = None
        these_tables = set(
            [table for (table, field) in these_fields] + [
                table for (table, field, value) in constraint_list] + [
                    table for (table, field, constraint_template) in
                    non_standard_constraint_list])
        if atomic_fields or (t1s.DBA_TABLENAME in these_tables):
            override_tablename_to_joins = {
                t1s.DBF_TABLENAME: [
                    (t1s.DBF_TABLENAME,
                     t1s.DBF_FQID,
                     t1s.F2A_TABLENAME,
                     t1s.F2A_FQID,
                     None),
                    (t1s.F2A_TABLENAME,
                     t1s.F2A_AQID,
                     t1s.DBA_TABLENAME,
                     t1s.DBA_AQID,
                     None)]}
        if full_fields:
            override_tablename_to_joins = {
                t1s.DBF_TABLENAME: [
                    (t1s.DBF_TABLENAME,
                     t1s.DBF_FQID,
                     t1s.F2F_TABLENAME,
                     t1s.F2F_COMPOSITEQID,
                     None),
                    (t1s.F2F_TABLENAME,
                     t1s.F2F_BASEQID,
                     t1s.DBF_TABLENAME,
                     t1s.DBF_FQID,
                     t1s.DBF_ALIAS2)]}
        return self.build_query_cmd(
            these_fields, constraint_list, non_standard_constraint_list,
            override_tablename_to_joins=override_tablename_to_joins)
