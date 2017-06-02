//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for the logging stuff. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 16 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE LoggingTest

#include "logging.h"

#include <sstream>

#include "test-init.h"

using std::stringstream;

// Tests that basic logging, where all logs end up in the same same log file,
// work as expected.
BOOST_AUTO_TEST_CASE(SingleFileLogPolicyWorks) {
  stringstream output;
  Log::SetOutputStream(&output);

  LOG(DEBUG) << "Message 1";
  LOG(INFO) << "Message 2";
  LOG(WARNING) << "Message 3";
  LOG(ERROR) << "Message 4";


  Log::SetApplicationLogLevel(WARNING);

  LOG(DEBUG) << "Should not be logged";
  LOG(INFO) << "Should not be logged either";
  LOG(WARNING) << "Message 5";
  LOG(ERROR) << "Message 6";

  // Now change the log level via preprocessor. That should cause all log
  // messages below ERROR to not even be compiled in!
#undef MIN_LOG_LEVEL
#define MIN_LOG_LEVEL 3
  LOG(DEBUG) << "Not Logged";
  LOG(INFO) << "Not Logged";
  LOG(WARNING) << "Not Logged";
  LOG(ERROR) << "Message 7";

  std::string output_str = output.str();
  BOOST_CHECK(output_str.find("Message 1\n") != std::string::npos);
  BOOST_CHECK(output_str.find("Message 2\n") != std::string::npos);
  BOOST_CHECK(output_str.find("Message 3\n") != std::string::npos);
  BOOST_CHECK(output_str.find("Message 4\n") != std::string::npos);
  BOOST_CHECK(output_str.find("Message 5\n") != std::string::npos);
  BOOST_CHECK(output_str.find("Message 6\n") != std::string::npos);
  BOOST_CHECK(output_str.find("Message 7\n") != std::string::npos);
  
  BOOST_CHECK(output_str.find("Should not") == std::string::npos);
  BOOST_CHECK(output_str.find("Not Logged") == std::string::npos);

}
