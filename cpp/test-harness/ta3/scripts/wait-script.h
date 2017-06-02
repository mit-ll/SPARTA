//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Script that waits for a given number of seconds
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_SCRIPTS_WAIT_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_SCRIPTS_WAIT_SCRIPT_H_

#include "test-harness/common/test-script.h"

#include "test-harness/ta3/master-harness-network-listener.h"
#include "common/check.h"

class GeneralLogger;

/// TODO(njhwang) create unit tests
class WaitScript : public TestScript {
 public:
  WaitScript(int num_secs, GeneralLogger* logger) : 
    num_secs_(num_secs), logger_(logger) {};

  virtual ~WaitScript() {};

  virtual void Run();

 private:
  int num_secs_;
  GeneralLogger* logger_;
};

class WaitScriptFactory {
 public:
  WaitScriptFactory() {};
  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path, GeneralLogger* logger);
};

#endif
