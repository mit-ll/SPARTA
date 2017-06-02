//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Command from harness to SUT asking the SUT to delete
//                     data. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************

#ifndef CPP_TEST_HARNESS_TA1_DELETE_COMMAND_H_
#define CPP_TEST_HARNESS_TA1_DELETE_COMMAND_H_

#include "test-harness/common/generic-numbered-command.h"

class DeleteCommand : public GenericNumberedCommand {
 public:
  DeleteCommand(NumberedCommandSender* nc, EventMessageMonitor* em = nullptr)
      : GenericNumberedCommand("DELETE", nc, em) {}

 private:
  /// Given data, this wraps it in a DELETE command. data is assumed to be an
  /// integer representing the row to delete.
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output);
};

#endif
