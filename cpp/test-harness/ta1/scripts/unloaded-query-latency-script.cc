//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of UnloadedQueryLatencyScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************

#include "unloaded-query-latency-script.h"

#include "common/safe-file-stream.h"
#include "common/general-logger.h"
#include "common/string-algo.h"
#include "common/future.h"
#include "common/knot.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/delay-generators.h"
#include "test-harness/ta1/query-command.h"

using namespace std;

UnloadedQueryLatencyScript::UnloadedQueryLatencyScript(
      std::istream* query_list_file, int num_iterations,
      QueryListScript::DelayFunction delay_function, 
      QueryCommand* query_command, GeneralLogger* logger)
    : QueryListScript(query_list_file, num_iterations, delay_function,
                      query_command, logger) {
}

void UnloadedQueryLatencyScript::Run() {
  // Run a query and wait for it to complete before running the next one. That
  // way there's only 1 query at a time in the system.
  LOG(INFO) << "Starting UnloadedQueryLatencyScript";

  int delay_us = delay_function_();
  if (delay_us > 0) {
    boost::this_thread::sleep(boost::posix_time::microseconds(delay_us));
  }

  for (int iteration = 0; iteration < num_iterations_; ++iteration) {
    for (size_t i = 0; i < queries_.size(); ++i) {
      Future<Knot> future = 
        query_command_->Schedule(i, query_ids_[i], queries_[i], logger_);
      future.Wait();
      int delay_us = delay_function_();
      if (delay_us > 0) {
        boost::this_thread::sleep(boost::posix_time::microseconds(delay_us));
      }
    }
  }
  logger_->Flush();
}

////////////////////////////////////////////////////////////////////////////////
// UnloadedQLSConstructor
////////////////////////////////////////////////////////////////////////////////

UnloadedQLSConstructor::UnloadedQLSConstructor(
    QueryCommand* query_command) : query_command_(query_command) {
}

TestScript* UnloadedQLSConstructor::operator()(
    const string& config_line, const string& dir_path,
    GeneralLogger* logger) {
  vector<string> config_parts = Split(config_line, ' ');
  CHECK(config_parts.size() >= 2 && config_parts.size() <= 4);
  string query_list_path = dir_path;
  DCHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  query_list_path += config_parts[0];
  SafeIFStream query_file(query_list_path.c_str());

  int num_iters = atoi(config_parts[1].c_str());
  CHECK(num_iters > 0);

  if (config_parts.size() > 2) {
    if (config_parts[2] == "NO_DELAY") {
      CHECK(config_parts.size() == 3);
      return new UnloadedQueryLatencyScript(
        &query_file, num_iters, &ZeroDelay, query_command_, logger);
    } else {
      CHECK(config_parts[2] == "FIXED_DELAY");
      CHECK(config_parts.size() == 4);
      // TODO(njhwang) use strol instead so we can do better error checking.
      int delay_micros = atoi(config_parts[3].c_str());
      FixedDelayFunctor e_delay(delay_micros);
      return new UnloadedQueryLatencyScript(
        &query_file, num_iters, e_delay, query_command_, logger);
    }
  } else {
    return new UnloadedQueryLatencyScript(
      &query_file, num_iters, &ZeroDelay, query_command_, logger);
  }
}
