//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A script for testing that DB modifications are atomic. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 27 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_MODIFY_AND_QUERY_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_MODIFY_AND_QUERY_SCRIPT_H_

#include <functional>
#include <memory>
#include <vector>

#include "test-harness/common/test-script.h"
#include "variable-delay-query-script.h"
#include "common/line-raw-data.h"
#include "common/knot.h"

class THRunScriptCommand;
class GeneralLogger;
class QueryCommand;

/// This is a versatile script that can instruct the test harness controlling the
/// server to issue any number of database modifications with variable delays
/// while this component runs two theads, one of which generates background
/// traffic with configurable delays and the other thread repeatedly issues
/// queries the correspond to the modifications in an attempt to catch atomicity
/// errors.
class ModifyAndQueryScript : public TestScript {
 public:
  typedef std::function<int ()> DelayFunction;

  /// query_modify_pairs is a file indicating modifications to be performed and
  /// queries to be run at the same time as those modifications in order to catch
  /// atomicity errors. The file is formatted with alternating lines: the first
  /// line indicates the query to perform and the 2nd line is the name of a file,
  /// relative to dir_path, that contains LineRaw formatted data suitable for
  /// VariableDelayModifyArgumentScript (including the delay generator, etc.
  /// 
  /// background_queries is a file containing a set of queries to be sent to the
  /// client in order to provide background traffic. The queries will be sent
  /// using VariableDelayQueryScript using delay_function as the delay.
  ModifyAndQueryScript(
      std::istream* query_modify_pairs, const std::string& dir_path,
      std::istream* background_queries,
      DelayFunction delay_function, THRunScriptCommand* run_script_command,
      QueryCommand* query_command, GeneralLogger* logger);

  virtual ~ModifyAndQueryScript();

  virtual void Run();

 private:
  void ParseQueryModifyPairs(std::istream* input_file,
                             const std::string& dir_path);

  void LogModificationCommandStatus(
      size_t global_id, const char* state);

  THRunScriptCommand* run_script_command_;
  QueryCommand* query_command_;
  GeneralLogger* logger_;

  std::auto_ptr<VariableDelayQueryScript> background_runner_;
  std::vector<Knot> queries_;
  std::vector<uint64_t> query_ids_;
  std::vector<LineRawData<Knot>*> modifications_;
};

/// A factory for use with ScriptsFromFile. Expects a line containing, in order,
/// the query_modify_pairs file, the background_queries file, and the delay
/// paramters (as per VariableDelayQueryScript).
class ModifyAndQueryScriptConstructor {
 public:
  ModifyAndQueryScriptConstructor(
      THRunScriptCommand* run_script_command, QueryCommand* query_command);

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path,
                         GeneralLogger* logger);

 private:
  THRunScriptCommand* run_script_command_;
  QueryCommand* query_command_;
};

#endif
