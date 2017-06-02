//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for the string algorithms. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 May 2012   omd            Original Version
//*****************************************************************

#include "string-algo.h"

#define BOOST_TEST_MODULE StringAlgoTest

#include <boost/assign/list_of.hpp>
#include <limits>
#include <string>
#include <vector>

#include "test-init.h"

using std::string;
using std::vector;

BOOST_AUTO_TEST_CASE(SplitWorks) {
  vector<string> t1 = Split("No delimiter", ',');
  BOOST_REQUIRE_EQUAL(t1.size(), 1);
  BOOST_CHECK_EQUAL(t1[0], "No delimiter");

  vector<string> t2 = Split("a,b,c", ',');
  BOOST_REQUIRE_EQUAL(t2.size(), 3);
  BOOST_CHECK_EQUAL(t2[0], "a");
  BOOST_CHECK_EQUAL(t2[1], "b");
  BOOST_CHECK_EQUAL(t2[2], "c");

  vector<string> t3 = Split("long 1\nlonger length 2\n\nfoo", '\n');
  BOOST_REQUIRE_EQUAL(t3.size(), 4);
  BOOST_CHECK_EQUAL(t3[0], "long 1");
  BOOST_CHECK_EQUAL(t3[1], "longer length 2");
  BOOST_CHECK_EQUAL(t3[2], "");
  BOOST_CHECK_EQUAL(t3[3], "foo");

  vector<string> t4 = Split(",,", ',');
  BOOST_REQUIRE_EQUAL(t4.size(), 3);
  BOOST_CHECK_EQUAL(t4[0], "");
  BOOST_CHECK_EQUAL(t4[1], "");
  BOOST_CHECK_EQUAL(t4[2], "");
}

BOOST_AUTO_TEST_CASE(ToUpperWorks) {
  string s1("abcDEFghizZQm");
  ToUpper(&s1);
  BOOST_CHECK_EQUAL(s1, "ABCDEFGHIZZQM");

  // Note: the @`[{ characters are the ascii codes just before and after a, z,
  // A, and Z so these are good edge cases.
  string s2("za$%mn!.?@`[{hello");
  ToUpper(&s2);
  BOOST_CHECK_EQUAL(s2, "ZA$%MN!.?@`[{HELLO");
}

BOOST_AUTO_TEST_CASE(ToLowerWorks) {
  string s1("ABcdeFGH ijKLm");
  ToLower(&s1);
  BOOST_CHECK_EQUAL(s1, "abcdefgh ijklm");

  string s2(" @#$*ZAmk@#4AA");
  ToLower(&s2);
  BOOST_CHECK_EQUAL(s2, " @#$*zamk@#4aa");
}

BOOST_AUTO_TEST_CASE(JoinWorks) {
  vector<string> data;
  data.push_back("Long part 1");
  data.push_back("p2");
  data.push_back("and part 3");

  BOOST_CHECK_EQUAL(Join(data, ","), "Long part 1,p2,and part 3");
  BOOST_CHECK_EQUAL(Join(data, " BIGDELIM "),
                    "Long part 1 BIGDELIM p2 BIGDELIM and part 3");
}

// This checks that SafeAtoi can convert valid values. It does *not* check that
// it crashes the program on invalid values. We should add that but we require
// death tests to do it.
//
// TODO(odain) Add death tests that ensure SafeAtoi crashes on bad input. See
// bug #789.
BOOST_AUTO_TEST_CASE(SafeAtoiWorks) {
  vector<int> test_values = boost::assign::list_of(-1)(0)(1)(100)(-285)(372)
                                           (std::numeric_limits<int>::min())
                                           (std::numeric_limits<int>::max());

  for (vector<int>::const_iterator i = test_values.begin();
       i != test_values.end(); ++i) {
    string str_value = itoa(*i);
    BOOST_CHECK_EQUAL(SafeAtoi(str_value), *i);
  }

  // And just to double check, we'll manually check a few of these in case atoi
  // is doing something weird.
  BOOST_CHECK_EQUAL(SafeAtoi("-118"), -118);
  BOOST_CHECK_EQUAL(SafeAtoi("0"), 0);
  BOOST_CHECK_EQUAL(SafeAtoi("1"), 1);
  BOOST_CHECK_EQUAL(SafeAtoi("83"), 83);
}

BOOST_AUTO_TEST_CASE(ConvertStringWorks) {
  // TODO(njhwang) figure out how to make this extract to (u)int8_t
  // (istringstream doesn't seem to support this?)
  //BOOST_CHECK_EQUAL(ConvertString<uint8_t>("0"), 0);
  //BOOST_CHECK_EQUAL(ConvertString<uint8_t>("255"), 255);
  //BOOST_CHECK_EQUAL(ConvertString<int8_t>("-128"), -128);
  //BOOST_CHECK_EQUAL(ConvertString<int8_t>("127"), 127);
  BOOST_CHECK_EQUAL(ConvertString<uint16_t>("0"), 0);
  BOOST_CHECK_EQUAL(ConvertString<uint16_t>("65535"), UINT16_MAX);
  BOOST_CHECK_EQUAL(ConvertString<int16_t>("-32768"), INT16_MIN);
  BOOST_CHECK_EQUAL(ConvertString<int16_t>("32767"), INT16_MAX);
  BOOST_CHECK_EQUAL(ConvertString<uint32_t>("0"), 0);
  BOOST_CHECK_EQUAL(ConvertString<uint32_t>("4294967295"), UINT32_MAX);
  BOOST_CHECK_EQUAL(ConvertString<int32_t>("-2147483648"), INT32_MIN);
  BOOST_CHECK_EQUAL(ConvertString<int32_t>("2147483647"), INT32_MAX);
  BOOST_CHECK_EQUAL(ConvertString<uint64_t>("0"), 0);
  BOOST_CHECK_EQUAL(ConvertString<uint64_t>("18446744073709551615"), 
                    UINT64_MAX);
  BOOST_CHECK_EQUAL(ConvertString<int64_t>("-9223372036854775808"),
                    INT64_MIN);
  BOOST_CHECK_EQUAL(ConvertString<int64_t>("9223372036854775807"),
                    INT64_MAX);
}

BOOST_AUTO_TEST_CASE(ConvertNumericWorks) {
  // TODO(njhwang) figure out how to make this extract to (u)int8_t
  // (ostringstream doesn't seem to support this?)
  //BOOST_CHECK_EQUAL(ConvertNumeric<uint8_t>(0), "0");
  //BOOST_CHECK_EQUAL(ConvertNumeric<uint8_t>(255), "255");
  //BOOST_CHECK_EQUAL(ConvertNumeric<int8_t>(-128), "-128");
  //BOOST_CHECK_EQUAL(ConvertNumeric<int8_t>(127), "127");
  BOOST_CHECK_EQUAL(ConvertNumeric<uint16_t>(0), "0");
  BOOST_CHECK_EQUAL(ConvertNumeric<uint16_t>(UINT16_MAX), "65535");
  BOOST_CHECK_EQUAL(ConvertNumeric<int16_t>(INT16_MIN), "-32768");
  BOOST_CHECK_EQUAL(ConvertNumeric<int16_t>(INT16_MAX), "32767");
  BOOST_CHECK_EQUAL(ConvertNumeric<uint32_t>(0), "0");
  BOOST_CHECK_EQUAL(ConvertNumeric<uint32_t>(UINT32_MAX), "4294967295");
  BOOST_CHECK_EQUAL(ConvertNumeric<int32_t>(INT32_MIN), "-2147483648");
  BOOST_CHECK_EQUAL(ConvertNumeric<int32_t>(INT32_MAX), "2147483647");
  BOOST_CHECK_EQUAL(ConvertNumeric<uint64_t>(0), "0");
  BOOST_CHECK_EQUAL(ConvertNumeric<uint64_t>(UINT64_MAX), 
                    "18446744073709551615");
  BOOST_CHECK_EQUAL(ConvertNumeric<int64_t>(INT64_MIN),
                    "-9223372036854775808");
  BOOST_CHECK_EQUAL(ConvertNumeric<int64_t>(INT64_MAX),
                    "9223372036854775807");
}
