# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Results database schema.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  16 Oct 2013   SY             Original Version
# *****************************************************************

# SPAR imports:
import spar_python.common.enum as enum

NULL_VALUES = ["NULL", None, "None", ""] # for checking whether a cell is populated
DB_NULL_VALUE = "NULL"
PY_NULL_VALUE = ""
TRUE_VALUES = ["True", "TRUE", "1", 1]
FALSE_VALUES = ["False", "FALSE", "0", 0]
DB_TRUE_VALUE = 1
DB_FALSE_VALUE = 0
PY_TRUE_VALUE = True
PY_FALSE_VALUE = False
DELIMITER = "|"

# field types in the results database:
FIELD_TYPES = enum.Enum("TEXT", "INTEGER", "REAL", "BOOL")

class ResultsSchema(object):

    def __init__(self):
        self.list_fields = dict()
        self.tablename_to_fieldtotype = None
        self.tablename_to_requiredfields = None
        self.tablename_to_aux = None
        self.tablename_to_joins = None
        self.performer_tablenamess = None
        self.other_tablenames_heirarchy = None
        
    def process_to_database_if_list(self, tablename, fieldname, value):
        """
        Args:
            tablename: the name of a table
            fieldname: the name of a field in tablename
            value: a value of fieldname

        Returns:
            The value formatted as it should be while in the database if the value
            represents a list
        """
        if (tablename, fieldname) in self.list_fields.keys():
            value = DELIMITER.join([str(elt) for elt in value])
        return value

    def process_to_database(self, tablename, fieldname, value):
        """
        Args:
            tablename: the name of a table
            fieldname: the name of a field in tablename
            value: a value of fieldname

        Returns:
            The value formatted as it should be while in the database
        """
        value = self.process_to_database_if_list(tablename, fieldname, value)
        if fieldname in self.tablename_to_fieldtotype[tablename].keys():
            if self.tablename_to_fieldtotype[
                tablename][fieldname] == FIELD_TYPES.TEXT:
                value = str(value)
                value.replace("'",'"')
                return value
            elif self.tablename_to_fieldtotype[
                tablename][fieldname] == FIELD_TYPES.BOOL:
                if value in NULL_VALUES:
                    return DB_NULL_VALUE
                elif value in FALSE_VALUES:
                    return DB_FALSE_VALUE
                else:
                    return DB_TRUE_VALUE
        return str(value)

    def process_from_database(self, tablename, fieldname, value):
        """
        Args:
            tablename: the name of a table
            fieldname: the name of a field in tablename
            value: a value of fieldname, formatted as it would be in the database

        Returns:
            The value formatted as it should be while being used
        """
        if (tablename, fieldname) in self.list_fields:
            if value in NULL_VALUES: value_list = []
            else:
                value_string_list = value.split(DELIMITER)
                # remove all empty elements from the list:
                value_string_list = filter(
                    lambda elt: elt != "", value_string_list)
                value_type = self.list_fields[(tablename, fieldname)]
                value_list = [value_type(elt) for elt in value_string_list]
            return value_list
        if value in NULL_VALUES:
            return PY_NULL_VALUE
        elif (fieldname in self.tablename_to_fieldtotype[tablename].keys() and
            self.tablename_to_fieldtotype[
                tablename][fieldname] == FIELD_TYPES.TEXT):
            value = str(value)
            value.replace('"', "'")
            return value
        elif (fieldname in self.tablename_to_fieldtotype[tablename].keys() and
            self.tablename_to_fieldtotype[
                tablename][fieldname] == FIELD_TYPES.BOOL):
            if value in TRUE_VALUES:
                return PY_TRUE_VALUE
            elif value in FALSE_VALUES:
                return PY_FALSE_VALUE
            else:
                assert False, (
                    "a boolean value should have one of the expected forms",
                    "which %s does not conform to." % value)
        else:
            return value

    def get_complex_function(self, tablename, fieldname, is_list=False):
        """
        Args:
            tablename: the name of a table
            fieldname: the name of a field in tablename
            is_complex: a boolean indicating whether or not the values should be
                many or one.

        Returns:
            a function that maps many values of fieldname to a single value
            (possibly a tuple)
        """
        if is_list:
            def func(values):
                return tuple(
                    [self.process_from_database(tablename, fieldname, value)
                     for value in values])
        else:
            def func(values):
                assert all([
                    values[0] == values[idx] for idx in xrange(len(values))])
                return self.process_from_database(
                    tablename, fieldname, values[0])
        return func

    def get_create_table_command(self, tablename):
        """
        Args:
            tablename: the name of a table
            aux: additional lines to be included int he command

        Returns:
            A string representing the sql command for creating the table in question
        """
        sql_cmd_lines = ["CREATE TABLE IF NOT EXISTS %s (" % tablename]
        comma_separated_lines = []
        for field in self.tablename_to_fieldtotype[tablename].keys():
            line = "%s %s" % (field, FIELD_TYPES.to_string(
                self.tablename_to_fieldtotype[tablename][field]))
            if field in self.tablename_to_requiredfields[tablename]:
                line += " NOT NULL"
            comma_separated_lines.append(line)
        if tablename in self.tablename_to_aux:
            comma_separated_lines.append(self.tablename_to_aux[tablename])
        content = ", ".join(comma_separated_lines)
        sql_cmd_lines += [content, ")"]
        return "".join(sql_cmd_lines)

    def process_for_sorting(self, item, (table, field)):
        """Processes the item so that it is in an order-friendly form."""
        return item
