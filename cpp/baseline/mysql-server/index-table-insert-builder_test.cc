//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for IndexTableInsertBuilder 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Oct 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE IndexTableInsertBuilder
#include "common/test-init.h"

#include "index-table-insert-builder.h"

#include <string>
#include <vector>

#include "baseline/common/common-mysql-defs.h"
#include "common/knot.h"

using namespace std;

// Note: These tests are not as robust as I'd like. They hard code the order of
// the rows in the VALUES clause and they hard code 
BOOST_AUTO_TEST_CASE(BuilderWorkds) {
  IndexTableInsertBuilder builder(
      kKeywordIndexTableName, kStemsIndexTableName, set<string>());

  string row_id("234725332");

  Knot data(new string("A field containing lots of words to be "
                       "parsed and inserted"));

  string keyword_statement;
  string stem_statement;

  builder.GetInsertStatements(row_id, "notes2", data,
                              &keyword_statement, &stem_statement);

  BOOST_CHECK_EQUAL(
      keyword_statement,
      "INSERT into keywords (id, col, word) VALUES "
      "(234725332, 'notes2', \"a\"), (234725332, 'notes2', \"and\"), "
      "(234725332, 'notes2', \"be\"), (234725332, 'notes2', \"containing\"), "
      "(234725332, 'notes2', \"field\"), (234725332, 'notes2', \"inserted\"), "
      "(234725332, 'notes2', \"lots\"), (234725332, 'notes2', \"of\"), "
      "(234725332, 'notes2', \"parsed\"), (234725332, 'notes2', \"to\"), "
      "(234725332, 'notes2', \"words\")");

  BOOST_CHECK_EQUAL(
      stem_statement,
      "INSERT into stems (id, col, word) VALUES "
      "(234725332, 'notes2', \"a\"), (234725332, 'notes2', \"and\"), "
      "(234725332, 'notes2', \"be\"), (234725332, 'notes2', \"contain\"), "
      "(234725332, 'notes2', \"field\"), (234725332, 'notes2', \"insert\"), "
      "(234725332, 'notes2', \"lot\"), (234725332, 'notes2', \"of\"), "
      "(234725332, 'notes2', \"pars\"), (234725332, 'notes2', \"to\"), "
      "(234725332, 'notes2', \"word\")");
}

// A field that contains the same words more than once should not cause those
// words to be indexed more than once.
BOOST_AUTO_TEST_CASE(RepeatsWork) {
  IndexTableInsertBuilder builder("keywords", "stems", set<string>());

  string row_id("234725332");

  Knot data(new string("A field containing lots of words to be "
                       "parsed and inserted. parsed and inserted. Words."));

  string keyword_statement;
  string stem_statement;

  builder.GetInsertStatements(row_id, "notes2", data,
                              &keyword_statement, &stem_statement);

  BOOST_CHECK_EQUAL(
      keyword_statement,
      "INSERT into keywords (id, col, word) VALUES "
      "(234725332, 'notes2', \"a\"), (234725332, 'notes2', \"and\"), "
      "(234725332, 'notes2', \"be\"), (234725332, 'notes2', \"containing\"), "
      "(234725332, 'notes2', \"field\"), (234725332, 'notes2', \"inserted\"), "
      "(234725332, 'notes2', \"lots\"), (234725332, 'notes2', \"of\"), "
      "(234725332, 'notes2', \"parsed\"), (234725332, 'notes2', \"to\"), "
      "(234725332, 'notes2', \"words\")");

  BOOST_CHECK_EQUAL(
      stem_statement,
      "INSERT into stems (id, col, word) VALUES "
      "(234725332, 'notes2', \"a\"), (234725332, 'notes2', \"and\"), "
      "(234725332, 'notes2', \"be\"), (234725332, 'notes2', \"contain\"), "
      "(234725332, 'notes2', \"field\"), (234725332, 'notes2', \"insert\"), "
      "(234725332, 'notes2', \"lot\"), (234725332, 'notes2', \"of\"), "
      "(234725332, 'notes2', \"pars\"), (234725332, 'notes2', \"to\"), "
      "(234725332, 'notes2', \"word\")");

}

BOOST_AUTO_TEST_CASE(FieldWithOneWordWorks) {
  IndexTableInsertBuilder builder("keywords", "stems", set<string>());

  string row_id("18");

  Knot data(new string(".!?word  "));

  string keyword_statement;
  string stem_statement;

  builder.GetInsertStatements(row_id, "notes4", data,
                              &keyword_statement, &stem_statement);

  BOOST_CHECK_EQUAL(
      keyword_statement,
      "INSERT into keywords (id, col, word) VALUES "
      "(18, 'notes4', \"word\")");

  BOOST_CHECK_EQUAL(
      stem_statement,
      "INSERT into stems (id, col, word) VALUES "
      "(18, 'notes4', \"word\")");
}


// Checks that a field that contains exactly no actual words (all stop-words or
// delimiters) doesn't cause errors. It should just return empty statements.
BOOST_AUTO_TEST_CASE(NoWordsWorks) {
  IndexTableInsertBuilder builder("keywords", "stems", set<string>());

  string row_id("18");

  Knot data(new string(".!? ;"));

  string keyword_statement;
  string stem_statement;

  builder.GetInsertStatements(row_id, "notes4", data,
                              &keyword_statement, &stem_statement);

  BOOST_CHECK_EQUAL(keyword_statement, "");

  BOOST_CHECK_EQUAL(stem_statement, "");
}

