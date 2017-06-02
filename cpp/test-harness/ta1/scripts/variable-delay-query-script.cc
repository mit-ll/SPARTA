//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of VariableDelayQueryScript. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************

#include "variable-delay-query-script.h"

#include <limits>
#include <chrono>
#include <thread>

#include "common/future-waiter.h"
#include "common/general-logger.h"
#include "common/safe-file-stream.h"
#include "common/types.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/ta1/query-command.h"
#include "test-harness/common/delay-generators.h"

using namespace std;

VariableDelayQueryScript::VariableDelayQueryScript(
      std::istream* query_list_file, int num_iterations,
      QueryCommand* query_command, GeneralLogger* logger,
      QueryListScript::DelayFunction delay_function)
    : QueryListScript(query_list_file, num_iterations,
                      delay_function, query_command, logger),
      should_stop_(false), script_complete_(false) {
  if (num_iterations_ == -1) {
    LOG(DEBUG) << "VariableDelayQueryScript will run until "
        << "Terminate() is called.";
    num_iterations_ = numeric_limits<int>::max();
  }
}

void VariableDelayQueryScript::Run() {
  LOG(INFO) << "Starting VariableDelayQueryScript";

  FutureWaiter<Knot> waiter;
  bool quitting = false;
  for (int iteration = 0; iteration < num_iterations_; ++iteration) {
    for (size_t i = 0; i < queries_.size(); ++i) {
      waiter.Add(
         query_command_->Schedule(i, query_ids_[i], queries_[i], logger_)); 
      int delay_us = delay_function_();
      if (delay_us > 0) {
        std::this_thread::sleep_for(std::chrono::microseconds(delay_us));
      }
      {
        MutexGuard l(should_stop_tex_);
        if (should_stop_) {
          LOG(INFO) << "VariableDelayQueryScript interrupted. Exiting";
          quitting = true;
          break;
        }
      }
    }
    if (quitting) {
      break;
    }
  }

  waiter.Wait();
  logger_->Flush();
  LOG(INFO) << "Finished VariableDelayQueryScript";
  script_complete_.Set(true);
}

void VariableDelayQueryScript::Terminate() {
  {
    MutexGuard l(should_stop_tex_);
    should_stop_ = true;
  }
  script_complete_.Wait(true);
  logger_->Flush();
}

////////////////////////////////////////////////////////////////////////////////
// VariableDelayScriptConstructor
////////////////////////////////////////////////////////////////////////////////

VariableDelayScriptConstructor::VariableDelayScriptConstructor(
    QueryCommand* query_command)
    : query_command_(query_command) {
}

TestScript* VariableDelayScriptConstructor::operator()(
    const string& config_line, const string& dir_path,
    GeneralLogger* logger) {
  vector<string> config_parts = Split(config_line, ' ');
  CHECK(config_parts.size() >= 3);

  string query_list_path = dir_path;
  CHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  query_list_path += config_parts[0];
  SafeIFStream query_file(query_list_path.c_str());

  int num_iters = atoi(config_parts[1].c_str());
  CHECK(num_iters > 0);

  if (config_parts[2] == "NO_DELAY") {
    CHECK(config_parts.size() == 3);
    return new VariableDelayQueryScript(
        &query_file, num_iters, query_command_, logger,
        &ZeroDelay);
  } else {
    CHECK(config_parts[2] == "EXPONENTIAL_DELAY")
        << "Unknown delay type: " << config_parts[2];
    CHECK(config_parts.size() == 4);
    int delay_micros = atoi(config_parts[3].c_str());
    const int kRandomSeed = 0;
    ExponentialDelayFunctor e_delay(delay_micros, kRandomSeed);
    return new VariableDelayQueryScript(
        &query_file, num_iters, query_command_, logger,
        e_delay);
  }
}
