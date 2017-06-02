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

#ifndef CPP_COMMON_TEST_UTIL_H_
#define CPP_COMMON_TEST_UTIL_H_

#include <iostream>
#include <string>
#include <vector>

/// Performs BOOST_EQUAL_CHECKs on the provided istream against each string in
/// expected_contents. Note that this extracts characters from the istream, and
/// thereby modifies the istream. Also note that all CHECKs can pass while still
/// leaving more data in the istream. This only verifies that all contents in
/// expected_contents are in input_stream in the specified order.
void VerifyIStreamContents(const std::vector<std::string>& expected_contents, 
                           std::istream* input_stream);

/// input should be a \n separated string, while exp_lines should be a vector of
/// the expected lines in input. Each line in exp_lines can be a regular
/// expressions. Checks will fail if there are an unexpected number of lines in
/// input, or if any of the lines in input fail the regular expression checks.
void VerifyInputLines(const std::string& input,
                      const std::vector<std::string>& exp_lines);

/// Same as the above, but prepends a time stamp regex to all non-empty lines in
/// exp_lines. This assumes the time stamp regex format is a bracketed floating
/// point number; if this changes, this function can be expanded to take the time
/// stamp regex string as an argument. 
void VerifyTimeStampedInputLines(const std::string& input,
                                 std::vector<std::string> exp_lines);

#endif
