//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A script that sends queries with a configurable delay
//                     between each query. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_VARIABLE_DELAY_QUERY_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_VARIABLE_DELAY_QUERY_SCRIPT_H_

#include "query-list-script.h"

#include <functional>
#include <thread>

#include "common/conditions.h"

class QueryCommand;
class GeneralLogger;
class DelayFunction;

/// This is constructed with a list of queries to be run and a DelayFunction.
/// Each call to DelayFunction returns the number of microseconds to wait before
/// *scheduling* the next query (if the SUT isn't in the READY state the query
/// command won't be sent).
///
/// Note: DelayFunction should produce reproducable results so that different
/// runs of the script on different performer systems produce identical results!
///
/// A few useful delay functions are included below.
class VariableDelayQueryScript : public QueryListScript {
 public:
  /// Asks the client to run each of the queries in query_list_file
  /// num_iterations times (will go through the entire file once before
  /// repeating. After each query is sent dealy_function is called and the script
  /// waits that many microseconds before scheudling the next query to send.
  ///
  /// If num_iterations == -1 this keeps sends the set of queries until
  /// Terminate() is called.
  ///
  /// Note: passing in a DealyFunction that always returns 0 allows this to
  /// measure throughput.
  VariableDelayQueryScript(
      std::istream* query_list_file, int num_iterations,
      QueryCommand* query_command, GeneralLogger* logger,
      DelayFunction delay_function);

  virtual ~VariableDelayQueryScript() {}

  virtual void Run();

  /// This script can be interrupted. When called this will wait for all
  /// already sent commands to complete but it won't send any new commands.
  virtual void Terminate();

 private:
  ///DelayFunction delay_function_;

  /// Set to true by Terminate()
  bool should_stop_;
  std::mutex should_stop_tex_;
  /// Terminate then blocks on this waiting for all the pending queries to
  /// complete.
  SimpleCondition<bool> script_complete_;
};

/// For use with ScriptsFromFile. This expects the configuration line to contain
/// a path to a file containing queries to run, an integer indicating the number
/// of time each query should be run, a string identifying a delay generator from
/// the set (NO_DELAY, EXPONENTIAL_DELAY). The rest of the line is specific to
/// the delay generator. In the case of NO_DELAY there is no parameter, and in
/// the case of EXPONENTIAL_DELAY the paramter is a single integer, the average
/// dealy in microseconds.
class VariableDelayScriptConstructor {
 public:
  VariableDelayScriptConstructor(QueryCommand* query_command);

  TestScript* operator()(
      const std::string& config_line, const std::string& dir_path,
      GeneralLogger* logger);

 private:
  QueryCommand* query_command_;
};

#endif
