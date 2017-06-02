//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for InsertHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 11 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE QueryHandlerTest
#include "../../common/test-init.h"

#include <string>

#include "query-handler.h"

using namespace std;

// NOTE: The test check that we re-write CONTAINED_IN and CONTAINS_STEM queries
// into correct queries. However, these aren't terribly robust tests as there
// are many ways to write a compatible query. However, the time to write really
// robust test is prohibitive so this will have to be good enough for now.

// A sublcass that we use for testing. It exposes some protected methods that we
// want to test and works with a NULL connection pool.
class TestableQueryHandler : public QueryHandler {
 public:
  TestableQueryHandler() : QueryHandler(NULL, NULL, -1) {}
  virtual ~TestableQueryHandler() {}

  bool NeedsExpansion(const string& query) const {
    return QueryHandler::NeedsExpansion(query);
  }

  void ExpandQuery(string* query) const {
    QueryHandler::ExpandQuery(query);
  }
};

// This isn't really "black-box" testing, but the regular expressions are
// complex enough it seems worthwhile to test that we're expanding only the
// correct set of queries.
BOOST_AUTO_TEST_CASE(TestNeedsExpansion) {
  TestableQueryHandler qh;
  BOOST_CHECK_EQUAL(
      qh.NeedsExpansion(
          "SELECT id FROM main WHERE CONTAINED_IN(notes1, 'hello')"),
      true);

  BOOST_CHECK_EQUAL(
      qh.NeedsExpansion(
          "SELECT * FROM main WHERE CONTAINED_IN(notes1, 'hello') and "
          "fname = 'Oliver'"),
      true);

  BOOST_CHECK_EQUAL(
      qh.NeedsExpansion(
          "SELECT id FROM main WHERE lname = 'Dain' or "
          "CONTAINS_STEM(notes2, 'there')"),
      true);

  BOOST_CHECK_EQUAL(
      qh.NeedsExpansion(
          "SELECT id FROM main WHERE lname = 'CONTAINED_IN(' or "
          "lname = 'CONTAINS_STEM(notes2, \\'there\\')'"),
      false);

  BOOST_CHECK_EQUAL(
      qh.NeedsExpansion(
          "SELECT id FROM main WHERE WORD_PROXIMITY(notes1, 'frabjous', 'callooh') <= 50"),
      true);

  BOOST_CHECK_EQUAL(
      qh.NeedsExpansion(
          "SELECT id FROM main WHERE WORD_PROXIMITY(notes3, 'foo', 'bar') < 100"),
      true);

  // Make sure it works with escaped ' characters.
  BOOST_CHECK_EQUAL(
      qh.NeedsExpansion(
          "SELECT * FROM main WHERE CONTAINED_IN(notes2, 'it\\'s')"), true);
}

BOOST_AUTO_TEST_CASE(SimpleContainedInExpansion) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE CONTAINED_IN(notes2, 'foo')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, keywords t1 WHERE (main.id = t1.id and "
      "t1.col = 'notes2' and t1.word = 'foo')");
}

BOOST_AUTO_TEST_CASE(SimpleEscapedQuoteContainedInExpansion) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE CONTAINED_IN(notes2, 'it\\'s')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, keywords t1 WHERE (main.id = t1.id and "
      "t1.col = 'notes2' and t1.word = 'it\\'s')");
}

BOOST_AUTO_TEST_CASE(ContainedInInConjunction1) {
  TestableQueryHandler qh;

  string q("SELECT * FROM main WHERE CONTAINED_IN(notes2, 'foo') "
           "and fname = 'Oliver'");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.* FROM main, keywords t1 WHERE (main.id = t1.id and "
      "t1.col = 'notes2' and t1.word = 'foo') and fname = 'Oliver'");
}

BOOST_AUTO_TEST_CASE(ContainedInInConjunction2) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE fname = 'Oliver' and "
           "CONTAINED_IN(notes2, 'foo')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, keywords t1 WHERE fname = 'Oliver' "
      "and (main.id = t1.id and " "t1.col = 'notes2' and t1.word = 'foo')");
}

BOOST_AUTO_TEST_CASE(TwoContainedInInDisjunction) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE CONTAINED_IN(notes3, 'bar') OR "
           "CONTAINED_IN(notes2, 'foo')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, keywords t1, keywords t2 WHERE "
      "(main.id = t1.id and t1.col = 'notes3' and t1.word = 'bar') OR "
      "(main.id = t2.id and t2.col = 'notes2' and t2.word = 'foo')");
}

BOOST_AUTO_TEST_CASE(SimpleContainsStem) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE CONTAINS_STEM(notes2, 'running')");
  qh.ExpandQuery(&q);
  // Note that we're checking that 'running' was stemmed to 'run'
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, stems t1 WHERE (main.id = t1.id and "
      "t1.col = 'notes2' and t1.word = 'run')");
}

BOOST_AUTO_TEST_CASE(SimpleQuotedQuoteContainsStem) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE CONTAINS_STEM(notes2, 'can\\'t')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, stems t1 WHERE (main.id = t1.id and "
      "t1.col = 'notes2' and t1.word = 'can\\'t')");
}

// Make sure we replace any and all ambiguous references to the id column with
// main.id. Note that we intentionally add lots of edge cases like id in quotes,
// id in the middle of words, etc.
BOOST_AUTO_TEST_CASE(IdColumnReplacementWorks) {
  TestableQueryHandler qh;

  string q(
      "SELECT id FROM main WHERE id = 10 OR CONTAINED_IN(notes4, 'hello')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, keywords t1 WHERE main.id = 10 OR "
      "(main.id = t1.id and t1.col = 'notes4' and t1.word = 'hello')");

  q = "SELECT * FROM main WHERE id = 10 OR CONTAINED_IN(notes4, 'hello')";
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.* FROM main, keywords t1 WHERE main.id = 10 OR "
      "(main.id = t1.id and t1.col = 'notes4' and t1.word = 'hello')");

  q = "SELECT * FROM main WHERE fname = 'id' OR id = 10 "
      "OR CONTAINED_IN(notes4, 'hello')";
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.* FROM main, keywords t1 WHERE fname = 'id' OR "
      "main.id = 10 OR "
      "(main.id = t1.id and t1.col = 'notes4' and t1.word = 'hello')");

  q = "SELECT * FROM main WHERE fname = 'this id is' OR id = 10 "
      "OR CONTAINED_IN(notes4, 'hello')";
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.* FROM main, keywords t1 WHERE fname = 'this id is' OR "
      "main.id = 10 OR "
      "(main.id = t1.id and t1.col = 'notes4' and t1.word = 'hello')");

  q = "SELECT * FROM main WHERE (id = 10 OR CONTAINED_IN(notes4, 'hello'))";
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.* FROM main, keywords t1 WHERE (main.id = 10 OR "
      "(main.id = t1.id and t1.col = 'notes4' and t1.word = 'hello'))");
}


// We test a big query with multiple CONTAINED_IN and CONTAINS_STEM clases in
// parantheses, etc.
BOOST_AUTO_TEST_CASE(ComplexQuery) {
  TestableQueryHandler qh;

  string q("SELECT * FROM main WHERE "
           "(CONTAINS_STEM(notes1, 'thirsty') OR fname = 'Oliver') AND "
           "(lname = 'Dain' OR "
           "M_OF_N(3, 2, id > 20, "
                   "CONTAINED_IN(notes3, 'thirsty'), "
                   "CONTAINS_STEM(notes2, 'worlds')))");
  qh.ExpandQuery(&q);
  // Note that we're checking that 'running' was stemmed to 'run'
  BOOST_CHECK_EQUAL(
      q, "SELECT main.* FROM main, stems t1, keywords t2, stems t3 WHERE "
      "((main.id = t1.id and t1.col = 'notes1' and t1.word = 'thirsti') "
      "OR fname = 'Oliver') AND (lname = 'Dain' OR "
      "M_OF_N(3, 2, main.id > 20, "
      "(main.id = t2.id and t2.col = 'notes3' and t2.word = 'thirsty'), "
      "(main.id = t3.id and t3.col = 'notes2' and t3.word = 'world')))");
}

BOOST_AUTO_TEST_CASE(SimpleProx) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE WORD_PROXIMITY(notes2, 'frabjous', 'callooh') < 30");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, alarms WHERE (main.id = alarms.id and "
      "alarms.field = 'notes2' and ((alarms.word1 = 'frabjous' and "
      "alarms.word2 = 'callooh') or (alarms.word1 = 'callooh' and alarms.word2 = 'frabjous')) and "
      "alarms.distance < 30)");
}

BOOST_AUTO_TEST_CASE(SimpleQuotedProx) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE WORD_PROXIMITY(notes3, '\\'Twas', 'brillig') <= 70");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, alarms WHERE (main.id = alarms.id and "
      "alarms.field = 'notes3' and ((alarms.word1 = '\\'Twas' and "
      "alarms.word2 = 'brillig') or (alarms.word1 = 'brillig' and alarms.word2 = '\\'Twas')) and "
      "alarms.distance <= 70)");
}

BOOST_AUTO_TEST_CASE(SimpleRanking) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE WORD_PROXIMITY(notes2, 'frabjous', 'callooh') < 30 ORDER BY WORD_PROXIMITY(notes2, 'frabjous', 'callooh')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, alarms WHERE (main.id = alarms.id and "
      "alarms.field = 'notes2' and ((alarms.word1 = 'frabjous' and "
      "alarms.word2 = 'callooh') or (alarms.word1 = 'callooh' and alarms.word2 = 'frabjous')) and "
      "alarms.distance < 30) ORDER BY alarms.distance");
}

BOOST_AUTO_TEST_CASE(SimpleQuotedRanking) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE WORD_PROXIMITY(notes3, '\\'Twas', 'brillig') <= 70 ORDER BY WORD_PROXIMITY(notes3, '\\'Twas', 'brillig')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, alarms WHERE (main.id = alarms.id and "
      "alarms.field = 'notes3' and ((alarms.word1 = '\\'Twas' and "
      "alarms.word2 = 'brillig') or (alarms.word1 = 'brillig' and alarms.word2 = '\\'Twas')) and "
      "alarms.distance <= 70) ORDER BY alarms.distance");
}

BOOST_AUTO_TEST_CASE(RelativeXmlValue) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE xml_value(xml, '//lname', 'SMITH')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, xml_join WHERE (main.id = xml_join.id and "
      "xml_join.field = 'xml' and xml_join.path LIKE '%/lname' and "
      "xml_join.value = 'SMITH')");
}

BOOST_AUTO_TEST_CASE(AbsoluteXmlValue) {
  TestableQueryHandler qh;

  string q("SELECT id FROM main WHERE xml_value(xml, '/Person/Manager/lname', 'SMITH')");
  qh.ExpandQuery(&q);
  BOOST_CHECK_EQUAL(
      q, "SELECT main.id FROM main, xml_join WHERE (main.id = xml_join.id and "
      "xml_join.field = 'xml' and xml_join.path = '/Person/Manager/lname' and "
      "xml_join.value = 'SMITH')");
}
