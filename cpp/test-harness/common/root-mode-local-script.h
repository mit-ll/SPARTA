//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A script that recieves root mode commands from the
//                     network and sends them to the sever. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 06 Nov 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_ROOT_MODE_LOCAL_SCRIPT_H_
#define CPP_TEST_HARNESS_COMMON_ROOT_MODE_LOCAL_SCRIPT_H_

#include <string>

#include "test-script.h"

class GeneralLogger;
class THRunScriptCommand;
class RootModeCommandSender;
class SUTRunningMonitor;

/// Note that this does a proper subset of what RootModeMasterScript needs to do.
/// Thus it also serves as a base class for that.
class RootModeLocalScript : public TestScript {
 public:
  /// command_string is the full command, excluding the terminating '\n'
  /// character, that we are going to send to the SUT.
  RootModeLocalScript(const std::string& command_string,
                      RootModeCommandSender* command_sender,
                      SUTRunningMonitor* sut_running,
                      GeneralLogger* logger);
  virtual ~RootModeLocalScript() {}

  virtual void Run();

 protected:
  const std::string command_string_;
  RootModeCommandSender* command_sender_;
  SUTRunningMonitor* sut_running_monitor_;
  GeneralLogger* logger_;
};

/// Functor to construct a RootModeLocalScript from the data received over the
/// network.
class RootModeLocalScriptFactory {
 public:
  RootModeLocalScriptFactory(
      RootModeCommandSender* command_sender, SUTRunningMonitor* sut_monitor,
      GeneralLogger* logger)
      : command_sender_(command_sender), sut_monitor_(sut_monitor),
        logger_(logger) {}

  TestScript* operator()(const LineRawData<Knot>& command_data) {
    CHECK(command_data.Size() == 1);
    return new RootModeLocalScript(command_data.Get(0).ToString(),
                                   command_sender_, sut_monitor_, logger_);
  }

 private:
  RootModeCommandSender* command_sender_;
  SUTRunningMonitor* sut_monitor_;
  GeneralLogger* logger_;
};

/// Functor to construct a RootModeLocalScript from the data listed in a file.
class RootModeLocalScriptFromFileFactory {
 public:
  RootModeLocalScriptFromFileFactory(
      RootModeCommandSender* command_sender, SUTRunningMonitor* sut_monitor)
      : command_sender_(command_sender), sut_monitor_(sut_monitor) {}

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path,
                         GeneralLogger* logger) {
    return new RootModeLocalScript(config_line, command_sender_, sut_monitor_,
                                   logger);
  }

 private:
  RootModeCommandSender* command_sender_;
  SUTRunningMonitor* sut_monitor_;
};

#endif
