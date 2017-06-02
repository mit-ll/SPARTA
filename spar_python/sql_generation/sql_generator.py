import collections
import argparse
import MySQLdb
import logging
import csv

import sys
import os
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.data_generation.spar_variables as sv

LOGGER = logging.getLogger(__name__)
# NOTE(njhwang) The constants below are system dependent. These are for Ubuntu
# 12.04 64-bit.
# CHAR/VARCHARs should be no longer than this (should otherwise be TEXT)
MAX_CHAR_LENGTH = 500
# TEXT fields get set to this length automatically in MariaDB
MAX_TEXT_LENGTH = 65535
# Max BLOB sizes
MAX_SMALL_BLOB_LENGTH = 65535
MAX_MEDIUM_BLOB_LENGTH = 16777215
# Define all numeric types that could be unsigned
# TODO(njhwang) should eventually support all data types (INTEGER, REAL)
UNSIGNED_NUMERIC_TYPES = ['TINYINT', 'SMALLINT', 'INT', 'BIGINT', 'FLOAT',
                          'DOUBLE']
# Define some things constant for SPAR tables
TABLE_CONSTS = {'base' : {'key' : 'id', 'partitions' : 5},
                'notes' : {'key' : 'id', 'partitions' : 10},
                'fingerprint' : {'key' : 'id', 'partitions' : 100},
                'keywords' : {'key' : 'id', 'partitions' : 10},
                'stems' : {'key' : 'id', 'partitions' : 10},
                'alarms' : {'key' : 'id', 'partitions' : 10},
                'row_hashes' : {'key' : 'id', 'partitions' : 1}}

def make_expanded_path(file_name):
    ''' Helper function to expand file/directory paths.'''
    if file_name:
        file_name = os.path.realpath( \
                    os.path.normpath( \
                    os.path.expanduser( \
                    os.path.expandvars(file_name))))
    return file_name

def get_database_connection(db_host, db_user, db_pass, db_name):
    '''Helper function to establish database connection.'''
    return MySQLdb.connect(host = db_host, 
                           user = db_user, 
                           passwd = db_pass,
                           db = db_name)

class SQLGenerator():
    '''Generate SQL create statements based on a database schema CSV file'''

    def __init__(self, schema_file_name):
        '''Initialize common objects and variables.'''
        # Validate inputs
        assert os.path.isfile(schema_file_name), \
            '%s is not a valid file' % schema_file_name

        # Parse schema file
        self.schema = collections.OrderedDict()
        self.field_order = collections.OrderedDict()
        self.__parse_csv(schema_file_name)

        # Populate enum information
        self.__enums = dict()
        self.__fill_enums()

    # TODO(njhwang) Write unit tests for this
    def __fill_enums(self):
        '''Fill the enum variables with the list of values from
        spar_variables.'''

        for num in sv.ENUM_VARS:
            values_list = []
            (sql_name, sql_type) = sv.sql_info[num]
            for value in sv.VAR_TO_ENUM[num].values_generator():
                values_list.append('\'%s\''% value)
            self.__enums[sql_name] = values_list

    # TODO(njhwang) Write unit tests for this
    def __parse_csv(self, file_name):
        '''Read the CSV file and convert the data to an internal format.'''

        # Validate starting state and input options
        assert len(self.schema) == 0, 'Schema has already been parsed.'
        try:
            file_handle = open(file_name, 'r')
        except IOError:
            LOGGER.error('Could not open input file %s', file_name)
            sys.exit(1)

        # Parse CSV file
        # Resulting data structure is an OrderedDict with table names as keys.
        # Each value in the OrderedDict is another OrderedDict with column names
        # as keys and column information as values.
        csv_reader = csv.DictReader(file_handle)
        for row in csv_reader:
            tables = row.pop('table').split(':')
            col = row.pop('name')
            self.field_order[col] = tables
            for table in tables:
                assert table in TABLE_CONSTS
                if table not in self.schema:
                    self.schema[table] = collections.OrderedDict()
                else:
                    assert col not in self.schema[table], \
                        '%s already in schema for %s' % (col, table)
                # Length is best handled as an integer
                row['length'] = int(row['length'])
                # Do some quick sanity checks on the schema row
                if row['length'] > 0:
                    # TODO(njhwang) should eventually support all field types
                    # BINARY, VARBINARY, TINYBLOB/TEXT, BLOB, MEDIUMTEXT,
                    # LONGBLOB/TEXT
                    assert row['type'] == 'CHAR' or \
                           row['type'] == 'VARCHAR' or \
                           row['type'] == 'TEXT' or \
                           row['type'] == 'MEDIUMBLOB' or \
                           row['type'] == 'BLOB'
                    if row['type'] == 'CHAR' or row['type'] == 'VARCHAR':
                        assert row['length'] <= MAX_CHAR_LENGTH
                    # MariaDB will set any TEXT and BLOB lengths to maximal
                    # values, so account for that on the internal representation
                    elif row['type'] == 'BLOB':
                        assert row['length'] <= MAX_SMALL_BLOB_LENGTH
                        row['length'] = MAX_SMALL_BLOB_LENGTH
                    elif row['type'] == 'MEDIUMBLOB':
                        assert row['length'] <= MAX_MEDIUM_BLOB_LENGTH
                        row['length'] = MAX_MEDIUM_BLOB_LENGTH
                    elif row['type'] == 'TEXT':
                        assert row['length'] <= MAX_TEXT_LENGTH
                        row['length'] = MAX_TEXT_LENGTH
                self.schema[table][col] = row

    # TODO(njhwang) Write unit tests for this
    def generate_create_sql(self):
        '''Generate create table SQL strings from internal structure.'''

        assert len(self.schema) > 0, 'Schema file does not appear to have ' + \
                                     'been parsed yet.'

        sql_syntax = ''
        notes_flag = False

        # Goes through each table in self.schema and generates creation syntax
        for table in self.schema:
            create_table_flag = False
            col_list = []
            for col in self.schema[table]:
                col_info = self.schema[table][col]
                col_str = ['  %s'% col]
                if col_info['type'] == 'ENUM':
                    if col in self.__enums.keys():
                        col_str.append(' ENUM(%s)' % \
                                       ', '.join(self.__enums[col]))
                    else:
                        LOGGER.error('Values for ENUM %s are not defined.', col)
                        sys.exit(1)
                # Length specification only required for CHAR/VARCHAR
                # TODO(njhwang) Would specifying lengths for numeric types
                # improve baseline performance at all?
                elif col_info['type'] == 'CHAR' or \
                     col_info['type'] == 'VARCHAR':
                    col_str.append(' %s'% col_info['type'])
                    col_str.append('(%s)'% col_info['length'])
                else:
                    col_str.append(' %s'% col_info['type'])
                if col == 'id':
                    # The id field is special, add snowflakes
                    col_str.append(' NOT NULL')
                else:
                    create_table_flag = True
                if table == 'notes' and col_info['index'] == 'true':
                    # If notes are indexed for keywords/stems, we'll tack on
                    # those tables to the end
                    notes_flag = True
                col_list.append(''.join(col_str))
            if create_table_flag:
                sql_syntax += 'CREATE TABLE IF NOT EXISTS %s (\n' % table
                sql_syntax += ',\n'.join(col_list)
                sql_syntax += ('\n) ENGINE = MYISAM PARTITION BY KEY(%s) '
                               'PARTITIONS %i;\n\n') % \
                              (TABLE_CONSTS[table]['key'], 
                               TABLE_CONSTS[table]['partitions'])

        if notes_flag:
            # Add notes field index tables
            notes_index_syntax = """CREATE TABLE IF NOT EXISTS keywords (
  id BIGINT UNSIGNED NOT NULL,
  col CHAR(30) NOT NULL,
  word CHAR(30) NOT NULL
) ENGINE = MyISAM PARTITION BY KEY(id) PARTITIONS 10;

CREATE TABLE IF NOT EXISTS stems (
  id BIGINT UNSIGNED NOT NULL,
  col CHAR(30) NOT NULL,
  word CHAR(30) NOT NULL
) ENGINE = MyISAM PARTITION BY KEY(id) PARTITIONS 10;

CREATE TABLE IF NOT EXISTS alarms (
  id BIGINT UNSIGNED NOT NULL,
  word1 CHAR(30) NOT NULL,
  word2 CHAR(30) NOT NULL,
  field CHAR(30) NOT NULL,
  distance INT NOT NULL 
) ENGINE = MyISAM PARTITION BY KEY(id) PARTITIONS 10;
"""
            sql_syntax += notes_index_syntax

        return sql_syntax

    # TODO(njhwang) Not sure how to write unit tests for this
    def generate_index_view_sql(self, db_conn, db_name):
        '''Generate create index and view SQL strings from internal 
           structure.
           
           Expects a database to be accessible via the MySQL API. This method
           checks that indices that already exist are not re-created, and that
           the main view is dropped if it already exists.'''

        # Validate starting state and input options
        assert len(self.schema) > 0, 'Schema file does not appear to have ' + \
                                     'been parsed yet.'
        assert 'base' in self.schema
        assert db_conn
        assert db_name

        # TODO(njhwang) Best way to confirm db_conn is up and running?
        # db_conn.sqlstate? db_conn.stat?  

        # Obtain database cursor
        curs = db_conn.cursor(MySQLdb.cursors.DictCursor)

        actual_schema = collections.OrderedDict()
        # Determine existing tables and their associated column info
        # actual_schema will have nearly the same structre as self.schema (with
        # the exception of the 'index' field from self.schema)
        num_results = curs.execute( \
                'SHOW FULL TABLES WHERE Table_type = \'BASE TABLE\'')
        tables = [result['Tables_in_%s' % db_name] for result in \
                  curs.fetchmany(num_results)]
        for table in tables:
            if table in TABLE_CONSTS:
                actual_schema[table] = collections.OrderedDict()
                # Note that 'DESCRIBE <table>' is dangerous, as the order in
                # which it returns rows is undefined; this command guarantees
                # the row order is the same as that specified by the CREATE
                # command 
                num_results = curs.execute( \
                    """SELECT * FROM information_schema.COLUMNS WHERE
                       TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY
                       ORDINAL_POSITION""",
                    (db_name, table))
                cols = curs.fetchmany(num_results)
                for col in cols:
                    col_name = col['COLUMN_NAME'].lower()
                    actual_schema[table][col_name] = {}
                    col_type = col['DATA_TYPE'].upper()
                    # Information on whether the field is unsigned is only in
                    # the 'COLUMN_TYPE' column
                    if col_type in UNSIGNED_NUMERIC_TYPES:
                        if 'unsigned' in col['COLUMN_TYPE'].lower():
                            col_type = col_type + ' UNSIGNED'
                    actual_schema[table][col_name]['type'] = col_type
                    col_length = col['CHARACTER_OCTET_LENGTH']
                    # Set col_length to 0 if it wasn't specified (i.e., for
                    # numeric types) or if the type is ENUM (which the SPAR
                    # database schema doesn't specify a length for)
                    if not col_length or col_type == 'ENUM':
                        col_length = 0
                    actual_schema[table][col_name]['length'] = col_length
            else:
                LOGGER.warning('Unrecognized table %s found in %s '
                               'while determining existing tables.' % \
                               (table, db_name))

        # Make sure internal schema matches actual schema
        kw_stems_present = False
        for table in self.schema:
            assert table in actual_schema
            for col in self.schema[table]:
                assert col in actual_schema[table]
                for field in self.schema[table][col]:
                    if field == 'index':
                        if self.schema[table][col][field] == 'true':
                            kw_stems_present = True
                    else:
                        assert self.schema[table][col][field] == \
                               actual_schema[table][col][field]
        # 'keywords' and 'stems' tables should be present if any field had
        # 'index' set to 'true'
        if kw_stems_present:
            assert 'keywords' in actual_schema
            assert 'stems' in actual_schema

        # Determine existing indices on all tables
        indexed_cols = {}
        for table in actual_schema:
            assert table not in indexed_cols
            indexed_cols[table] = []
            num_results = curs.execute('SHOW INDEXES IN %s' % table)
            indices = curs.fetchmany(num_results)
            for index in indices:
                indexed_cols[table].append(index['Key_name'])

        sql_syntax = ''

        # Create any required indices on base table
        for col in self.schema['base']:
            if col in indexed_cols['base']:
                LOGGER.info('Index on base.%s already exists. Skipping.' % col)
            elif col == 'id':
                sql_syntax += 'CREATE UNIQUE INDEX id ON base(id);\n\n'
            # TODO(njhwang) how do we want to index the xml column? Currently a
            # TEXT field that should not be indexed
            elif col != 'xml':
                sql_syntax += 'CREATE INDEX %s ON base(%s);\n\n' % (col, col)

        # Create any required indices on notes table
        if 'notes' in self.schema:
            if 'id' in indexed_cols['notes']:
                LOGGER.info('Index on notes.id already exists. Skipping.')
            else:
                sql_syntax += 'CREATE UNIQUE INDEX id ON notes(id);\n\n'

        # Create any required indices on fingerprint table
        if 'fingerprint' in self.schema:
            if 'id' in indexed_cols['fingerprint']:
                LOGGER.info('Index on fingerprint.id already exists. Skipping.')
            else:
                sql_syntax += 'CREATE UNIQUE INDEX id ON fingerprint(id);\n\n'

        # Create any required indices on row_hashes table
        if 'row_hashes' in self.schema:
            if 'id' in indexed_cols['row_hashes']:
                LOGGER.info('Index on row_hashes.id already exists. Skipping.')
            else:
                sql_syntax += 'CREATE UNIQUE INDEX id ON row_hashes(id);\n\n'

        # Create any required indices on keywords/stems tables
        kw_tables = ['keywords', 'stems']
        for table in kw_tables:
            if table in actual_schema:
                if 'id' in indexed_cols[table]:
                    LOGGER.info('Index on %s.id already exists. Skipping.' % \
                                table)
                else:
                    sql_syntax += 'CREATE INDEX id ON %s(id);\n\n' % table
                if 'word_col' in indexed_cols[table]:
                    LOGGER.info('Index on %s.word_col already exists. '
                                'Skipping.' % table)
                else:
                    # Note that while word, column combo is guaranteed to be
                    # unique, we can't create a unique index on it as these
                    # columns aren't part of the partition function.
                    sql_syntax += ('CREATE INDEX word_col ON '
                                  '%s(word, col);\n\n') % table

        # Determine existing views
        num_results = curs.execute( \
            'SHOW FULL TABLES WHERE TABLE_TYPE LIKE \'%VIEW%\'')
        views = [result['Tables_in_%s' % db_name] for result in \
                  curs.fetchmany(num_results)]

        notes_in_view = False
        fprint_in_view = False

        # If 'main' view already exists, drop it
        if 'main' in views:
            sql_syntax += 'DROP VIEW main;\n\n'

        # Create the 'main' view
        sql_syntax += 'CREATE VIEW main AS SELECT '
        for field in self.field_order:
            if 'base' in self.field_order[field]:
                sql_syntax += 'b.%s, ' % field
            elif 'notes' in self.field_order[field]:
                notes_in_view = True
                sql_syntax += 'n.%s, ' % field
            elif 'fingerprint' in self.field_order[field]:
                fprint_in_view = True
                sql_syntax += 'f.%s, ' % field
            else:
                assert 'row_hashes' in self.field_order[field]
        assert sql_syntax.endswith(', ')
        sql_syntax = sql_syntax[:-2]
        sql_syntax += ' FROM base AS b'
        if notes_in_view:
            sql_syntax += ' JOIN notes AS n ON b.id = n.id'
        if fprint_in_view:
            sql_syntax += ' JOIN fingerprint AS f ON b.id = f.id'

        return sql_syntax


def main():
    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                  'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                  'CRITICAL': logging.CRITICAL}

    # Define command line arguments
    parser = argparse.ArgumentParser()

    # NOTE(njhwang) This would use add_mutually_exclusive_group, but argparse
    # currently doesn't have support for group naming and description for a
    # mutually exclusive group. Determined it was less confusing for the user if
    # we manually check for mutual exclusion so the command-line help is
    # clearer.
    group = parser.add_argument_group('SQL generation selection',
            'Only one of -c/--create-sql or -i/--index-view-sql should be '
            'selected. This is to prevent users from piping the output of this '
            'script directly to a SQL database when both options are enabled, '
            'as indexing and view creation should typically occur after a '
            'database has been completely populated.')
    group.add_argument('-c', '--create-sql', dest = 'create_sql',
          action = 'store_true', default = False,
          help = 'Enable generation of table creation syntax')
    group.add_argument('-i', '--index-view-sql', dest = 'index_view_sql',
          action = 'store_true', default = False,
          help = 'Enable generation of index and view creation syntax')

    group = parser.add_argument_group('general arguments')
    group.add_argument('-s', '--schema', dest = 'schema',
           type = str, required = True, help = 'CSV schema file to import')
    group.add_argument('--log-level', dest = 'log_level', default = 'INFO',
          type = str, choices = log_levels.keys(),
          help = 'Only output log messages with the given severity or '
                 'above')

    group = parser.add_argument_group('table creation arguments', 
            'Only need to be specified if -c/--create-sql is specified.')
    group.add_argument('--create-file', dest = 'create_file',
          type = str, help = 'Output file for table creation syntax')

    group = parser.add_argument_group('index and view creation arguments', 
            'Only need to be specified if -i/--index-view-sql is specified. '
            'Note that index and view creation requires access to an existing '
            'database to check for existing indices and views.')
    group.add_argument('--index-view-file', dest = 'index_view_file',
          type = str, help = 'Output file for index and view creation syntax')
    group.add_argument('-D', '--db-name', dest = 'db_name',
          type = str, help = 'MariaDB database')
    group.add_argument('--db-host', dest = 'db_host',
          type = str, default = 'localhost', help = 'MariaDB database host')
    group.add_argument('-u', '--db-user', dest = 'db_user',
          type = str, help = 'MariaDB database user')
    # TODO(njhwang) What if there isn't a password to database? Will this work?
    group.add_argument('-p', '--password', '--passwd', dest = 'db_pass',
          type = str, help = 'MariaDB database password')

    options = parser.parse_args()

    # Update input options that may require path expansion
    options.schema = make_expanded_path(options.schema)
    options.create_file = make_expanded_path(options.create_file)
    options.index_view_file = make_expanded_path(options.index_view_file)

    # Validate input options
    assert options.create_sql ^ options.index_view_sql, \
        'Only one of -c/--create-sql or -i/--index-view-sql can be specified'
    assert os.path.isfile(options.schema), \
        '%s is not a valid file' % options.schema
    if options.create_file:
        assert os.path.isdir(os.path.dirname(options.create_file)), \
            '%s is not a valid destination' % options.create_file
    if options.index_view_file:
        assert os.path.isdir(os.path.dirname(options.index_view_file)), \
            '%s is not a valid destination' % options.index_view_file
    if options.index_view_sql:
        assert options.db_name, \
            '-D/--db-name must be specified with -i/--index-view-sql'
        assert options.db_user, \
            '-u/--db-user must be specified with -i/--index-view-sql'
        assert options.db_pass, \
            '-p/--db-pass must be specified with -i/--index-view-sql'

    # Update logging level
    logging.basicConfig(level = log_levels[options.log_level],
                        format = '%(levelname)s: %(message)s')

    # Generate SQL output (or files, if specified)
    generator = SQLGenerator(options.schema)
    disclaimer = '# Autogenerated by sql_generator.py. DO NOT EDIT\n\n'

    if options.create_sql:
        create_syntax = generator.generate_create_sql()
        if options.create_file:
            try:
                sql_file = open(options.create_file, 'w')
            except IOError:
                LOGGER.error('Could not open output file %s',
                             options.create_file)
                sys.exit(1)
            sql_file.write(disclaimer)
            sql_file.write(create_syntax)
            sql_file.close()
        else:
            print create_syntax

    if options.index_view_sql:
        db_conn = get_database_connection(options.db_host,
                                          options.db_user,
                                          options.db_pass,
                                          options.db_name)
  
        index_view_syntax = \
            generator.generate_index_view_sql(db_conn, options.db_name)
        if options.index_view_file:
            try:
                sql_file = open(options.index_view_file, 'w')
            except IOError:
                LOGGER.error('Could not open output file %s',
                             options.index_view_file)
                sys.exit(1)
            sql_file.write(disclaimer)
            sql_file.write(index_view_syntax)
            sql_file.close()
        else:
            print index_view_syntax
        db_conn.close()

if __name__ == "__main__":
    main()
