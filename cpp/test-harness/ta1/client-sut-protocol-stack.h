//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Class that manages the stack of protocol parsers needed
//                     to control the client SUT from the test harness.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA1_CLIENT_SUT_PROTOCOL_STACK_H_
#define CPP_TEST_HARNESS_TA1_CLIENT_SUT_PROTOCOL_STACK_H_

#include "test-harness/common/sut-protocol-stack.h"

#include <memory>

#include "query-command.h"

class AggNumberedCommandSender;
class RootModeCommandSender;
class EventMessageMonitor;

class ClientSUTProtocolStack : public SUTProtocolStack {
 public:
  ClientSUTProtocolStack() {}
  virtual ~ClientSUTProtocolStack() {}
  
  QueryCommand* GetQueryCommand() {
    return query_command_.get();
  }

  RootModeCommandSender* GetRootModeCommandSender() {
    return root_mode_command_sender_;
  }

 protected:
  /// Adds test harness commands to the protocol stack.
  virtual void SetupCommands();

 private:
  /// These are owned by proto manager so no need to free them.
  AggNumberedCommandSender* nc_sender_;
  std::unique_ptr<QueryCommand> query_command_;
  EventMessageMonitor* eventmsg_monitor_;
  RootModeCommandSender* root_mode_command_sender_;
};

#endif
