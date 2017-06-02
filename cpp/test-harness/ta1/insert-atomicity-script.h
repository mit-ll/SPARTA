//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A test script to check insert atomicity. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_INSERT_ATOMICITY_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_INSERT_ATOMICITY_SCRIPT_H_

#include "test-harness/common/test-script.h"
#include "common/knot.h"

#include <string>

class GeneralLogger;
class QueryCommand;
class THRunScriptCommand;

/// This script asks the harness driving the server to insert some data. Then it
/// queries for that same data as fast as possible. 
class InsertAtomicityScript : public TestScript {
 public:
  /// TODO(odain) update this so it takes a file containing queries and insert
  /// data.
  InsertAtomicityScript(const Knot& query,
                        LineRawData<Knot>* insert_data,
                        QueryCommand* query_command,
                        THRunScriptCommand* run_script_command,
                        GeneralLogger* logger);

  virtual void Run();

 private:
  void LogStarted();

  Knot query_;
  std::auto_ptr<LineRawData<Knot> > insert_data_;
  QueryCommand* query_command_;
  THRunScriptCommand* run_script_command_;
  GeneralLogger* logger_;
};


#endif
