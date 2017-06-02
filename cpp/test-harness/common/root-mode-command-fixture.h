//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        A unit test fixture for testing root mode commands. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_ROOT_MODE_COMMAND_FIXTURE_H_
#define CPP_TEST_HARNESS_COMMON_ROOT_MODE_COMMAND_FIXTURE_H_

#include "root-mode-command-sender.h"
#include "ready-monitor-fixture.h"

/// Adds a RootModeCommandSender to the stack defined by ReadyMonitorFixture.
/// See the comments on that class.
class RootModeCommandFixture : public ReadyMonitorFixture {
 public:
  RootModeCommandFixture();
  virtual ~RootModeCommandFixture() {}

  RootModeCommandSender* rm_extension;
};

inline RootModeCommandFixture::RootModeCommandFixture() {
  rm_extension = new RootModeCommandSender(ready_monitor);
  manager->AddHandler("DONE", rm_extension);
}


#endif
