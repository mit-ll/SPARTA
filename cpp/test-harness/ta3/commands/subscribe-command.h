//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Command from harness to SUT asking the SUT 
//                     to subscribe with a particular filter. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_SUBSCRIBE_COMMAND_H_
#define CPP_TEST_HARNESS_TA3_SUBSCRIBE_COMMAND_H_

#include "test-harness/common/generic-numbered-command.h"

class SubscribeCommand : public GenericNumberedCommand {
 public:
  SubscribeCommand(NumberedCommandSender* nc)
      : GenericNumberedCommand("SUBSCRIBE", nc) {}

 private:
  /// Given data, this wraps it in a SUBSCRIBE command. data is assumed to be
  /// such that data.Get(0) returns the subscriber ID to use, and data.Get(1)
  /// returns the subscription filter to use.
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output);
};

#endif
