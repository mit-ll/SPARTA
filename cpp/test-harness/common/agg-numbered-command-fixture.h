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

#ifndef CPP_TEST_HARNESS_COMMON_AGG_NUMBERED_COMMAND_FIXTURE_H_
#define CPP_TEST_HARNESS_COMMON_AGG_NUMBERED_COMMAND_FIXTURE_H_

#include "agg-numbered-command-sender.h"
#include "numbered-command-counter.h"
#include "ready-monitor-fixture.h"

/// Adds a NumberedCommandSender to the stack defined by ReadyMonitorFixture.
/// See the comments on that class.
class AggNumberedCommandFixture : public ReadyMonitorFixture {
 public:
  AggNumberedCommandFixture() {
    /// The manager takes ownership of nc_sender so we don't free it.
    nc_sender = new AggNumberedCommandSender(ready_monitor);
    manager->AddHandler("RESULTS", nc_sender);

    NumberedCommandCounter::Reset();
  }

  virtual ~AggNumberedCommandFixture() {}

  AggNumberedCommandSender* nc_sender;
};

#endif
