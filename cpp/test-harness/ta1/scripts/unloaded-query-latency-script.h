//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A script for measuring query latency with an unloaded
//                     netowrk. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_UNLOADED_QUERY_LATENCY_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_UNLOADED_QUERY_LATENCY_SCRIPT_H_

#include <vector>

#include "query-list-script.h"

class QueryCommand;
class GeneralLogger;
class DelayFunction;

/// Given a list of queries, issue each query, wait for the query and wait for
/// the query to complete before issuing the next query.
class UnloadedQueryLatencyScript : public QueryListScript {
 public:
  /// See QueryListScript constructor.
  UnloadedQueryLatencyScript(
      std::istream* query_list_file, int num_iterations,
      DelayFunction delay_function, 
      QueryCommand* query_command, GeneralLogger* logger);

  virtual ~UnloadedQueryLatencyScript() {}

  virtual void Run();
};

/// For use with ScriptsFromFile class. This expect the configuration line to
/// contain a path to a file containing queries to run and an integer indicating
/// the number of times each script should be run.
class UnloadedQLSConstructor {
 public:
  UnloadedQLSConstructor(QueryCommand* query_command);

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path, GeneralLogger* logger);

 private:
  QueryCommand* query_command_;
};

#endif
