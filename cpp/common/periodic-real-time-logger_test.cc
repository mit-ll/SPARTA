//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit test for PeriodicRealTimeLogger
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Jan 2013   ni24039        Original Version
//*****************************************************************

#define BOOST_TEST_MODULE PeriodicRealTimeLoggerTest

#include "test-init.h"
#include "test-util.h"

#include "periodic-real-time-logger.h"
#include "general-logger.h"
#include "util.h"

#include <boost/assign/list_of.hpp>
#include <sstream>
#include <string>
#include <vector>
#include <chrono>
#include <thread>

using namespace std;
using boost::assign::list_of;

BOOST_AUTO_TEST_CASE(PeriodicRealTimeLoggerWorks) {
  ostringstream* output = new ostringstream;
  OstreamElapsedTimeLogger logger(output);
  std::unique_ptr<std::thread> logger_thread;

  auto logger_fn = [&logger]() {
    LogRealTime(&logger);
    this_thread::sleep_for(chrono::milliseconds(1000));
    LogRealTime(&logger);
    this_thread::sleep_for(chrono::milliseconds(1000));
    LogRealTime(&logger);
  };

  PeriodicRealTimeLogger timestamper(&logger, 1);
  timestamper.Start();
  logger_thread.reset(new thread(logger_fn));
  this_thread::sleep_for(chrono::milliseconds(3500));
  timestamper.Stop();
  logger_thread->join();
  string result = output->str();
  vector<string> exp_lines = 
    list_of("EPOCH_TIME: \\d+\\.\\d+$")
           ("EPOCH_TIME: \\d+\\.\\d+$")
           ("EPOCH_TIME: \\d+\\.\\d+$")
           ("EPOCH_TIME: \\d+\\.\\d+$")
           ("EPOCH_TIME: \\d+\\.\\d+$")
           ("EPOCH_TIME: \\d+\\.\\d+$")
           ("EPOCH_TIME: \\d+\\.\\d+$")("");
  VerifyTimeStampedInputLines(result, exp_lines);
}
