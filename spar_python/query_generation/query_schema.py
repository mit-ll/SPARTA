# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Jill
#  Description:        Constants for query generation.
# *****************************************************************

import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)
import spar_python.common.enum as enum                                                                              
 
                                                                                                                                                        
CAT =        enum.Enum('EQ',
                       'EQ_FISHING_INT',
                       'EQ_FISHING_STR',
                       'P1_EQ_AND',
                       'P1_EQ_OR',
                       'P1_EQ_DNF',
                       'P1_EQ_CNF',
                       'P1_EQ_DEEP',
                       'P1_EQ_NOT',
                       'P1_OTHER_AND',
                       'P1_OTHER_OR',
                       'P2_RANGE',
                       'P2_RANGE_FOO',
                       'P2_LESS',
                       'P2_GREATER',
                       'P2_GREATER_FOO',
                       'P3',
                       'P4',
                       'P6_INITIAL_ONE',
                       'P6_MIDDLE_ONE',
                       'P6_FINAL_ONE',
                       'P7_INITIAL',
                       'P7_BOTH',
                       'P7_FINAL',
                       'P7_OTHER_1',
                       'P7_OTHER_2',
                       'P7_OTHER_3',
                       'P7_OTHER_4',
                       'P7_OTHER_5',
                       'P7_OTHER_6',
                       'P7_OTHER_7',
                       'P7_OTHER_8',
                       'P7_OTHER_9',
                       'P7_OTHER_10',
                       'P7_OTHER_11',
                       'P7_OTHER_12',
                       'P7_OTHER_13',
                       'P7_OTHER_14',
                       'P7_OTHER_15',
                       'P7_OTHER_16',
                       'P7_OTHER_17',
                       'P8_EQ',
                       'P8_OTHER',
                       'P9_EQ',
                       'P9_ALARM_WORDS',
                       'P9_OTHER',
                       'P11_SHORT',
                       'P11_FULL')                                                           
                                                                                                  
                                                                                                                                                                                                                                            

FIELD_TYPES = enum.Enum("TEXT", "INTEGER", "REAL", "BOOL", "LIST", "MANY")

### Common Fields ###
QRY_ENUM = 'enum'
QRY_CAT = "category"
QRY_SUBCAT = "sub_category"
QRY_PERF = 'perf'
QRY_DBNUMRECORDS = "db_num_records"
QRY_DBRECORDSIZE = "db_record_size"
QRY_QID = "qid"
QRY_WHERECLAUSE = "where_clause"
QRY_FIELD = "field"
QRY_FIELDTYPE = "field_type"
QRY_QUERIES = "queries"
QRY_LRSS = 'r_lower'
QRY_URSS = 'r_upper'
QRY_RSS = 'rss'
QRY_VALID = 'valid'
### EQ ###
QRY_VALUE = "value"
QRY_NEGATE = "negate"

### Ranges ###
QRY_LBOUND = "lbound"
QRY_UBOUND = "ubound"
QRY_RANGECOVERAGE = "range_coverage"
QRY_RANGE = "range"
QRY_RANGEEXPL = "r_exp_lower"
QRY_RANGEEXPU = 'r_exp_upper'
QRY_TYPE = 'type'
QRY_RANGEEXP = 'range_exp'
### Searches ###
QRY_KEYWORDLEN = "keyword_len"
QRY_SEARCHFOR = "search_for"
QRY_SEARCHFORLIST = 'search_for_list'
QRY_SEARCHDELIMNUM = 'search_delim_num'

### p1 ###
QRY_NUMCLAUSES = 'num_clauses'
QRY_NUMTERMSPERCLAUSE = 'num_terms_per_clause'
QRY_FTMLOWER = 'ftm_lower'
QRY_FTMUPPER = 'ftm_upper'
QRY_SUBBOBS = 'sub_bobs'
# for P1_and
QRY_NUMRECORDSMATCHINGFIRSTTERM = 'num_records_matching_first_term'
# for P1_or
QRY_SUMRECORDSMATCHINGEACHTERM = 'sum_records_matching_each_term'
# for P1_eq_not a list of which terms are negated (zero based)
QRY_NEGATEDTERMS = 'negated_terms'

### p8 & p9 ###
QRY_N = "n_value"
QRY_M = "m_value"
QRY_MATCHINGRECORDCOUNTS = 'matching_record_counts'
QRY_FIRSTALARMWORD = 'first_alarm_word'
QRY_SECONDALARMWORD = 'second_alarm_word'
QRY_DISTANCELIST = 'distance_list'

QRY_ALARMWORDONE = 'alarmword1'
QRY_ALARMWORDTWO = 'alarmword2'
QRY_ALARMWORDDISTANCE = 'alarmword_distance'
QRY_MATCHINGROWIDANDDISTANCES = 'alarmword_matching_row_id_and_distances'

### P11 ###
QRY_XPATH = 'xpath'

### Fields used for query aggregator results ###
QRY_FISHING_MATCHES_FOUND = 'fishing_matches_found'
QRY_SUBRESULTS = 'subresults'


QRY_FIELDS_TO_TYPES = {
    QRY_CAT: FIELD_TYPES.TEXT,
    QRY_SUBCAT: FIELD_TYPES.TEXT,
    QRY_DBNUMRECORDS: FIELD_TYPES.INTEGER,
    QRY_DBRECORDSIZE: FIELD_TYPES.INTEGER,
    QRY_QID: FIELD_TYPES.INTEGER,
    QRY_WHERECLAUSE: FIELD_TYPES.TEXT,
    QRY_FIELD: FIELD_TYPES.TEXT,
    QRY_FIELDTYPE: FIELD_TYPES.TEXT,
    QRY_QUERIES: FIELD_TYPES.LIST,
    QRY_VALUE: FIELD_TYPES.MANY,
    QRY_NEGATE: FIELD_TYPES.BOOL,
    QRY_LBOUND: FIELD_TYPES.MANY,
    QRY_UBOUND: FIELD_TYPES.MANY,
    QRY_RANGECOVERAGE: FIELD_TYPES.REAL,
    QRY_RANGE: FIELD_TYPES.INTEGER,
    QRY_KEYWORDLEN: FIELD_TYPES.INTEGER,
    QRY_SEARCHFOR: FIELD_TYPES.TEXT,
    QRY_NUMRECORDSMATCHINGFIRSTTERM: FIELD_TYPES.INTEGER,
    QRY_NEGATEDTERMS: FIELD_TYPES.INTEGER,
    QRY_NUMCLAUSES: FIELD_TYPES.INTEGER,
    QRY_NUMTERMSPERCLAUSE: FIELD_TYPES.INTEGER,
    QRY_N: FIELD_TYPES.INTEGER,
    QRY_M: FIELD_TYPES.INTEGER,
    QRY_FISHING_MATCHES_FOUND: FIELD_TYPES.INTEGER}
 
 
