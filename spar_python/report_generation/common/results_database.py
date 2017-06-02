# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A results database
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  16 Oct 1013   SY             Original version
# **************************************************************

# general imports:
import sqlite3
import csv
import logging
import copy

# SPAR imports:
import spar_python.report_generation.common.results_schema as results_schema

# LOGGER:
LOGGER = logging.getLogger(__file__)

class ResultsDB(object):
    """
    A results database, containing per-operation information such as baseline
    results, performer results, etc.

    Attributes:
        _db_path: the path to the results database
        _db_conn: the sqlite connection to the results database
        _db_curs: the cursour of the results database
        _schema: a results database schema object
    """

    def __init__(self, db_path, schema):
        """
        Initializes the database with a location (db_path), a schema module and
        a logger, then starts the connecion and provides a cursor.
        """
        # Establish database connection:
        self._db_path = db_path
        self._db_conn = sqlite3.connect(self._db_path)
        self._db_curs = self._db_conn.cursor()
        self._schema = schema

        # build the tables if they do not already exist:
        table_creation_cmds = [
            self._schema.get_create_table_command(table)
            for table in
            self._schema.tablename_to_fieldtotype.keys()]
        for table_creation_cmd in table_creation_cmds:
            self._execute(table_creation_cmd)
        
    def _execute(self, sql_cmd):
        """
        Executes the speicified command on the database.

        Args:
          sql_cmd: a sql command
        """
        #LOGGER.info(sql_cmd)
        try:
            self._db_curs.execute(sql_cmd)
            self._commit()
        except sqlite3.OperationalError, e:
            e.args = ["The command in question: %s, The error message: %s" % (
                sql_cmd, e.args)]
            raise e

    def _execute_many(self, statement, values):
        """
        Executes multiple commands on the database.

        Args:
            statement: a sql command with '?' in the place of some of the values
            values: a list of value tuples
        """
        self._db_curs.executemany(statement, values)
        self._commit()
        
    def _fetchall(self):
        """
        Fetches all results of an executed query.
        """
        return self._db_curs.fetchall()

    def _fetchone(self):
        """
        Fetches the next result of an executed query.
        """
        return self._db_curs.fetchone()

    def _commit(self):
        """
        Commits pending changes to the database
        """
        self._db_conn.commit()
                 
    def close(self):
        """
        Closes the connection to the database
        """
        self._db_conn.close()

    def add_row(self, table, values):
        """
        Adds a row to the table specified.
        
        Args:
            table: the name of the table to which the row is to be added.
            values: a dictionary mapping field to value.
        """
        self.add_rows(table, [values])

    def add_rows(self, table, values):
        """
        Adds multiple rows to the table specified.

        Args:
            table: the name of the table to white the row is to be added.
            values: a list of dictionaries mapping field to value, one
                dictionary corresponding to each row to be added.
        """
        fields_list = list(set.union(*[set(values_dict.keys())
                                       for values_dict in values]))
        prepared_statement = "INSERT INTO %s (%s) VALUES (%s)" % (
            table, ",".join(fields_list),
            ",".join(["?" for field in fields_list]))
        prepared_values = [
            tuple([str(self._schema.process_to_database(
                table, field, values_dict[field]))
                   if field in values_dict else None
                   for field in fields_list]) for values_dict in values]
        self._execute_many(statement=prepared_statement,
                           values=prepared_values)

    def update(self, table, field, value, constraint_list=None,
               non_standard_constraint_list=None):
        """
        Updates a single value in the database.
    
        Args:
            table: the name of a table in the database
            field: a field in table
            value: the value that the field should have for the specified row
            constraint_list: a list of tuples of the form (table, field, value),
                where query values are returned only if table.field=value for
                all of the tuples.
            non_standard_constraint_list: a list of tuples of the form (table,
                field, constraint_template), where constraint_template is a
                string with two instances of %s; one for table, and one for
                field.
                This should be used for constraints that can't re represented as
                table.field=value.
        """
        constraint = self.build_constraint(
            constraint_list=constraint_list,
            non_standard_constraint_list=non_standard_constraint_list)
        processed_value = self._schema.process_to_database(
            table, field, value)
        if (field in self._schema.tablename_to_fieldtotype[table].keys() and
            self._schema.tablename_to_fieldtotype[
                table][field] == results_schema.FIELD_TYPES.TEXT):
            processed_value = "'" + processed_value + "'"
        cmd = "UPDATE {0} SET {1}={2}".format(table, field, processed_value)
        if constraint:
            cmd += " WHERE {0}".format(constraint)
        self._execute(cmd)

    def clear(self):
        """
        Clears the database
        """
        for table in self._schema.tablename_to_fieldtotype.keys():
            self._execute("DELETE FROM " + table + " WHERE 1=1")

    def is_populated(self, table, field, constraint_list=None,
                     non_standard_constraint_list=None):
        """
        Args:
            table: a table in the database
            field: a field in table
            constraint_list: a list of tuples of the form (table, field, value),
                where query values are returned only if table.field=value for
                all of the tuples.
            non_standard_constraint_list: a list of tuples of the form (table,
                field, constraint_template), where constraint_template is a
                string with two instances of %s; one for table, and one for
                field.
                This should be used for constraints that can't re represented as
                table.field=value.

        Returns True if field is populated in table wherever the constraint
        holds. Returns False otherwise.
        """
        vals = self.get_values(
            [(table, field)], constraint_list=constraint_list,
            non_standard_constraint_list=non_standard_constraint_list)[0]
        return all([val not in results_schema.NULL_VALUES for val in vals])

    def build_simple_query_cmd(self, fields, constraint_list=None,
                               non_standard_constraint_list=None):
        """
        Args:
            fields: a list of tuples of the form (table, field) the
                values for which are desired.
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
        tables = list(set([table for (table, field) in fields]))
        assert len(tables) == 1, "cannot retreive from more than one table"
        table = tables[0]
        if not constraint_list: constraint_list = []
        if not non_standard_constraint_list: non_standard_constraint_list = []
        constraint = None
        if constraint_list or non_standard_constraint_list:
            constraint = self.build_constraint(
                constraint_list, non_standard_constraint_list)
        sql_cmd = "SELECT "
        sql_cmd += ", ".join([".".join([table, field])
                              for (table, field) in fields])
        sql_cmd += " FROM {}".format(table)
        if constraint:
            sql_cmd += " WHERE " + constraint
        return sql_cmd

    def build_query_cmd(
        self, fields, constraint_list=None, non_standard_constraint_list=None,
        override_tablename_to_joins=None, override_primary_table=None):
        """
        Args:
            fields: a list of tuples of the form (table, field) the
                values for which are desired.
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
        tablename_to_joins = copy.deepcopy(self._schema.tablename_to_joins)
        if override_tablename_to_joins:
            tablename_to_joins.update(override_tablename_to_joins)
        if not constraint_list:
            constraint_list = []
        if not non_standard_constraint_list:
            non_standard_constraint_list = []
        tables = set([table for (table, field) in fields] +
                     [table for (table, field, value) in constraint_list] +
                     [table for (table, field, constraint_template) in
                                 non_standard_constraint_list])
        present_per_tables = list(self._schema.performer_tablenames & tables)
        if len(list(tables)) == 1:
            # this is a simple query, and can be handled by a generic database.
            return self.build_simple_query_cmd(
                fields=fields, constraint_list=constraint_list,
                non_standard_constraint_list=non_standard_constraint_list)
        assert len(present_per_tables) <= 1, (
            "too many performer tables are present.")
        if present_per_tables:
            primary_table = present_per_tables[0]
        else:
            for tablename in self._schema.other_tablenames_heirarchy:
                if tablename in tables:
                    primary_table = tablename
        if not override_primary_table:
            override_primary_table = primary_table
        constraint = None
        if constraint_list or non_standard_constraint_list:
            constraint = self.build_constraint(
                constraint_list, non_standard_constraint_list)
        sql_cmd = "SELECT "
        sql_cmd += ", ".join([".".join([table, field])
                              for (table, field) in fields])
        # map of primary table to necessary joins (denoted tuples of the
        # form (source_table, source_field, target_table, target_field)):
        sql_cmd += " FROM {}".format(override_primary_table)
        awaiting_joins = tablename_to_joins[primary_table]
        performed_joins = []
        while awaiting_joins:
            join = awaiting_joins.pop()
            (source_table, source_field, target_table, target_field,
             alias) = join
            if join not in performed_joins:
                if not alias:
                    sql_cmd += " INNER JOIN {0} ON {1}.{2}={0}.{3}".format(
                        target_table, #0
                        source_table, #1
                        source_field, #2
                        target_field) #3
                else:
                    sql_cmd += " INNER JOIN {0} AS {4} ON {1}.{2}={4}.{3}".format(
                        target_table,
                        source_table,
                        source_field,
                        target_field,
                        alias)
                performed_joins.append(join)
                awaiting_joins.extend(tablename_to_joins[target_table])
        if constraint:
            sql_cmd += " WHERE " + constraint
        return sql_cmd

    def get_values(self, fields, constraint_list=None,
                   non_standard_constraint_list=None):
        """
        Args:
            fields: a list of tuples of the form (table, field) the unique
                values for which are desired.
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
            fields, constraint_list=constraint_list,
            non_standard_constraint_list=non_standard_constraint_list))
        if not values_list: values_list = [[] for field_idx
                                           in xrange(len(fields))]
        return values_list

    def get_unique_values(self, fields, constraint_list=None,
                          non_standard_constraint_list=None):
        """
        Args:
            fields: a list of tuples of the form (table, field) the unique
                values for which are desired.
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
        num_fields = len(fields)
        assert num_fields > 0, (
            "cannot retreive unique values when no fields are specified")
        output = self._process_query_cmd(
            fields, constraint_list, non_standard_constraint_list)
        output = list(set(output))
        output = self.sort(output, fields)
        if num_fields == 1:
            output = [elt[0] for elt in output]
        return output

    def _process_query_cmd(self, fields, constraint_list=None,
                           non_standard_constraint_list=None):
        """
        Args:
            fields: a list of tuples of the form (table, field) the unique
                values for which are desired.
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
        sql_cmd = self.build_query_cmd(fields, constraint_list,
                                       non_standard_constraint_list)
        num_fields = len(fields)
        values_list = []
        self._execute(sql_cmd)
        row = self._fetchone()
        while row != [] and row != None:
            assert len(row) == num_fields
            row_values = tuple([
                self._schema.process_from_database(
                    table, field, row_elt)
                for ((table, field), row_elt) in zip(fields, row)])
            values_list.append(row_values)
            row = self._fetchone()
        if not values_list:
            LOGGER.warn(
                "No entries were found with the constraint %s."
                % self.build_constraint(
                    constraint_list=constraint_list,
                    non_standard_constraint_list=non_standard_constraint_list))
        return values_list

    def to_values_list(self, list_of_tuples):
        """
        Args:
            list_of_tuples: a list of tuples

        Returns:
            A list of lists, each list corresponding to the values at one index
            of the tuples
        """
        return [list(values) for values in zip(*list_of_tuples)]

    def sort(self, tuples, list_of_fields):
        """
        Sorts the tuples in a canonical way.
        Args:
            tuples: a list of tuples, each tuple containing values, one
                corresponding to each field in list_of_fields
            list_of_fields: a list of tuples of the form (table, field)
        """
        def func(tup):
            return [self._schema.process_for_sorting(
                item, (table, field))
                    for (item, (table, field)) in zip(tup, list_of_fields)]
        return sorted(tuples, key=func)

    def build_constraint(self, constraint_list=None,
                         non_standard_constraint_list=None):
        """
        Args:
            constraint_list: a list of tuples of the form (table, field, value).
            non_standard_constraint_list: a list of tuples of the form (table,
                field, constraint_template), where constraint_template is a
                string with two instances of %s; one for table, and one for
                field.
                This should be used for constraints that can't re represented
                as table.field=value.

        Returns:
            a string representing the constraint in sqlite syntax.
        """
        if not constraint_list: constraint_list = []
        if not non_standard_constraint_list: non_standard_constraint_list = []
        constraints = []
        for (table, field, value) in constraint_list:
            processed_value = self._schema.process_to_database(
                table, field, value)
            if processed_value in results_schema.NULL_VALUES:
                constraints.append(
                    "({0}.{1} is NULL OR {0}.{1}='')".format(table, field))
            elif ((field in self._schema.tablename_to_fieldtotype[table].keys())
                  and (self._schema.tablename_to_fieldtotype[
                      table][field] == results_schema.FIELD_TYPES.BOOL)):
                if processed_value in results_schema.TRUE_VALUES:
                    constraints.append("{0}.{1}".format(table, field))
                elif processed_value in results_schema.FALSE_VALUES:
                    constraints.append("NOT {0}.{1}".format(table, field))
                else:
                    assert False, ("non-boolean value assigned to boolean "
                                   "field in constraint")
            elif ((field in self._schema.tablename_to_fieldtotype[table].keys())
                  and (self._schema.tablename_to_fieldtotype[
                      table][field] == results_schema.FIELD_TYPES.TEXT)):
                constraints.append("{0}.{1}='{2}'".format(
                    table, field, processed_value))
            else:
                constraints.append("{0}.{1}={2}".format(
                    table, field, processed_value))
        constraints += [constraint_template % (table, field)
                        for (table, field, constraint_template)
                        in non_standard_constraint_list]
        if not constraints: constraints.append("1=1")
        return " AND ".join(constraints)

    def output_csv(self, table_name, csv_file):
        """
        Writes the contents of a table to a csv file.

        Args:
            table_name: the name of a table in the database
            csv_file: a file to which the content of the table is to be
                written
        """
        sql_cmd = "PRAGMA table_info(%s)" % table_name
        self._execute(sql_cmd)
        column_header_tuples = self._db_curs.fetchall()
        column_headers = [str(tup[1]) for tup in column_header_tuples]
        # write to the csv file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(column_headers)
        sql_cmd = "SELECT * FROM %s" % table_name
        self._execute(sql_cmd)
        row = self._db_curs.fetchone()
        while row:
            csv_writer.writerow(row)
            row = self._db_curs.fetchone()
