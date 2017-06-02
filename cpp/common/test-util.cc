//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Various test utilites. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Dec 2012   ni24039        Original Version
//*****************************************************************

#include "test-util.h"

#include <boost/test/unit_test.hpp>
#include <boost/regex.hpp>

#include "string-algo.h"
#include "check.h"

void VerifyIStreamContents(const std::vector<std::string>& expected_contents, 
                           std::istream* input_stream) {
  std::string actual_content;
  for (auto expected_content : expected_contents) {
    CHECK(input_stream->good());
    getline(*input_stream, actual_content);
    BOOST_CHECK_EQUAL(actual_content, expected_content);
    actual_content.clear();
  }
}

void VerifyInputLines(const std::string& input,
                      const std::vector<std::string>& exp_lines) {
  std::vector<std::string> input_lines = Split(input, '\n');
  BOOST_REQUIRE_MESSAGE(
      input_lines.size() == exp_lines.size(),
      "Expected only " << exp_lines.size() 
      << " lines in the input. Found the following "
      << input_lines.size() << " lines:\n"
      << input);

  for (size_t i = 0; i < exp_lines.size(); i++) {
    boost::regex exp_regex(exp_lines[i]);
    BOOST_CHECK_MESSAGE(boost::regex_match(input_lines[i], exp_regex),
        "Unexpected input line:\nReceived: " << input_lines[i]);
  }
}

void VerifyTimeStampedInputLines(const std::string& input,
                                 std::vector<std::string> exp_lines) {
  for (size_t i = 0; i < exp_lines.size(); i++) {
    if (exp_lines[i].length() > 0) {
      exp_lines[i] = "^\\[\\d+\\.\\d+\\] " + exp_lines[i];
    }
  }
  VerifyInputLines(input, exp_lines);
}
