//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for KnotLogger 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 13 Sep 2012   omd            Original Version
//*****************************************************************

#include "general-logger.h"

#define BOOST_TEST_MODULE KnotLoggerTest
#include "test-init.h"
#include "test-util.h"

#include <boost/assign/list_of.hpp>
#include <sstream>
#include <string>
#include <vector>

#include "string-algo.h"

using namespace std;
using boost::assign::list_of;

BOOST_AUTO_TEST_CASE(OstreamTimeLoggerWorks) {
  ostringstream* output = new ostringstream;
  OstreamElapsedTimeLogger logger(output);

  logger.Log("This is a test!");
  logger.Log("This is line 2.");

  string result = output->str();

  // The last "line" should be empty - it's there because there's a final "\n"
  // character.
  vector<string> exp_lines = 
    list_of("This is a test!$")
           ("This is line 2\\.$")("");
  VerifyTimeStampedInputLines(result, exp_lines);
}

BOOST_AUTO_TEST_CASE(OstreamRawLoggerWorks) {
  ostringstream* output = new ostringstream;
  OstreamRawTimeLogger logger(output);

  logger.Log("This is a test!");
  logger.Log("This is line 2.");

  string result = output->str();

  // The last "line" should be empty - it's there because there's a final "\n"
  // character.
  vector<string> exp_lines = 
    list_of("This is a test!$")
           ("This is line 2\\.$")("");
  VerifyTimeStampedInputLines(result, exp_lines);
}
