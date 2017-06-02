//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Class that manages the stack of protocol parsers needed
//                     to control the TA1 server SUT from the test harness. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_SERVER_SUT_PROTOCOL_STACK_H_
#define CPP_TEST_HARNESS_TA3_SERVER_SUT_PROTOCOL_STACK_H_

#include <memory>

#include "test-harness/common/sut-protocol-stack.h"
#include "test-harness/ta3/commands/publish-command.h"

class RootModeCommandSender;
class NumberedCommandSender;

class ServerSUTProtocolStack : public SUTProtocolStack {
 public:
  ServerSUTProtocolStack() {}
  virtual ~ServerSUTProtocolStack() {}

  NumberedCommandSender* GetNumberedCommandSender() {
    return nc_sender_;
  }

  RootModeCommandSender* GetRootModeCommandSender() {
    return root_mode_command_sender_;
  }

  PublishCommand* GetPublishCommand() {
    return publish_command_.get();
  }

 protected:
  /// Adds test harness commands to the protocol stack.
  virtual void SetupCommands();

 private:
    /// This is owned by this stack's protocol manager, so no need to free it.
  RootModeCommandSender* root_mode_command_sender_;
  NumberedCommandSender* nc_sender_;
  std::unique_ptr<PublishCommand> publish_command_;
};

#endif
