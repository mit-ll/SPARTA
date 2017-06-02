# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Utilities for test generation
# *****************************************************************

import sys
import os
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.report_generation.ta1.ta1_schema as rdb
import spar_python.data_generation.spar_variables as sv


HI_ENTROPY_FIELDS = [sv.enum_to_sql_name(sv.VARS.SSN),
                     sv.enum_to_sql_name(sv.VARS.STREET_ADDRESS),
                     sv.enum_to_sql_name(sv.VARS.ZIP_CODE)]

HI_ENTROPY_FIELD_VALUES = {sv.enum_to_sql_name(sv.VARS.SSN) :
                           ['111111111', '222222222', '333333333'],
                           sv.enum_to_sql_name(sv.VARS.STREET_ADDRESS) :
                           ['123 Fake St', 
                            '103 Xxx Yyyy St', 
                            '9999 Pizza Pie Rd'],
                           sv.enum_to_sql_name(sv.VARS.ZIP_CODE) :
                           ['aaaaa', 'bbbbb', 'ccccc']}

class IDGenerator(object):
    '''
    Used to create a unique number for the .ts filenames
    Currently it will make a 5 digit number.
    '''
    def __init__(self, start_val=0):
        self.__id = start_val

    def get_id(self):
        self.__id = self.__id + 1
        return "%05d" % self.__id
        
def make_expanded_path(path):
    '''
    Expands a path for ~ and environment variables, normalizes it
    and follows symlinks.
    e.g. "~me/$foo/test1" -> "/home/me/aaa/bbb/test1" 
    '''
    if path:
        return os.path.realpath( \
            os.path.normpath( \
                os.path.expanduser( \
                    os.path.expandvars(path))))
    else:
        return path

def callback_for_list_options(option, opt, value, parser):
    ''' used for list options'''
    setattr(parser.values, option.dest, value.split(','))

def get_dbsize_string(db_record_size, db_num_records):
    ''' 
    Single method to create the db size string which is used
    by the .ts and .q files
    '''
    ROWS_SUFFIX = 'rows'
    RECORDS_SUFFIX = 'Bpr'
    PREFIX_MAP = {'100':'100', '1000':'1k', '100000':'100k', '1000000':'1M',
                  '100000000':'100M', '1000000000':'1B'}
    # TODO(jill) this check should be more robust; should individually check for
    # invalid record sizes and invalid number of records
    assert str(db_num_records) in PREFIX_MAP and \
           str(db_record_size) in PREFIX_MAP, ('Combination of %srows and ' + \
             '%sBpr is not a valid test database configuration') % \
               (db_num_records, db_record_size)
    dbsize = '_'.join([PREFIX_MAP[str(db_num_records)] + ROWS_SUFFIX, 
                       PREFIX_MAP[str(db_record_size)] + RECORDS_SUFFIX])
    return dbsize

def get_db_size(resultdb):
    '''
    Get the record size and number of records for the database 
    DBF_RECORDSIZE = "db_record_size"
    DBF_NUMRECORDS = "db_num_records"
    '''
    # pull it from the first entry in the full queries table.
    # we are assuming that the result database is only for one database size
    resultdb._execute("SELECT " + rdb.DBF_RECORDSIZE + ", " + \
                          rdb.DBF_NUMRECORDS + " FROM " + rdb.DBF_TABLENAME)
    results_tuple = resultdb._fetchone()
    assert results_tuple, 'Could not fetch any results from full_queries table'
    (record_size, num_records) = results_tuple

    return (record_size, num_records)
