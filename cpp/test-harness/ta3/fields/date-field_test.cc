//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for DateField 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jan 2013   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE DateFieldTest
#include "common/test-init.h"

#include "date-field.h"

#include <boost/assign/list_inserter.hpp>
#include <map>
#include <sstream>
#include <string>

#include "field-set.h"


using namespace std;
namespace ba = boost::assign;

BOOST_AUTO_TEST_CASE(NumValuesWorks) {
  DateField df1("testing", "2012-01-29", "2012-01-31");
  // Should be 2 possible data values: 1/29 and 1/30 (the end value is
  // exclusive).
  BOOST_CHECK_EQUAL(df1.NumValues(), 2);

  DateField df2("testing", "2012-01-29", "2012-02-01");
  // Should be 3 possible values: 1/29. 1/30, and 1/31
  BOOST_CHECK_EQUAL(df2.NumValues(), 3);

  DateField df3("testing", "2012-01-01", "2013-01-01");
  // 2012 was a leap year so there should be 366 days
  BOOST_CHECK_EQUAL(df3.NumValues(), 366);

  DateField df4("test", "2013-01-01", "2014-01-01");
  // 2013 is not a leap year so we expect 365
  BOOST_CHECK_EQUAL(df4.NumValues(), 365);

  DateField df5("test", "2013-02-21", "2014-02-21");
  // Should still be 365 days.
  BOOST_CHECK_EQUAL(df5.NumValues(), 365);
}

// Create a date field that can only generate one of two dates. Generate a few
// hundred dates and make sure only the two expected values are seen and that
// they're both seen roughly equally. To test the equality we assume that the
// number of times each value was seen should have a binomial distribution. If
// we generate 100 values the probability of seeing one of the two values less
// than 27 times is less than 1 in 1 million.
BOOST_AUTO_TEST_CASE(RandomValueSmallRangeWorks) {
  DateField df("test field", "2013-01-31", "2013-02-02");

  map<string, int> obs_counts;
  obs_counts["2013-01-31"] = 0;
  obs_counts["2013-02-01"] = 0;

  for (int i = 0; i < 100; ++i) {
    char buffer[df.MaxLength()];
    char* end_c = df.RandomValue(df.MaxLength(), buffer);
    string date(buffer, end_c - buffer);
    BOOST_CHECK_MESSAGE(
        obs_counts.find(date) != obs_counts.end(),
        "Only expected dates are 2013-01-31 and 2013-02-01 but "
        << date << " was generated");
    obs_counts[date] += 1;
  }

  BOOST_CHECK_EQUAL(obs_counts.size(), 2);
  BOOST_CHECK_EQUAL(obs_counts["2013-01-31"] + obs_counts["2013-02-01"], 100);

  BOOST_CHECK_GE(obs_counts["2013-01-31"], 27);
  BOOST_CHECK_GE(obs_counts["2013-02-01"], 27);
}

// Create a date field that could generate 2013-01-31, 2013-02-01, or
// 2013-02-02. Then exclude the 1st and last and call RandomValueExcluding. We
// should always get back the middle value.
BOOST_AUTO_TEST_CASE(RandomValueExcludingWorks) {
  set<string> exclude_vals;
  ba::insert(exclude_vals)("2013-01-31")("2013-02-02");
  DateField df("test", "2013-01-31", "2013-02-03");

  BOOST_CHECK_EQUAL(df.NumValues(), 3);

  for (int i = 0; i < 10; ++i) {
    char buffer[df.MaxLength()];
    char* end_c = df.RandomValueExcluding(exclude_vals, df.MaxLength(), buffer);
    string date(buffer, end_c - buffer);
    BOOST_CHECK_EQUAL(date, "2013-02-01");
  }
}

// Check that we can construct a date field using a file and a FieldSet.
BOOST_AUTO_TEST_CASE(DateFieldFromConfigFileWorks) {
  FieldSet fs;
  istringstream fields_file(
      "date1 DateField 1910-01-01 2013-02-01\n"
      "date2 DateField 1972-02-20 1972-02-24\n");
  fs.AppendFromFile(&fields_file);

  BOOST_CHECK_EQUAL(fs.Size(), 2);

  BOOST_CHECK_EQUAL(fs.Get(0)->name(), "date1");
  BOOST_CHECK_EQUAL(fs.Get(1)->name(), "date2");

  BOOST_CHECK_EQUAL(fs.Get(1)->NumValues(), 4);
  // The correct value of 37652 was generated via Python's datetime library.
  BOOST_CHECK_EQUAL(fs.Get(0)->NumValues(), 37652);
}
