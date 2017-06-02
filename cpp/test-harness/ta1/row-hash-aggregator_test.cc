//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for RowHashAggregator 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************


#define BOOST_TEST_MODULE RowHashAggregatorTest
#include "common/test-init.h"

#include "row-hash-aggregator.h"

#include <boost/regex.hpp>
#include <string>
#include <vector>

#include "common/string-algo.h"

using std::string;
using std::vector;

BOOST_AUTO_TEST_CASE(SingleRowWorks) {
  RowHashAggregator agg;
  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("12345")));
  agg.AddPartialResult(Knot(new string("This will get hashed")));
  agg.AddPartialResult(Knot(new string("And so will this")));
  agg.AddPartialResult(Knot(new string("ENDROW")));
  agg.Done();

  Future<Knot> f = agg.GetFuture();

  // The result should start with the row id
  BOOST_CHECK_EQUAL(f.Value().ToString().find("12345 "), 0);

  // And following the row id should be a hex hash and a newline. Note that I'm
  // requiring the has be represented by a hex string that's *exactly* 32 bytes
  // long in hex. That is true of the MD5 sum hash I'm using but it sin't
  // strictly required by the interface of this class. However, we do want all
  // hashes to be the same length and this makes it much easier to write a
  // test.
  boost::regex expected("12345 [0-9a-f]{32}\n");

  BOOST_CHECK(boost::regex_match(f.Value().ToString(), expected));
}

BOOST_AUTO_TEST_CASE(DifferentDelimeterWorks) {
  RowHashAggregator agg1;
  agg1.AddPartialResult(Knot(new string("ROW")));
  agg1.AddPartialResult(Knot(new string("12345")));
  agg1.AddPartialResult(Knot(new string("This will get hashed")));
  agg1.AddPartialResult(Knot(new string("And so will this")));
  agg1.AddPartialResult(Knot(new string("ENDROW")));
  agg1.Done();

  RowHashAggregator agg2("INSERT", "ENDINSERT");
  agg2.AddPartialResult(Knot(new string("INSERT")));
  agg2.AddPartialResult(Knot(new string("12345")));
  agg2.AddPartialResult(Knot(new string("This will get hashed")));
  agg2.AddPartialResult(Knot(new string("And so will this")));
  agg2.AddPartialResult(Knot(new string("ENDINSERT")));
  agg2.Done();

  Future<Knot> f1 = agg1.GetFuture();
  Future<Knot> f2 = agg2.GetFuture();

  // The results should be equal
  BOOST_CHECK_EQUAL(f1.Value().ToString(), f2.Value().ToString());
}

BOOST_AUTO_TEST_CASE(MultipleRowsWork) {
  RowHashAggregator agg;
  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("12345")));
  agg.AddPartialResult(Knot(new string("This will get hashed")));
  agg.AddPartialResult(Knot(new string("And so will this")));
  agg.AddPartialResult(Knot(new string("ENDROW")));

  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("78910")));
  agg.AddPartialResult(Knot(new string("Different values in the rows")));
  agg.AddPartialResult(Knot(new string("And this is not the same")));
  agg.AddPartialResult(Knot(new string("ENDROW")));
  agg.Done();

  Future<Knot> f = agg.GetFuture();

  vector<string> result_lines = Split(f.Value().ToString(), '\n');
  // Since it ends with a newline there should be 3 strings in the vector but
  // the last should be empty.
  BOOST_REQUIRE_EQUAL(result_lines.size(), 3);
  BOOST_CHECK_EQUAL(result_lines[2], "");

  // See the test above for an explanation of the regex here.
  boost::regex expected0("12345 [0-9a-f]{32}");
  BOOST_CHECK_EQUAL(result_lines[0].find("12345 "), 0);
  BOOST_CHECK(boost::regex_match(result_lines[0], expected0));

  boost::regex expected1("78910 [0-9a-f]{32}");
  BOOST_CHECK_EQUAL(result_lines[1].find("78910 "), 0);
  BOOST_CHECK(boost::regex_match(result_lines[1], expected1));
}

// Make sure things will work for "select id ..." queries.
BOOST_AUTO_TEST_CASE(IdOnlyWorks) {
  RowHashAggregator agg;
  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("12345")));
  agg.AddPartialResult(Knot(new string("ENDROW")));

  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("78910")));
  agg.AddPartialResult(Knot(new string("ENDROW")));
  agg.Done();

  Future<Knot> f = agg.GetFuture();

  vector<string> result_lines = Split(f.Value().ToString(), '\n');
  // Since it ends with a newline there should be 3 strings in the vector but
  // the last should be empty.
  BOOST_REQUIRE_EQUAL(result_lines.size(), 3);
  BOOST_CHECK_EQUAL(result_lines[2], "");

  BOOST_CHECK_EQUAL(result_lines[0], "12345");
  BOOST_CHECK_EQUAL(result_lines[1], "78910");

}

// Make sure we handle FAILED messages correctly.
BOOST_AUTO_TEST_CASE(FailedMessagesWork) {
  RowHashAggregator agg;
  agg.AddPartialResult(Knot(new string("FAILED")));
  agg.AddPartialResult(Knot(new string("Bad things happened.")));
  agg.AddPartialResult(Knot(new string("So I sent FAILED.")));
  agg.AddPartialResult(Knot(new string("ENDFAILED")));
  agg.Done();

  Future<Knot> f = agg.GetFuture();

  BOOST_CHECK_EQUAL(f.Value(),
                    "FAILED\nBad things happened.\nSo I sent FAILED.\n"
                    "ENDFAILED\n");
}

// Make sure we handle a mixture of row and FAILED messages correctly.
BOOST_AUTO_TEST_CASE(MixedMessagesWork) {
  RowHashAggregator agg;
  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("12345")));
  agg.AddPartialResult(Knot(new string("ENDROW")));

  agg.AddPartialResult(Knot(new string("FAILED")));
  agg.AddPartialResult(Knot(new string("Bad things happened.")));
  agg.AddPartialResult(Knot(new string("So I sent FAILED.")));
  agg.AddPartialResult(Knot(new string("ENDFAILED")));

  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("78910")));
  agg.AddPartialResult(Knot(new string("ENDROW")));

  agg.Done();

  Future<Knot> f = agg.GetFuture();

  vector<string> result_lines = Split(f.Value().ToString(), '\n');
  // Since it ends with a newline there should be an extra empty string in the
  // vector.
  BOOST_REQUIRE_EQUAL(result_lines.size(), 7);
  BOOST_CHECK_EQUAL(result_lines[6], "");

  BOOST_CHECK_EQUAL(result_lines[0], "12345");

  BOOST_CHECK_EQUAL(result_lines[1], "FAILED");
  BOOST_CHECK_EQUAL(result_lines[2], "Bad things happened.");
  BOOST_CHECK_EQUAL(result_lines[3], "So I sent FAILED.");
  BOOST_CHECK_EQUAL(result_lines[4], "ENDFAILED");

  BOOST_CHECK_EQUAL(result_lines[5], "78910");
}

// Make sure we handle multiple FAILED messages correctly.
BOOST_AUTO_TEST_CASE(MultipleFailedMessagesWork) {
  RowHashAggregator agg;
  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("12345")));
  agg.AddPartialResult(Knot(new string("ENDROW")));

  agg.AddPartialResult(Knot(new string("FAILED")));
  agg.AddPartialResult(Knot(new string("Bad things happened.")));
  agg.AddPartialResult(Knot(new string("So I sent FAILED.")));
  agg.AddPartialResult(Knot(new string("ENDFAILED")));

  agg.AddPartialResult(Knot(new string("FAILED")));
  agg.AddPartialResult(Knot(new string("Bad things happened again.")));
  agg.AddPartialResult(Knot(new string("So I sent FAILED again.")));
  agg.AddPartialResult(Knot(new string("ENDFAILED")));

  agg.AddPartialResult(Knot(new string("ROW")));
  agg.AddPartialResult(Knot(new string("78910")));
  agg.AddPartialResult(Knot(new string("ENDROW")));

  agg.AddPartialResult(Knot(new string("FAILED")));
  agg.AddPartialResult(Knot(new string("Bad things happened AGAIN.")));
  agg.AddPartialResult(Knot(new string("So I sent FAILED...again.")));
  agg.AddPartialResult(Knot(new string("ENDFAILED")));

  agg.Done();

  Future<Knot> f = agg.GetFuture();

  vector<string> result_lines = Split(f.Value().ToString(), '\n');
  // Since it ends with a newline there should be an extra empty string in the
  // vector.
  BOOST_REQUIRE_EQUAL(result_lines.size(), 15);
  BOOST_CHECK_EQUAL(result_lines[14], "");

  BOOST_CHECK_EQUAL(result_lines[0], "12345");

  BOOST_CHECK_EQUAL(result_lines[1], "FAILED");
  BOOST_CHECK_EQUAL(result_lines[2], "Bad things happened.");
  BOOST_CHECK_EQUAL(result_lines[3], "So I sent FAILED.");
  BOOST_CHECK_EQUAL(result_lines[4], "ENDFAILED");

  BOOST_CHECK_EQUAL(result_lines[5], "FAILED");
  BOOST_CHECK_EQUAL(result_lines[6], "Bad things happened again.");
  BOOST_CHECK_EQUAL(result_lines[7], "So I sent FAILED again.");
  BOOST_CHECK_EQUAL(result_lines[8], "ENDFAILED");

  BOOST_CHECK_EQUAL(result_lines[9], "78910");

  BOOST_CHECK_EQUAL(result_lines[10], "FAILED");
  BOOST_CHECK_EQUAL(result_lines[11], "Bad things happened AGAIN.");
  BOOST_CHECK_EQUAL(result_lines[12], "So I sent FAILED...again.");
  BOOST_CHECK_EQUAL(result_lines[13], "ENDFAILED");
}
