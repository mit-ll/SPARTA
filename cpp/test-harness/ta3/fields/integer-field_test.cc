//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for IntegerField 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jan 2013   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE IntegerFieldTest
#include "common/test-init.h"

#include "integer-field.h"

#include <boost/assign/list_inserter.hpp>
#include <map>
#include <string>

using namespace std;
namespace ba = boost::assign;

BOOST_AUTO_TEST_CASE(NumValuesWorks) {
  IntegerField int_f1("testing", "%d", 10, 13);
  // 10, 11, and 12 are the only legal values.
  BOOST_CHECK_EQUAL(int_f1.NumValues(), 3);

  IntegerField int_f2("testing", "%d", 0, 20);
  // 10, 11, and 12 are the only legal values.
  BOOST_CHECK_EQUAL(int_f2.NumValues(), 20);
}

BOOST_AUTO_TEST_CASE(MaxLengthWorks) {
  IntegerField f1("test", "%d", 0, 5);
  BOOST_CHECK_EQUAL(f1.MaxLength(), 1);

  IntegerField f2("test", "%d", 0, 10);
  // End is exclusive so max val == 9
  BOOST_CHECK_EQUAL(f2.MaxLength(), 1);

  IntegerField f3("test", "%d", -9, 10);
  // The end of the range is exclusive so the max value is 9, but -9 requires 2
  // characters.
  BOOST_CHECK_EQUAL(f3.MaxLength(), 2);

  IntegerField f4("test", "%d", 0, 100);
  // The end of the range is exclusive so the largest value this can generate is
  // 99.
  BOOST_CHECK_EQUAL(f4.MaxLength(), 2);

  IntegerField f5("test", "%d", 99, 101);
  BOOST_CHECK_EQUAL(f5.MaxLength(), 3);

  IntegerField f6("test", "%d", 0, 101);
  BOOST_CHECK_EQUAL(f6.MaxLength(), 3);

  IntegerField f7("another test", "%d", 0, 105);
  BOOST_CHECK_EQUAL(f7.MaxLength(), 3);
}

// Create a field that can only generate one of two dates. Generate a
// hundred values and make sure only the two expected values are seen and that
// they're both seen roughly equally. To test the equality we assume that the
// number of times each value was seen should have a binomial distribution. If
// we generate 100 values the probability of seeing one of the two values less
// than 27 times is less than 1 in 1 million.
BOOST_AUTO_TEST_CASE(DistributionCorrect) {
  IntegerField f("test field", "%d", 1, 3);

  map<string, int> obs_counts;
  obs_counts["1"] = 0;
  obs_counts["2"] = 0;

  for (int i = 0; i < 100; ++i) {
    char buffer[f.MaxLength()];
    char* end_c = f.RandomValue(f.MaxLength(), buffer);
    string val(buffer, end_c - buffer);
    BOOST_CHECK_MESSAGE(
        obs_counts.find(val) != obs_counts.end(),
        "Only expected values are 1 and 2 but "
        << val << " was generated");
    obs_counts[val] += 1;
  }

  BOOST_CHECK_EQUAL(obs_counts.size(), 2);
  BOOST_CHECK_EQUAL(obs_counts["1"] + obs_counts["2"], 100);

  BOOST_CHECK_GE(obs_counts["1"], 27);
  BOOST_CHECK_GE(obs_counts["2"], 27);
}

// Same as the above but we exclude some values leaving only legal ones left.
BOOST_AUTO_TEST_CASE(DistributionCorrectWithExclude) {
  set<string> exclude_vals;
  ba::insert(exclude_vals)("0")("1")("3");
  IntegerField f("test field", "%d", -1, 4);

  map<string, int> obs_counts;
  // These are the only values in [-1, 3) that haven't been excluded.
  obs_counts["-1"] = 0;
  obs_counts["2"] = 0;

  for (int i = 0; i < 100; ++i) {
    char buffer[f.MaxLength()];
    char* end_c = f.RandomValueExcluding(exclude_vals, f.MaxLength(), buffer);
    string val(buffer, end_c - buffer);
    BOOST_CHECK_MESSAGE(
        obs_counts.find(val) != obs_counts.end(),
        "Only expected values are 1 and 2 but "
        << val << " was generated");
    obs_counts[val] += 1;
  }

  BOOST_CHECK_EQUAL(obs_counts.size(), 2);
  BOOST_CHECK_EQUAL(obs_counts["-1"] + obs_counts["2"], 100);

  BOOST_CHECK_GE(obs_counts["-1"], 27);
  BOOST_CHECK_GE(obs_counts["2"], 27);
}

// Try an IntegerField with various format strings and make sure the right
// values get returned and that MaxLength() returns the expected values.
BOOST_AUTO_TEST_CASE(FormatStringsWork) {
  {
    IntegerField f("test", "%05d", 1, 3);
    BOOST_CHECK_EQUAL(f.MaxLength(), 5);
    char buffer[f.MaxLength()];
    char* end_ptr = f.RandomValue(f.MaxLength(), buffer);
    string result(buffer, end_ptr - buffer);
    BOOST_CHECK_MESSAGE(
        result == "00001" || result == "00002",
        "Expected 00001 or 00002 but got " << result);
  }

  {
    IntegerField f("test", "%+d", 1, 3);
    BOOST_CHECK_EQUAL(f.MaxLength(), 2);
    char buffer[f.MaxLength()];
    char* end_ptr = f.RandomValue(f.MaxLength(), buffer);
    string result(buffer, end_ptr - buffer);
    BOOST_CHECK_MESSAGE(
        result == "+1" || result == "+2",
        "Expected +1 or +2 but got " << result);
  }

  {
    IntegerField f("test", "foo %02d bar", 1, 3);
    BOOST_CHECK_EQUAL(f.MaxLength(), 10);
    char buffer[f.MaxLength()];
    char* end_ptr = f.RandomValue(f.MaxLength(), buffer);
    string result(buffer, end_ptr - buffer);
    BOOST_CHECK_MESSAGE(
        result == "foo 01 bar" || result == "foo 02 bar",
        "Expected 'foo 01 bar' or 'foo 02 bar' but got " << result);
  }

}
