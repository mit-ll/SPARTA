//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Command from harness to SUT asking the SUT 
//                     to unsubscribe a particular subscription. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_UNSUBSCRIBE_COMMAND_H_
#define CPP_TEST_HARNESS_TA3_UNSUBSCRIBE_COMMAND_H_

#include "test-harness/common/generic-numbered-command.h"

class UnsubscribeCommand : public GenericNumberedCommand {
 public:
  UnsubscribeCommand(NumberedCommandSender* nc)
      : GenericNumberedCommand("UNSUBSCRIBE", nc) {}

 private:
  /// Given data, this wraps it in an UNSUBSCRIBE command. data is assumed to be
  /// such that data.Get(0) returns the subscriber ID to use.
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output);
};

#endif
