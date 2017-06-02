//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Waits for all client SUTs to receive their final
//                     publications.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Jan 2013   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_MULTI_WAIT_FOR_FINAL_PUBLICATIONS_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_MULTI_WAIT_FOR_FINAL_PUBLICATIONS_SCRIPT_H_

#include <string>

#include "wait-for-final-publication-script.h"
#include "test-harness/common/test-script.h"

class MultiClientSUTProtocolStack;
class SUTRunningMonitor;
class GeneralLogger;
class EventLoop;

/// TODO(njhwang) create unit tests
class MultiWaitForFinalPublicationScript : public TestScript {
 public:
  MultiWaitForFinalPublicationScript(int timeout,
                      MultiClientSUTProtocolStack* sut_protocols,
                      GeneralLogger* logger);
  virtual ~MultiWaitForFinalPublicationScript() {}

  virtual void Run();

 protected:
  int timeout_;
  MultiClientSUTProtocolStack* sut_protocols_;
  GeneralLogger* logger_;
};

class MultiWaitForFinalPublicationScriptFactory {
 public:
  MultiWaitForFinalPublicationScriptFactory(
      MultiClientSUTProtocolStack* sut_protocols, GeneralLogger* logger)
      : sut_protocols_(sut_protocols), logger_(logger) {}

  TestScript* operator()(const LineRawData<Knot>& command_data) {
    CHECK(command_data.Size() == 1);
    return new MultiWaitForFinalPublicationScript(
          SafeAtoi(command_data.Get(0).ToString()),
          sut_protocols_, logger_);
  }

 private:
  MultiClientSUTProtocolStack* sut_protocols_;
  GeneralLogger* logger_;
};

#endif
