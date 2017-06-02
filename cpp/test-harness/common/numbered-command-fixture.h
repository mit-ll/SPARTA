//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A unit test fixture for testing numbered commands. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_FIXTURE_H_
#define CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_FIXTURE_H_

#include "numbered-command-counter.h"
#include "numbered-command-sender.h"
#include "ready-monitor-fixture.h"

/// Adds a NumberedCommandSender to the stack defined by ReadyMonitorFixture.
/// See the comments on that class.
class NumberedCommandFixture : public ReadyMonitorFixture {
 public:
  NumberedCommandFixture() {
    nc_extension = new NumberedCommandSender(ready_monitor);
    manager->AddHandler("RESULTS", nc_extension);

    NumberedCommandCounter::Reset();
  }

  virtual ~NumberedCommandFixture() {}

  NumberedCommandSender* nc_extension;
};

#endif
