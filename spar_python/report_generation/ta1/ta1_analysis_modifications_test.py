# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Tests the modification analysis tool.
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  21 Nov 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest
import sqlite3

# SPAR imports:
import spar_python.report_generation.ta1.ta1_database as t1d
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_analysis_modifications as t1am

DBPATH = ":memory:"
WHERECLAUSE = "dummy where clause"
BASELINENAME = "baseline"
PERFORMERNAME = "white knight"
TESTCASEID = "TC001"
NUMRECORDS = 1000
RECORDSIZE = 100

from spar_python.report_generation.a_col_ta1_config import config
config.results_db_path = DBPATH
config.performername = PERFORMERNAME
config.baselinename = BASELINENAME


class Ta1DatabaseTest(unittest.TestCase):

    def setUp(self):
        self.config = config

    def test_no_mods(self):
        this_config = self.config
        this_config.results_db.clear()
        ins_mod_cat = t1s.MOD_CATEGORIES.to_string(t1s.MOD_CATEGORIES.insert)
        # an insertion modification getter:
        ins_mod_getter = t1am.ModificationGetter(
            config=this_config)
        ins_analysis = ins_mod_getter.get_analysis(mod_cat=ins_mod_cat)
        self.assertEquals(ins_analysis.nummods, 0)
        self.assertEquals(ins_analysis.numfailedmods, 0)
        self.assertEquals(ins_analysis.nummodsbadinfo, 0)
        self.assertEquals(ins_analysis.numgoodmods, 0)
        self.assertEquals(ins_analysis.nummodswrongpostqueries, 0)
        self.assertEquals(ins_analysis.min_correct_slatencies, [])
        self.assertEquals(ins_analysis.min_correct_rlatencies, [])
        self.assertEquals(ins_analysis.max_wrong_slatencies, [])
        self.assertEquals(ins_analysis.max_wrong_rlatencies, [])

    def test_correct(self):
        this_config = self.config
        set_up_static_db(this_config.results_db)
        ins_mod_cat = t1s.MOD_CATEGORIES.to_string(t1s.MOD_CATEGORIES.insert)
        # an insertion modification getter:
        ins_mod_getter = t1am.ModificationGetter(
            config=this_config)
        ins_analysis = ins_mod_getter.get_analysis(mod_cat=ins_mod_cat)
        self.assertEquals(ins_analysis.nummods, 2)
        self.assertEquals(ins_analysis.numfailedmods, 0)
        self.assertEquals(ins_analysis.nummodsbadinfo, 0)
        self.assertEquals(ins_analysis.numgoodmods, 2)
        self.assertEquals(ins_analysis.nummodswrongpostqueries, 0)
        self.assertEquals(ins_analysis.min_correct_slatencies, [48.0, 48.0])
        self.assertEquals(ins_analysis.min_correct_rlatencies, [49.0, 49.0])
        self.assertEquals(ins_analysis.max_wrong_slatencies, [])
        self.assertEquals(ins_analysis.max_wrong_rlatencies, [])
        
    def test_wrong_pre(self):
        this_config = self.config
        set_up_static_db(this_config.results_db)
        ins_mod_cat = t1s.MOD_CATEGORIES.to_string(t1s.MOD_CATEGORIES.update)
        # an update modification getter:
        ins_mod_getter = t1am.ModificationGetter(
            config=this_config)
        ins_analysis = ins_mod_getter.get_analysis(mod_cat=ins_mod_cat)
        self.assertEquals(ins_analysis.nummods, 2)
        self.assertEquals(ins_analysis.numfailedmods, 0)
        self.assertEquals(ins_analysis.nummodsbadinfo, 1)
        self.assertEquals(ins_analysis.numgoodmods, 1)
        self.assertEquals(ins_analysis.nummodswrongpostqueries, 0)
        self.assertEquals(ins_analysis.min_correct_slatencies, [48.0])
        self.assertEquals(ins_analysis.min_correct_rlatencies, [49.0])
        self.assertEquals(ins_analysis.max_wrong_slatencies, [])
        self.assertEquals(ins_analysis.max_wrong_rlatencies, [])
        
    def test_wrong_post(self):
        this_config = self.config
        set_up_static_db(this_config.results_db)
        ins_mod_cat = t1s.MOD_CATEGORIES.to_string(t1s.MOD_CATEGORIES.delete)
        # an delete modification getter:
        ins_mod_getter = t1am.ModificationGetter(
            config=this_config)
        ins_analysis = ins_mod_getter.get_analysis(mod_cat=ins_mod_cat)
        self.assertEquals(ins_analysis.nummods, 2)
        self.assertEquals(ins_analysis.numfailedmods, 0)
        self.assertEquals(ins_analysis.nummodsbadinfo, 0)
        self.assertEquals(ins_analysis.numgoodmods, 1)
        self.assertEquals(ins_analysis.nummodswrongpostqueries, 1)
        self.assertEquals(ins_analysis.min_correct_slatencies, [48.0])
        self.assertEquals(ins_analysis.min_correct_rlatencies, [49.0])
        self.assertEquals(ins_analysis.max_wrong_slatencies, [48.0])
        self.assertEquals(ins_analysis.max_wrong_rlatencies, [49.0])

    def test_failed_mod(self):
        this_config = self.config
        set_up_static_db(this_config.results_db)
        # add failed modification row:
        mod_row = {
            t1s.MODS_NUMRECORDS: NUMRECORDS,
            t1s.MODS_RECORDSIZE: RECORDSIZE,
            t1s.MODS_MID: 201,
            t1s.MODS_CATEGORY: t1s.MODS_CATEGORIES.to_string(
                t1s.MODS_CATEGORIES.insert),
            t1s.MODS_RECORDID: 2010}
        this_config.results_db.add_row(t1s.MODS_TABLENAME, mod_row)
        pmods_row = {
            t1s.PMODS_PERFORMER: PERFORMERNAME,
            t1s.PMODS_TESTCASEID: TESTCASEID,
            t1s.PMODS_MID: 201,
            t1s.PMODS_SENDTIME: 20100.0,
            t1s.PMODS_RESULTSTIME: 20101.0,
            t1s.PMODS_MODLATENCY: 1.0,
            t1s.PMODS_STATUS: "failure sadness"}
        this_config.results_db.add_row(t1s.PMODS_TABLENAME, pmods_row)
        ins_mod_cat = t1s.MOD_CATEGORIES.to_string(t1s.MOD_CATEGORIES.insert)
        # an insertion modification getter:
        ins_mod_getter = t1am.ModificationGetter(
            config=this_config)
        ins_analysis = ins_mod_getter.get_analysis(mod_cat=ins_mod_cat)
        self.assertEquals(ins_analysis.nummods, 3)
        self.assertEquals(ins_analysis.numfailedmods, 1)
        self.assertEquals(ins_analysis.nummodsbadinfo, 0)
        self.assertEquals(ins_analysis.numgoodmods, 2)
        self.assertEquals(ins_analysis.nummodswrongpostqueries, 0)
        self.assertEquals(ins_analysis.min_correct_slatencies, [48.0, 48.0])
        self.assertEquals(ins_analysis.min_correct_rlatencies, [49.0, 49.0])
        self.assertEquals(ins_analysis.max_wrong_slatencies, [])
        self.assertEquals(ins_analysis.max_wrong_rlatencies, [])

def set_up_static_db(this_database):
    """
    Enters some hard-coded modification values into the database.
    """
    this_database.clear()
    # add modifications:
    mods_row_base = {
        t1s.MODS_NUMRECORDS: NUMRECORDS,
        t1s.MODS_RECORDSIZE: RECORDSIZE}
    mods_rows = [
        {t1s.MODS_MID: 1,
         t1s.MODS_CATEGORY: t1s.MODS_CATEGORIES.to_string(
             t1s.MODS_CATEGORIES.insert),
         t1s.MODS_RECORDID: 10},
        {t1s.MODS_MID: 2,
         t1s.MODS_CATEGORY: t1s.MODS_CATEGORIES.to_string(
             t1s.MODS_CATEGORIES.insert),
         t1s.MODS_RECORDID: 20},
        {t1s.MODS_MID: 3,
         t1s.MODS_CATEGORY: t1s.MODS_CATEGORIES.to_string(
             t1s.MODS_CATEGORIES.update),
         t1s.MODS_RECORDID: 30},
        {t1s.MODS_MID: 4,
         t1s.MODS_CATEGORY: t1s.MODS_CATEGORIES.to_string(
             t1s.MODS_CATEGORIES.update),
         t1s.MODS_RECORDID: 40},
        {t1s.MODS_MID: 5,
         t1s.MODS_CATEGORY: t1s.MODS_CATEGORIES.to_string(
             t1s.MODS_CATEGORIES.delete),
         t1s.MODS_RECORDID: 50},
        {t1s.MODS_MID: 6,
         t1s.MODS_CATEGORY: t1s.MODS_CATEGORIES.to_string(
             t1s.MODS_CATEGORIES.delete),
         t1s.MODS_RECORDID: 60}]
    for mods_row in mods_rows:
        mods_row.update(mods_row_base)
        this_database.add_row(t1s.MODS_TABLENAME, mods_row)

    # add performer modifications:
    pmods_row_base = {
        t1s.PMODS_PERFORMER: PERFORMERNAME,
        t1s.PMODS_TESTCASEID: TESTCASEID}
    pmods_rows = [
        {t1s.PMODS_MID: 1,
         t1s.PMODS_SENDTIME: 100.0,
         t1s.PMODS_RESULTSTIME: 101.0,
         t1s.PMODS_MODLATENCY: 1.0},
        {t1s.PMODS_MID: 2,
         t1s.PMODS_SENDTIME: 200.0,
         t1s.PMODS_RESULTSTIME: 201.0,
         t1s.PMODS_MODLATENCY: 1.0},
        {t1s.PMODS_MID: 3,
         t1s.PMODS_SENDTIME: 300.0,
         t1s.PMODS_RESULTSTIME: 301.0,
         t1s.PMODS_MODLATENCY: 1.0},
        {t1s.PMODS_MID: 4,
         t1s.PMODS_SENDTIME: 400.0,
         t1s.PMODS_RESULTSTIME: 401.0,
         t1s.PMODS_MODLATENCY: 1.0},
        {t1s.PMODS_MID: 5,
         t1s.PMODS_SENDTIME: 500.0,
         t1s.PMODS_RESULTSTIME: 501.0,
         t1s.PMODS_MODLATENCY: 1.0},
        {t1s.PMODS_MID: 6,
         t1s.PMODS_SENDTIME: 600.0,
         t1s.PMODS_RESULTSTIME: 601.0,
         t1s.PMODS_MODLATENCY: 1.0}]
    for pmods_row in pmods_rows:
        pmods_row.update(pmods_row_base)
        this_database.add_row(t1s.PMODS_TABLENAME, pmods_row)

    # add modification queries:
    mquery_row_base = {
        t1s.MODQUERIES_WHERECLAUSE: WHERECLAUSE,
        t1s.MODQUERIES_NUMRECORDS: NUMRECORDS,
        t1s.MODQUERIES_RECORDSIZE: RECORDSIZE}
    mquery_rows = []
    m2mq_rows = []
    for (qid, mods_row) in zip(range(1, 7), mods_rows):
        mquery_row = {t1s.MODQUERIES_QID: qid,
                      t1s.MODQUERIES_MID: mods_row[t1s.MODS_MID]}
        mquery_row.update(mquery_row_base)
        mquery_rows.append(mquery_row)
        basemris = [1]
        if mods_row[t1s.MODS_CATEGORY] == t1s.MODS_CATEGORIES.to_string(
             t1s.MODS_CATEGORIES.delete):
            premris = basemris + [mods_row[t1s.MODS_RECORDID]]
            postmris = basemris
        elif mods_row[t1s.MODS_CATEGORY] in [
            t1s.MODS_CATEGORIES.to_string(t1s.MODS_CATEGORIES.insert),
            t1s.MODS_CATEGORIES.to_string(t1s.MODS_CATEGORIES.update)]:
            premris = basemris
            postmris = basemris + [mods_row[t1s.MODS_RECORDID]]
        else: assert False
        premrhs = [str(mri) for mri in premris]
        postmrhs = [str(mri) for mri in postmris]
        m2mq_row = {
            t1s.M2MQ_QID: qid,
            t1s.M2MQ_MID: mods_row[t1s.MODS_MID],
            t1s.M2MQ_PREIDS: premris,
            t1s.M2MQ_PREHASHES: premrhs,
            t1s.M2MQ_POSTIDS: postmris,
            t1s.M2MQ_POSTHASHES: postmrhs}
        m2mq_rows.append(m2mq_row)
    for mquery_row in mquery_rows:
        this_database.add_row(t1s.MODQUERIES_TABLENAME, mquery_row)
    for m2mq_row in m2mq_rows:
        this_database.add_row(t1s.M2MQ_TABLENAME, m2mq_row)

    # add performer queries:
    pquery_row_base = {
        t1s.DBP_PERFORMERNAME: PERFORMERNAME,
        t1s.DBP_TESTCASEID: TESTCASEID,
        t1s.DBP_ISMODIFICATIONQUERY: True,
        t1s.DBP_ISTHROUGHPUTQUERY: False}
    # in the following, the inserts are correct, the updates have a wrong
    # pre-query, and the deletes have a wrong post-query:
    pquery_rows = [
        {t1s.DBP_FQID: 101, # extra
         t1s.DBP_SELECTIONCOLS: "*",
         t1s.DBP_SENDTIME: 75.0,
         t1s.DBP_RESULTSTIME: 76.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 2, 3],
         t1s.DBP_RETURNEDRECORDHASHES: [str(1), str(2), str(3)]},
        {t1s.DBP_FQID: 1, # pre insert (correct)
         t1s.DBP_SELECTIONCOLS: "*",
         t1s.DBP_SENDTIME: 50.0,
         t1s.DBP_RESULTSTIME: 51.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1],
         t1s.DBP_RETURNEDRECORDHASHES: [str(1)]},
        {t1s.DBP_FQID: 1, # post insert (correct)
         t1s.DBP_SELECTIONCOLS: "*",
         t1s.DBP_SENDTIME: 149.0,
         t1s.DBP_RESULTSTIME: 150.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 10],
         t1s.DBP_RETURNEDRECORDHASHES: [str(1), str(10)]},
        {t1s.DBP_FQID: 2, # pre insert (correct)
         t1s.DBP_SELECTIONCOLS: "id",
         t1s.DBP_SENDTIME: 150.0,
         t1s.DBP_RESULTSTIME: 151.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1],
         t1s.DBP_RETURNEDRECORDHASHES: []},
        {t1s.DBP_FQID: 2, # post insert (correct)
         t1s.DBP_SELECTIONCOLS: "id",
         t1s.DBP_SENDTIME: 249.0,
         t1s.DBP_RESULTSTIME: 250.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 20],
         t1s.DBP_RETURNEDRECORDHASHES: []},
        {t1s.DBP_FQID: 3, # pre update (wrong)
         t1s.DBP_SELECTIONCOLS: "*",
         t1s.DBP_SENDTIME: 250.0,
         t1s.DBP_RESULTSTIME: 251.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 2],
         t1s.DBP_RETURNEDRECORDHASHES: [str(1), str(2)]},
        {t1s.DBP_FQID: 3, # post update
         t1s.DBP_SELECTIONCOLS: "*",
         t1s.DBP_SENDTIME: 349.0,
         t1s.DBP_RESULTSTIME: 350.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 30],
         t1s.DBP_RETURNEDRECORDHASHES: [str(1), str(30)]},
        {t1s.DBP_FQID: 4, # pre update
         t1s.DBP_SELECTIONCOLS: "id",
         t1s.DBP_SENDTIME: 350.0,
         t1s.DBP_RESULTSTIME: 351.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1],
         t1s.DBP_RETURNEDRECORDHASHES: []},
        {t1s.DBP_FQID: 4, # post update
         t1s.DBP_SELECTIONCOLS: "id",
         t1s.DBP_SENDTIME: 449.0,
         t1s.DBP_RESULTSTIME: 450.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 40],
         t1s.DBP_RETURNEDRECORDHASHES: []},
        {t1s.DBP_FQID: 5, # pre delete
         t1s.DBP_SELECTIONCOLS: "*",
         t1s.DBP_SENDTIME: 450.0,
         t1s.DBP_RESULTSTIME: 451.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 50],
         t1s.DBP_RETURNEDRECORDHASHES: [str(1), str(50)]},
        {t1s.DBP_FQID: 5, # post delete
         t1s.DBP_SELECTIONCOLS: "*",
         t1s.DBP_SENDTIME: 549.0,
         t1s.DBP_RESULTSTIME: 550.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1],
         t1s.DBP_RETURNEDRECORDHASHES: [str(1)]},
        {t1s.DBP_FQID: 6, # pre delete
         t1s.DBP_SELECTIONCOLS: "id",
         t1s.DBP_SENDTIME: 550.0,
         t1s.DBP_RESULTSTIME: 551.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 60],
         t1s.DBP_RETURNEDRECORDHASHES: []},
        {t1s.DBP_FQID: 6, # post delete (wrong)
         t1s.DBP_SELECTIONCOLS: "id",
         t1s.DBP_SENDTIME: 649.0,
         t1s.DBP_RESULTSTIME: 650.0,
         t1s.DBP_QUERYLATENCY: 1.0,
         t1s.DBP_RETURNEDRECORDIDS: [1, 60],
         t1s.DBP_RETURNEDRECORDHASHES: []}]

    for pquery_row in pquery_rows:
        pquery_row.update(pquery_row_base)
        this_database.add_row(t1s.DBP_TABLENAME, pquery_row)
