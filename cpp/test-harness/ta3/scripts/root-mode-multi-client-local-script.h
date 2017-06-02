//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A script that recieves root mode commands from the
//                     master test harness network and sends them to all 
//                     clients. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_ROOT_MODE_MULTI_CLIENT_LOCAL_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_ROOT_MODE_MULTI_CLIENT_LOCAL_SCRIPT_H_

#include <string>

#include "test-harness/common/test-script.h"

class GeneralLogger;
class MultiClientSUTProtocolStack;
class SUTRunningMonitor;
class EventLoop;

/// TODO(njhwang) create unit tests
class RootModeMultiClientLocalScript : public TestScript {
 public:
  /// command_string is the full command, excluding the terminating '\n'
  /// character, that we are going to send to the SUT.
  RootModeMultiClientLocalScript(const std::string& command_string,
                      MultiClientSUTProtocolStack* sut_protocols,
                      GeneralLogger* logger, 
                      std::vector<SUTRunningMonitor*> sut_monitors);
  virtual ~RootModeMultiClientLocalScript() {}

  virtual void Run();

 protected:
  const std::string command_string_;
  MultiClientSUTProtocolStack* sut_protocols_;
  GeneralLogger* logger_;
  std::vector<SUTRunningMonitor*> sut_monitors_;
};

/// Functor to construct a RootModeLocalScript from the data received over the
/// network.
class RootModeMultiClientLocalScriptFactory {
 public:
  RootModeMultiClientLocalScriptFactory(
      MultiClientSUTProtocolStack* sut_protocols, GeneralLogger* logger,
      std::vector<SUTRunningMonitor*> sut_monitors)
      : sut_protocols_(sut_protocols), logger_(logger), 
        sut_monitors_(sut_monitors) {}

  TestScript* operator()(const LineRawData<Knot>& command_data) {
    CHECK(command_data.Size() == 1);
    return new RootModeMultiClientLocalScript(command_data.Get(0).ToString(),
                                   sut_protocols_, logger_, sut_monitors_);
  }

 private:
  MultiClientSUTProtocolStack* sut_protocols_;
  GeneralLogger* logger_;
  std::vector<SUTRunningMonitor*> sut_monitors_;
};

#endif
