//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A unit test fixture for testing
//                     MultiNumberedCommandSender. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_MULTI_NUMBERED_COMMAND_FIXTURE_H_
#define CPP_TEST_HARNESS_COMMON_MULTI_NUMBERED_COMMAND_FIXTURE_H_

#include "ready-monitor-fixture.h"

/// Adds a MultiNumberedCommandSender to the stack defined by
/// ReadyMonitorFixture.  See the comments on that class.
class MultiNumberedCommandFixture : public ReadyMonitorFixture {
 public:
  MultiNumberedCommandFixture();
  virtual ~MultiNumberedCommandFixture() {}

  MultiNumberedCommandSender* nc_extension;
};

inline MultiNumberedCommandFixture::MultiNumberedCommandFixture() {
  nc_extension = new MultiNumberedCommandSender(ready_monitor);
  manager->AddHandler("RESULTS", nc_extension);
}

#endif
