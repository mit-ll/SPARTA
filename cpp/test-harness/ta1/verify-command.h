//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A numbered command that sends the VERIFY command to a
//                     server. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_VERIFY_COMMAND_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_VERIFY_COMMAND_H_

#include "test-harness/common/generic-numbered-command.h"

// TODO(njhwang) build unit tests for this
class VerifyCommand : public GenericNumberedCommand {
 public:
  VerifyCommand(NumberedCommandSender* nc, EventMessageMonitor* em = nullptr)
      : GenericNumberedCommand("VERIFY", nc, em) {}

 protected:
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output);
};


#endif
