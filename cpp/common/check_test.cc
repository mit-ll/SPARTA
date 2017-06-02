//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for the functions in check.h 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 03 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE CheckTest

#include <boost/regex.hpp>
#include <iostream>
#include <string>
#include <vector>

#include "logging.h"
#include "string-algo.h"
#include "test-init.h"

#define NO_DEATH_ON_CHECK_FAIL

#include "check.h"

using boost::regex_search;
using boost::regex;
using std::string;
using std::vector;

BOOST_AUTO_TEST_CASE(CheckBasic) {
  std::stringstream test_stream;
  Log::SetOutputStream(&test_stream);
  // TODO(njhwang) unit test is failing here for some reason
  // Simplest failing check I could think of.
  CHECK(false);
  // Check that the error message has the expected format.
  regex expected_re(
      "Check 'false' failed in .*check_test.cc on line \\d+");
  BOOST_CHECK(regex_search(test_stream.str(), expected_re));

  // Check a slightly more complicated test.
  test_stream.str("");
  CHECK(7 == 11);
  expected_re = "Check '7 == 11' failed in .*check_test.cc on line \\d+";
  BOOST_CHECK(regex_search(test_stream.str(), expected_re));
}

// Since NDEBUG is not defined DCHECK should work exactly the same way as
// CHECK
#ifndef NDEBUG
BOOST_AUTO_TEST_CASE(DCheckBasic) {
  std::stringstream test_stream;
  Log::SetOutputStream(&test_stream);
  // Simplest failing check I could think of.
  DCHECK(false);
  // Check that the error message has the expected format.
  regex expected_re(
      "Check 'false' failed in .*check_test.cc on line \\d+");
  BOOST_CHECK(regex_search(test_stream.str(), expected_re));

  // Check a slightly more complicated test.
  test_stream.str("");
  CHECK(7 == 11);
  expected_re = "Check '7 == 11' failed in .*check_test.cc on line \\d+";
  BOOST_CHECK(regex_search(test_stream.str(), expected_re));
  
}
#endif

// Make sure you can use a CHECK as an output stream.
BOOST_AUTO_TEST_CASE(CheckAsStream) {
  std::stringstream test_stream;
  Log::SetOutputStream(&test_stream);

  CHECK(false) << "This is my output: " << 22;
  vector<string> lines = Split(test_stream.str(), '\n');
  BOOST_REQUIRE_EQUAL(lines.size(), 3);
  regex expected_line_1_re(
      "Check 'false' failed in .*check_test.cc on line \\d+");
  BOOST_CHECK(regex_search(lines[0], expected_line_1_re));
  BOOST_CHECK_EQUAL(lines[1], "This is my output: 22");
  BOOST_CHECK_EQUAL(lines[2], "");
}
