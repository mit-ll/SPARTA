# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Constants for TA1 analytics.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  Earlier       NH             Original Version
#  16 May 2013   SY
#  6 June 2013   MZ             Schema update
#  3 Aug 2013    SY             Another schema update
# *****************************************************************

# SPAR imports:
import spar_python.common.enum as enum
from spar_python.report_generation.common.results_schema import *

DBF_ALIAS1 = "dbf1"
DBF_ALIAS2 = "dbf2"

# field types in the results database:
FIELD_TYPES = enum.Enum("TEXT", "INTEGER", "REAL", "BOOL")
# field types in the test database:
TEST_FIELD_TYPES = enum.Enum("integer", "string", "enum", "date")

CATEGORIES = enum.Enum(
    "EQ", "P1", "P2", "P3", "P4", "P6", "P7", "P8", "P9", "P11")

MODS_CATEGORIES = enum.Enum("insert", "delete", "update")

ATOMIC_CATEGORIES = [CATEGORIES.EQ,
                     CATEGORIES.P2,
                     CATEGORIES.P3,
                     CATEGORIES.P4,
                     CATEGORIES.P6,
                     CATEGORIES.P7,
                     CATEGORIES.P11]

SELECTION_COLS = ["*", "id"]

SUBCATEGORIES = {
    CATEGORIES.P1: enum.Enum("eqand", "eqor", "eqdnf", "eqdeep",
                             "eqcnf", "eqnot", "otherand", "otheror",
                             "otheribm"),
    CATEGORIES.P2: enum.Enum("range", "less", "greater"),
    CATEGORIES.P6: enum.Enum("initialone", "middleone", "finalone",
                             #"middlemany"
                             ),
    CATEGORIES.P7: enum.Enum("initial", "both", "final", "other"),
    CATEGORIES.P8: enum.Enum("eq", "other"),
    CATEGORIES.P9: enum.Enum("eq", "alarmwords", "other"),
    CATEGORIES.P11: enum.Enum("eqfull", "eqdoubleslash",
                              "rangefull", "rangedoubleslash")}
SUBSUBCATEGORIES = {
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqcnf): range(1, 9),
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqdeep): range(1, 9),
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqnot): range(1, 7),
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].otheribm): range(1, 3),
    (CATEGORIES.P7, SUBCATEGORIES[CATEGORIES.P7].other): range(1, 18),
    (CATEGORIES.P8, SUBCATEGORIES[CATEGORIES.P8].other): range(1, 7),
    (CATEGORIES.P9, SUBCATEGORIES[CATEGORIES.P9].other): range(1, 7)}

# category names:

CATEGORY_NAMES = {
    CATEGORIES.EQ: "Equality",
    CATEGORIES.P1: "Boolean",
    CATEGORIES.P2: "Range",
    CATEGORIES.P3: "Keyword",
    CATEGORIES.P4: "Stemming",
    CATEGORIES.P6: "Wildcard Search",
    CATEGORIES.P7: "Subsequence Search",
    CATEGORIES.P8: "Threshold",
    CATEGORIES.P9: "Ranking",
    CATEGORIES.P11: "XML"}

CATEGORY_AND_SUBCATEGORY_NAMES = {
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqand):
    "Conjunctions of Equalities",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqor):
    "Disjunctions of Equalities",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqdnf):
    "Disjunctions of Conjunctions of Equalities",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqcnf):
    "Conjunctions of Disjunctions of Equalities",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqdeep):
    "Boolean Formulas of Depth Greater than Two",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].eqnot):
    "Boolean Formulas of Equalities Containing Negations",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].otherand):
    "Conjunctions of Other Query Types",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].otheror):
    "Disjunctions of Other Query Types",
    (CATEGORIES.P1, SUBCATEGORIES[CATEGORIES.P1].otheribm):
    "Conjunctions of one or two Equalities and a Range Query",
    (CATEGORIES.P2, SUBCATEGORIES[CATEGORIES.P2].range):
    "Two-Sided Range Queries",
    (CATEGORIES.P2, SUBCATEGORIES[CATEGORIES.P2].greater):
    "Greater-Than Range Queries",
    (CATEGORIES.P2, SUBCATEGORIES[CATEGORIES.P2].less):
    "Less-Than Range Queries",
    (CATEGORIES.P8, SUBCATEGORIES[CATEGORIES.P8].eq):
    "Threshold Queries over Equalities",
    (CATEGORIES.P8, SUBCATEGORIES[CATEGORIES.P8].other):
    "Threshold Queries over Other Query Types",
    (CATEGORIES.P9, SUBCATEGORIES[CATEGORIES.P9].eq):
    "Ranking Queries over Equalities",
    (CATEGORIES.P9, SUBCATEGORIES[CATEGORIES.P9].other):
    "Ranking Queries over Other Query Types",
    (CATEGORIES.P11, SUBCATEGORIES[CATEGORIES.P11].eqfull):
    "Full XML Equality Queries",
    (CATEGORIES.P11, SUBCATEGORIES[CATEGORIES.P11].rangefull):
    "Full XML Range Queries",
    (CATEGORIES.P11, SUBCATEGORIES[CATEGORIES.P11].eqdoubleslash):
    "Leaf Node XML Equality Queries",
    (CATEGORIES.P11, SUBCATEGORIES[CATEGORIES.P11].rangedoubleslash):
    "Leaf Node XML Range Queries"}

# indicates which atomic categories are applicable to which test field types:
CATEGORY_TO_FIELDS = {
    CATEGORIES.EQ: TEST_FIELD_TYPES.numbers_list(),
    CATEGORIES.P2: TEST_FIELD_TYPES.numbers_list(),
    CATEGORIES.P3: [TEST_FIELD_TYPES.string],
    CATEGORIES.P4: [TEST_FIELD_TYPES.string],
    CATEGORIES.P6: [TEST_FIELD_TYPES.string],
    CATEGORIES.P7: [TEST_FIELD_TYPES.string],
    CATEGORIES.P11: [TEST_FIELD_TYPES.string]}

MOD_CATEGORIES = enum.Enum("insert", "delete", "update")

### FOR STORING RESULTS IN A DB ###
DBA_TABLENAME = "atomic_queries"
DBA_AQID = "aqid"
DBA_CAT = "category"
DBA_SUBCAT = "sub_category"
DBA_SUBSUBCAT = "sub_sub_category"
DBA_NUMRECORDS = "db_num_records"
DBA_RECORDSIZE = "db_record_size"
DBA_WHERECLAUSE = "where_clause"
DBA_NUMMATCHINGRECORDS = "num_matching_records"
DBA_FIELD = "field"
DBA_FIELDTYPE = "field_type"
DBA_KEYWORDLEN = "keyword_len"
DBA_RANGE = "range"
    
DBA_FIELDS_TO_TYPES = {
    DBA_AQID: FIELD_TYPES.INTEGER,
    DBA_CAT: FIELD_TYPES.TEXT,
    DBA_SUBCAT: FIELD_TYPES.TEXT,
    DBA_SUBSUBCAT: FIELD_TYPES.TEXT,
    DBA_NUMRECORDS: FIELD_TYPES.INTEGER,
    DBA_RECORDSIZE: FIELD_TYPES.INTEGER,
    DBA_WHERECLAUSE: FIELD_TYPES.TEXT,
    DBA_NUMMATCHINGRECORDS: FIELD_TYPES.INTEGER,
    DBA_FIELD: FIELD_TYPES.TEXT,
    DBA_FIELDTYPE: FIELD_TYPES.TEXT,
    DBA_KEYWORDLEN: FIELD_TYPES.INTEGER,
    DBA_RANGE: FIELD_TYPES.INTEGER}

DBA_REQUIRED_FIELDS = [
    DBA_AQID,
    DBA_CAT,
    DBA_NUMRECORDS,
    DBA_RECORDSIZE,
    DBA_WHERECLAUSE,
    DBA_NUMMATCHINGRECORDS,
    DBA_FIELD,
    DBA_FIELDTYPE]

DBF_TABLENAME = "full_queries"
DBF_FQID = "qid"
DBF_CAT = "category"
DBF_SUBCAT = "sub_category"
DBF_SUBSUBCAT = "sub_sub_category"
DBF_NUMRECORDS = "db_num_records"
DBF_RECORDSIZE = "db_record_size"
DBF_WHERECLAUSE = "where_clause"
DBF_P8M = "p8_m"
DBF_P8N = "p8_n"
DBF_P9MATCHINGRECORDCOUNTS = "p9_matching_record_counts"
DBF_NUMMATCHINGRECORDS = "num_matching_records"
DBF_MATCHINGRECORDIDS = "matching_record_ids"
DBF_MATCHINGRECORDHASHES = "matching_record_hashes"
DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM = "p1_and_num_records_matching_first_term"
DBF_P1ORSUMRECORDSMATCHINGEACHTERM = "p1_or_sum_records_matching_each_term"
DBF_P1NEGATEDTERM = "p1_negated_term"
DBF_P1NUMTERMSPERCLAUSE = "p1_num_terms_per_clause"
DBF_P1NUMCLAUSES = "p1_num_clauses"
DBF_P1DEPTH = "p1_depth"
DBF_REJECTINGPOLICIES = "rejecting_policies"
DBF_IBM1SUPPORTED = "supported_by_ibm_ta1"
DBF_IBM2SUPPORTED = "supported_by_ibm_ta2"
DBF_COLUMBIASUPPORTED = "supported_by_columbia"
DBF_SELECTSTAR = "run_in_select_star_mode"

DBF_FIELDS_TO_TYPES = {
    DBF_FQID: FIELD_TYPES.INTEGER,
    DBF_CAT: FIELD_TYPES.TEXT,
    DBF_SUBCAT: FIELD_TYPES.TEXT,
    DBF_SUBSUBCAT: FIELD_TYPES.TEXT,
    DBF_NUMRECORDS: FIELD_TYPES.INTEGER,
    DBF_RECORDSIZE: FIELD_TYPES.INTEGER,
    DBF_WHERECLAUSE: FIELD_TYPES.TEXT,
    DBF_P8M: FIELD_TYPES.INTEGER,
    DBF_P8N: FIELD_TYPES.INTEGER,
    DBF_P9MATCHINGRECORDCOUNTS: FIELD_TYPES.TEXT,
    DBF_NUMMATCHINGRECORDS: FIELD_TYPES.INTEGER,
    DBF_MATCHINGRECORDIDS: FIELD_TYPES.TEXT,
    DBF_MATCHINGRECORDHASHES: FIELD_TYPES.TEXT,
    DBF_P1ANDNUMRECORDSMATCHINGFIRSTTERM: FIELD_TYPES.INTEGER,
    DBF_P1ORSUMRECORDSMATCHINGEACHTERM: FIELD_TYPES.INTEGER,
    DBF_P1NEGATEDTERM: FIELD_TYPES.TEXT,
    DBF_P1NUMTERMSPERCLAUSE: FIELD_TYPES.INTEGER,
    DBF_P1NUMCLAUSES: FIELD_TYPES.INTEGER,
    DBF_P1DEPTH: FIELD_TYPES.INTEGER,
    DBF_REJECTINGPOLICIES: FIELD_TYPES.TEXT,
    DBF_IBM1SUPPORTED: FIELD_TYPES.BOOL,
    DBF_IBM2SUPPORTED: FIELD_TYPES.BOOL,
    DBF_COLUMBIASUPPORTED: FIELD_TYPES.BOOL,
    DBF_SELECTSTAR: FIELD_TYPES.BOOL}

DBF_REQUIRED_FIELDS = [
    DBF_FQID,
    DBF_CAT,
    DBF_NUMRECORDS,
    DBF_RECORDSIZE,
    DBF_WHERECLAUSE]

DBP_TABLENAME = "performer_queries"
DBP_FQID = "qid"
DBP_PERFORMERNAME = "performer"
DBP_TESTCASEID = "test_case_id"
DBP_SELECTIONCOLS = "selection_cols"
DBP_SENDTIME = "send_time"
DBP_RESULTSTIME = "results_time"
DBP_QUERYLATENCY = "query_latency"
DBP_EVENTMSGTIMES = "eventmsg_times"
DBP_EVENTMSGIDS = "eventmsg_ids"
DBP_EVENTMSGVALS = "eventmsg_vals"
DBP_NUMNEWRETURNEDRECORDS = "num_noncached_returned_records"
DBP_RETURNEDRECORDIDS = "returned_record_ids"
DBP_RETURNEDRECORDHASHES = "returned_record_hashes"
DBP_NUMTHREADS = "num_threads"
DBP_STATUS = "status"
DBP_CURRENTPOLICIES = "current_policies"
DBP_ISCORRECT = "correctness"
DBP_ISMODIFICATIONQUERY = "modification_query"
DBP_ISTHROUGHPUTQUERY = "throughput_query"

DBP_FIELDS_TO_TYPES = {
    DBP_FQID: FIELD_TYPES.INTEGER,
    DBP_PERFORMERNAME: FIELD_TYPES.TEXT,
    DBP_TESTCASEID: FIELD_TYPES.TEXT,
    DBP_SELECTIONCOLS: FIELD_TYPES.TEXT,
    DBP_SENDTIME: FIELD_TYPES.REAL,
    DBP_RESULTSTIME: FIELD_TYPES.REAL,
    DBP_QUERYLATENCY: FIELD_TYPES.REAL,
    DBP_EVENTMSGTIMES: FIELD_TYPES.TEXT,
    DBP_EVENTMSGIDS: FIELD_TYPES.TEXT,
    DBP_EVENTMSGVALS: FIELD_TYPES.TEXT,
    DBP_NUMNEWRETURNEDRECORDS: FIELD_TYPES.INTEGER,
    DBP_RETURNEDRECORDIDS: FIELD_TYPES.TEXT,
    DBP_RETURNEDRECORDHASHES: FIELD_TYPES.TEXT,
    DBP_NUMTHREADS: FIELD_TYPES.INTEGER,
    DBP_STATUS: FIELD_TYPES.TEXT,
    DBP_CURRENTPOLICIES: FIELD_TYPES.TEXT,
    DBP_ISCORRECT: FIELD_TYPES.BOOL,
    DBP_ISMODIFICATIONQUERY: FIELD_TYPES.BOOL,
    DBP_ISTHROUGHPUTQUERY: FIELD_TYPES.BOOL}

DBP_REQUIRED_FIELDS = [
    DBP_PERFORMERNAME,
    DBP_TESTCASEID,
    DBP_FQID,
    DBP_SELECTIONCOLS,
    DBP_ISMODIFICATIONQUERY,
    DBP_ISTHROUGHPUTQUERY]

MODS_TABLENAME = "mods"
MODS_MID = "mid"
MODS_CATEGORY = "category"
MODS_NUMRECORDS = "db_num_records"
MODS_RECORDSIZE = "db_record_size"
MODS_RECORDID = "record_id"

MODS_FIELDS_TO_TYPES = {
    MODS_MID: FIELD_TYPES.INTEGER,
    MODS_CATEGORY: FIELD_TYPES.TEXT,
    MODS_NUMRECORDS: FIELD_TYPES.INTEGER,
    MODS_RECORDSIZE: FIELD_TYPES.INTEGER,
    MODS_RECORDID: FIELD_TYPES.INTEGER}

MODS_REQUIRED_FIELDS = [
    MODS_MID,
    MODS_CATEGORY,
    MODS_NUMRECORDS,
    MODS_RECORDSIZE,
    MODS_RECORDID]

MODQUERIES_TABLENAME = "mod_queries"
MODQUERIES_QID = "qid"
MODQUERIES_WHERECLAUSE = "where_clause"
MODQUERIES_NUMRECORDS = "db_num_records"
MODQUERIES_RECORDSIZE = "db_record_size"
MODQUERIES_MID = "mid"

MODQUERIES_FIELDS_TO_TYPES = {
    MODQUERIES_QID: FIELD_TYPES.INTEGER,
    MODQUERIES_WHERECLAUSE: FIELD_TYPES.TEXT,
    MODQUERIES_NUMRECORDS: FIELD_TYPES.INTEGER,
    MODQUERIES_RECORDSIZE: FIELD_TYPES.INTEGER,
    MODQUERIES_MID: FIELD_TYPES.INTEGER}

MODQUERIES_REQUIRED_FIELDS = [
    MODQUERIES_QID,
    MODQUERIES_WHERECLAUSE,
    MODQUERIES_NUMRECORDS,
    MODQUERIES_RECORDSIZE,
    MODQUERIES_MID]

M2MQ_TABLENAME = "mods_to_modqueries"
M2MQ_QID = "qid"
M2MQ_MID = "mid"
M2MQ_PREIDS = "pre_matching_record_ids"
M2MQ_PREHASHES = "pre_matching_record_hashes"
M2MQ_POSTIDS = "post_matching_record_ids"
M2MQ_POSTHASHES = "post_matching_record_hashes"

M2MQ_FIELDS_TO_TYPES = {
    M2MQ_QID: FIELD_TYPES.INTEGER,
    M2MQ_MID: FIELD_TYPES.INTEGER,
    M2MQ_PREIDS: FIELD_TYPES.TEXT,
    M2MQ_PREHASHES: FIELD_TYPES.TEXT,
    M2MQ_POSTIDS: FIELD_TYPES.TEXT,
    M2MQ_POSTHASHES: FIELD_TYPES.TEXT}

M2MQ_REQUIRED_FIELDS = [
    M2MQ_QID,
    M2MQ_MID,
    M2MQ_PREIDS,
    M2MQ_PREHASHES,
    M2MQ_POSTIDS,
    M2MQ_POSTHASHES]

PMODS_TABLENAME = "performer_mods"
PMODS_PERFORMER = "performer"
PMODS_TESTCASEID = "test_case_id"
PMODS_MID = "mid"
PMODS_SENDTIME = "send_time"
PMODS_RESULTSTIME = "results_time"
PMODS_MODLATENCY = "mod_latency"
PMODS_EVENTMSGTIMES = "eventmsg_times"
PMODS_EVENTMSGIDS = "eventmsg_ids"
PMODS_EVENTMSGVALS = "eventmsg_vals"
PMODS_STATUS = "status"

PMODS_FIELDS_TO_TYPES = {
    PMODS_PERFORMER: FIELD_TYPES.TEXT,
    PMODS_TESTCASEID: FIELD_TYPES.TEXT,
    PMODS_MID: FIELD_TYPES.INTEGER,
    PMODS_SENDTIME: FIELD_TYPES.REAL,
    PMODS_RESULTSTIME: FIELD_TYPES.REAL,
    PMODS_MODLATENCY: FIELD_TYPES.REAL,
    PMODS_EVENTMSGTIMES: FIELD_TYPES.TEXT,
    PMODS_EVENTMSGIDS: FIELD_TYPES.TEXT,
    PMODS_EVENTMSGVALS: FIELD_TYPES.TEXT,
    PMODS_STATUS: FIELD_TYPES.TEXT}

PMODS_REQUIRED_FIELDS = [
    PMODS_PERFORMER,
    PMODS_TESTCASEID,
    PMODS_MID]    

F2A_TABLENAME = "full_to_atomic_junction"
F2A_AQID= "atomic_row_id"
F2A_FQID = "full_row_id"

F2A_FIELDS_TO_TYPES = {
    F2A_AQID: FIELD_TYPES.INTEGER,
    F2A_FQID: FIELD_TYPES.INTEGER}

F2A_REQUIRED_FIELDS = [F2A_AQID, F2A_FQID]

F2F_TABLENAME = "full_to_full_junction"
F2F_COMPOSITEQID = "composite_full_query"
F2F_BASEQID = "base_full_query"

F2F_FIELDS_TO_TYPES = {
    F2F_COMPOSITEQID: FIELD_TYPES.INTEGER,
    F2F_BASEQID: FIELD_TYPES.INTEGER}

F2F_REQUIRED_FIELDS = [F2F_COMPOSITEQID, F2F_BASEQID]

PVER_TABLENAME = "performer_verifications"
PVER_PERFORMER = "performer"
PVER_TESTCASEID = "test_case_id"
PVER_RECORDID = "record_id"
PVER_VERIFICATION = "verification"
PVER_SENDTIME = "send_time"
PVER_RESULTSTIME = "results_time"
PVER_VERIFICATIONLATENCY = "verification_latency"
PVER_MODLATENCY = "mod_latency"
PVER_EVENTMSGTIMES = "eventmsg_times"
PVER_EVENTMSGIDS = "eventmsg_ids"
PVER_EVENTMSGVALS = "eventmsg_vals"
PVER_STATUS = "status"
PVER_CORRECTNESS = "correctness"

PVER_FIELDS_TO_TYPES = {
    PVER_PERFORMER: FIELD_TYPES.TEXT,
    PVER_TESTCASEID: FIELD_TYPES.TEXT,
    PVER_RECORDID: FIELD_TYPES.INTEGER,
    PVER_VERIFICATION: FIELD_TYPES.BOOL,
    PVER_SENDTIME: FIELD_TYPES.REAL,
    PVER_RESULTSTIME: FIELD_TYPES.REAL,
    PVER_VERIFICATIONLATENCY: FIELD_TYPES.REAL,
    PVER_EVENTMSGTIMES: FIELD_TYPES.TEXT,
    PVER_EVENTMSGIDS: FIELD_TYPES.TEXT,
    PVER_EVENTMSGVALS: FIELD_TYPES.TEXT,
    PVER_STATUS: FIELD_TYPES.TEXT,
    PVER_CORRECTNESS: FIELD_TYPES.BOOL}

PVER_REQUIRED_FIELDS = [
    PVER_PERFORMER,
    PVER_TESTCASEID,
    PVER_VERIFICATION,
    PVER_VERIFICATIONLATENCY]

TABLENAME_TO_FIELDTOTYPE = {
    DBA_TABLENAME: DBA_FIELDS_TO_TYPES,
    DBF_TABLENAME: DBF_FIELDS_TO_TYPES,
    DBP_TABLENAME: DBP_FIELDS_TO_TYPES,
    MODS_TABLENAME: MODS_FIELDS_TO_TYPES,
    MODQUERIES_TABLENAME: MODQUERIES_FIELDS_TO_TYPES,
    M2MQ_TABLENAME: M2MQ_FIELDS_TO_TYPES,
    PMODS_TABLENAME: PMODS_FIELDS_TO_TYPES,
    F2A_TABLENAME: F2A_FIELDS_TO_TYPES,
    F2F_TABLENAME: F2F_FIELDS_TO_TYPES,
    PVER_TABLENAME: PVER_FIELDS_TO_TYPES}

TABLENAME_TO_REQUIREDFIELDS = {
    DBA_TABLENAME: DBA_REQUIRED_FIELDS,
    DBF_TABLENAME: DBF_REQUIRED_FIELDS,
    DBP_TABLENAME: DBP_REQUIRED_FIELDS,
    MODS_TABLENAME: MODS_REQUIRED_FIELDS,
    MODQUERIES_TABLENAME: MODQUERIES_REQUIRED_FIELDS,
    M2MQ_TABLENAME: M2MQ_REQUIRED_FIELDS,
    PMODS_TABLENAME: PMODS_REQUIRED_FIELDS,
    F2A_TABLENAME: F2A_REQUIRED_FIELDS,
    F2F_TABLENAME: F2F_REQUIRED_FIELDS,
    PVER_TABLENAME: PVER_REQUIRED_FIELDS}

# a dictionary of all pipe-delimited list fields, in (table, field) form,
# mapped to the type of their elements:
LIST_FIELDS = {
    (DBF_TABLENAME, DBF_MATCHINGRECORDIDS): int,
    (DBF_TABLENAME, DBF_MATCHINGRECORDHASHES): str,
    (DBF_TABLENAME, DBF_REJECTINGPOLICIES): str,
    (DBF_TABLENAME, DBF_P9MATCHINGRECORDCOUNTS): int,
    (DBF_TABLENAME, DBF_P1NEGATEDTERM): int,
    (DBP_TABLENAME, DBP_RETURNEDRECORDIDS): int,
    (DBP_TABLENAME, DBP_RETURNEDRECORDHASHES): str,
    (DBP_TABLENAME, DBP_CURRENTPOLICIES): str,
    (DBP_TABLENAME, DBP_EVENTMSGTIMES): float,
    (DBP_TABLENAME, DBP_EVENTMSGIDS): str,
    (DBP_TABLENAME, DBP_EVENTMSGVALS): str,
    (DBP_TABLENAME, DBP_STATUS): str,
    (M2MQ_TABLENAME, M2MQ_PREIDS): int,
    (M2MQ_TABLENAME, M2MQ_PREHASHES): str,
    (M2MQ_TABLENAME, M2MQ_POSTIDS): int,
    (M2MQ_TABLENAME, M2MQ_POSTHASHES): str,
    (PMODS_TABLENAME, PMODS_STATUS): str,
    (PMODS_TABLENAME, PMODS_EVENTMSGTIMES): float,
    (PMODS_TABLENAME, PMODS_EVENTMSGIDS): str,
    (PMODS_TABLENAME, PMODS_EVENTMSGVALS): str,
    (PVER_TABLENAME, PVER_STATUS): str,
    (PVER_TABLENAME, PVER_EVENTMSGTIMES): float,
    (PVER_TABLENAME, PVER_EVENTMSGIDS): str,
    (PVER_TABLENAME, PVER_EVENTMSGVALS): str}

# a dictionary mapping each table to auxiliary lines necessary in its
# construction:
TABLENAME_TO_AUX = {
    DBA_TABLENAME:
    ",".join(["UNIQUE (%s, %s, %s)"
              % (DBA_NUMRECORDS, DBA_RECORDSIZE, DBA_WHERECLAUSE),
              "UNIQUE (%s)" % DBA_AQID]),
    DBF_TABLENAME: "UNIQUE (%s)" % DBF_FQID,
    DBP_TABLENAME:
    ",".join(["FOREIGN KEY (%s) REFERENCES %s (%s)" %
              (DBP_FQID, DBF_TABLENAME, DBF_FQID),
              "UNIQUE (%s, %s)" %
              (DBP_SENDTIME, DBP_RESULTSTIME)]),
    F2A_TABLENAME:
    "".join(["FOREIGN KEY (%s) REFERENCES %s (ROWID), " %
             (F2A_FQID, DBF_TABLENAME),
             "FOREIGN KEY (%s) REFERENCES %s (ROWID)" %
             (F2A_AQID, DBA_TABLENAME)]),
    PMODS_TABLENAME: "UNIQUE (%s, %s)" % (PMODS_SENDTIME, PMODS_RESULTSTIME),
    PVER_TABLENAME: "UNIQUE (%s, %s)" % (PVER_SENDTIME, PVER_RESULTSTIME)}

PERFORMER_TABLENAMES = set(
    [DBP_TABLENAME, PMODS_TABLENAME, PVER_TABLENAME])

# a list of the non-performer tables, in order from most to least likely to be
# the primary table.
OTHER_TABLENAMES_HEIRARCHY = [
    DBA_TABLENAME, DBF_TABLENAME, MODQUERIES_TABLENAME, MODS_TABLENAME]

# map of primary table to necessary joins (denoted tuples of the
# form (source_table, source_field, target_table, target_field,
# target_table_alias (None if not applicable))):
TABLENAME_TO_JOINS = {}
for tablename in TABLENAME_TO_FIELDTOTYPE.keys():
    TABLENAME_TO_JOINS[tablename] = []
TABLENAME_TO_JOINS[MODQUERIES_TABLENAME] = [
    (MODQUERIES_TABLENAME,
     MODQUERIES_MID,
     MODS_TABLENAME,
     MODS_MID,
     None)]
TABLENAME_TO_JOINS[PMODS_TABLENAME] = [
    (PMODS_TABLENAME,
     PMODS_MID,
     MODS_TABLENAME,
     MODS_MID,
     None)]
TABLENAME_TO_JOINS[DBP_TABLENAME] = [
    (DBP_TABLENAME,
     DBP_FQID,
     DBF_TABLENAME,
     DBF_FQID,
     None)]
# the DBF_TABLENAME value in TABLENAME_TO_JOINS should be overridden if we
# care to connect to atomic or other full queries

class Ta1ResultsSchema(ResultsSchema):
    
    def __init__(self):
        super(Ta1ResultsSchema, self).__init__()
        self.list_fields = LIST_FIELDS
        self.tablename_to_fieldtotype = TABLENAME_TO_FIELDTOTYPE
        self.tablename_to_requiredfields = TABLENAME_TO_REQUIREDFIELDS
        self.tablename_to_aux = TABLENAME_TO_AUX
        self.tablename_to_joins = TABLENAME_TO_JOINS
        self.performer_tablenames = PERFORMER_TABLENAMES
        self.other_tablenames_heirarchy = OTHER_TABLENAMES_HEIRARCHY

    def process_for_sorting(self, item, (table, field)):
        """Processes the item so that it is in an order-friendly form."""
        if ((table, field) in [(DBA_TABLENAME, DBA_CAT),
                               (DBF_TABLENAME, DBF_CAT)]
            and item in CATEGORIES.values_list()):
            return CATEGORIES.value_to_number[item]
        else:
            return item
