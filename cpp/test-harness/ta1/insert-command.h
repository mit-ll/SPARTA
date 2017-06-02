//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Command from harness to SUT asking the SUT 
//                     to insert data. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 12 Sep 2012   omd            Original Version
// 19 Sep 2012   ni24039        Refactored to use GenericCommand
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA1_INSERT_COMMAND_H_
#define CPP_TEST_HARNESS_TA1_INSERT_COMMAND_H_

#include "test-harness/common/generic-numbered-command.h"

class InsertCommand : public GenericNumberedCommand {
 public:
  InsertCommand(NumberedCommandSender* nc, EventMessageMonitor* em = nullptr)
      : GenericNumberedCommand("INSERT", nc, em) {}

 private:
  /// Given data, this wraps it in an INSERT/ENDINSERT pair. data is assumed to
  /// be such that data.Get(0) returns the data to be inserted into the 1st
  /// column of the DB, data.Get(1) contains the data for the 2nd column, etc.
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output);
};

#endif
