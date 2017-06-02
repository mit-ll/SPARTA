//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Script that identifies and profiles client harnesses
//                     connected to a server harness.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_SCRIPTS_UPDATE_NETWORK_MAP_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_SCRIPTS_UPDATE_NETWORK_MAP_SCRIPT_H_

#include "test-harness/common/test-script.h"

#include "test-harness/ta3/master-harness-network-listener.h"
#include "common/check.h"

class GeneralLogger;

/// TODO(njhwang) create unit tests
class UpdateNetworkMapScript : public TestScript {
 public:
  UpdateNetworkMapScript(
      size_t num_harnesses, size_t num_suts,
      MasterHarnessNetworkListener* listener, 
      GeneralLogger* logger);

  virtual ~UpdateNetworkMapScript() {};

  virtual void Run();

 private:
  size_t num_harnesses_;
  size_t num_suts_;
  MasterHarnessNetworkListener* listener_;
  GeneralLogger* logger_;
};

class UpdateNetworkMapScriptFactory {
 public:
  UpdateNetworkMapScriptFactory(
      MasterHarnessNetworkListener* listener);

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path, GeneralLogger* logger);

 private:
  MasterHarnessNetworkListener* listener_;
};

#endif
