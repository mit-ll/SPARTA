# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Test database class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Sep 2013   SY             Original version
# *****************************************************************

import math

### NOTE: this is NOT an actual database class.
### It handles string representation only.

class TestDatabase(object):
    """Handles TA1 test database representation.

    Attributes:
        short_database_names: a dictionary mapping (num_records, record_size)
            to a database nickname
        db_num_records: the number of records in the test database
        db_record_size: the average record size in the test database
    """
    def __init__(self, short_database_names, db_num_records, db_record_size):
        """Initializes the TestDatabase with a dict of short database names,
        a number of records and a record size."""
        self.db_num_records = db_num_records
        self.db_record_size = db_record_size
        self._short_database_names = short_database_names
        self._database_name_template = "Database with %s Rows, Each of Size %s"

    def get_db_num_records_str(self):
        """Returns the string used to represent the number of records in the
        database"""
        log_db_num_records = math.log10(self.db_num_records)
        if int(log_db_num_records) == log_db_num_records:
            return "$10^{%s}$" % str(int(log_db_num_records))
        return str(self.db_num_records)

    def get_db_record_size_str(self):
        """Returns the string used to represent the database record size"""
        log_db_record_size = math.log10(self.db_record_size)
        if int(log_db_record_size) == log_db_record_size:
            return "$10^{%s}$B" % str(int(log_db_record_size))
        return str(self.db_record_size) + "B"

    def _get_database_name_from_template(self, template):
        """Returns the string used to refer to the database in question given
        a name tempalte.
        Args:
            template: a string with '%s' where the number of records and the
                record size should be.
        """
        return template % (
            self.get_db_num_records_str(),
            self.get_db_record_size_str())

    def get_database_name(self, lower=False):
        """Returns the string used to refer to the database in question.
        Args:
            lower: a boolean indicating whether lowercase is desired.
        """
        if not lower:
            return self._get_database_name_from_template(
                self._database_name_template)
        else:
            return self._get_database_name_from_template(
                self._database_name_template.lower())
    
    def get_short_database_name(self, lower=False):
        """Returns the short string used to refer to the database in question.
        Args:
            lower: a boolean indicating whether lowercase is desired.
        """
        if (self.db_num_records,
            self.db_record_size) not in self._short_database_names:
            return self.get_database_name(lower)
        else:
            nickname = self._short_database_names[
                (self.db_num_records, self.db_record_size)]
            if lower: return nickname.lower()
            else: return nickname

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return ((self.db_num_records == other.db_num_records)
                    and (self.db_record_size == other.db_record_size)
                    and (self.get_short_database_name()
                         == other.get_short_database_name()))
        else:
            return False
