//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Script for sending root mode commands to both client and
//                     server. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_ROOT_MODE_MASTER_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_ROOT_MODE_MASTER_SCRIPT_H_

#include <string>

#include "test-harness/common/root-mode-local-script.h"

class GeneralLogger;
class MasterHarnessNetworkListener;
class RootModeCommandSender;
class SUTRunningMonitor;

/// Oddly, the master script inherits from the local script. That's because the
/// local script just sends the command to it's SUT. The master needs to do that
/// *and* send a request over the network to have the local run and send the
/// command to its SUT. Thus, the functionality of the master is a proper
/// superset of the functionality of the local and inheritance makes sense.
/// TODO(njhwang) create unit tests
class RootModeMasterScript : public RootModeLocalScript {
 public:
  RootModeMasterScript(const std::string& command_string,
                       RootModeCommandSender* command_sender,
                       SUTRunningMonitor* sut_running,
                       MasterHarnessNetworkListener* listener,
                       GeneralLogger* logger);

  virtual ~RootModeMasterScript() {}

  virtual void Run();

 private:
  MasterHarnessNetworkListener* listener_;
};

/// For use with the ScriptsFromFile class. This expects the configuration line
/// to contain just a single string, the root mode command to run.
class RootModeMasterScriptFactory {
 public:
  RootModeMasterScriptFactory(
      RootModeCommandSender* command_sender,
      SUTRunningMonitor* sut_monitor,
      MasterHarnessNetworkListener* listener)
      : command_sender_(command_sender),
        sut_monitor_(sut_monitor),
        listener_(listener) {}

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path, GeneralLogger* logger) {
    return new RootModeMasterScript(
        config_line, command_sender_, sut_monitor_, listener_, logger);
  }
 private:
  RootModeCommandSender* command_sender_;
  SUTRunningMonitor* sut_monitor_;
  MasterHarnessNetworkListener* listener_;
};

#endif
