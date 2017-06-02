//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Class that manages the stack of protocol parsers needed
//                     to control the TA1 server SUT from the test harness. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA1_SERVER_SUT_PROTOCOL_STACK_H_
#define CPP_TEST_HARNESS_TA1_SERVER_SUT_PROTOCOL_STACK_H_

#include "test-harness/common/sut-protocol-stack.h"

#include <memory>

#include "delete-command.h"
#include "insert-command.h"
#include "update-command.h"
#include "verify-command.h"

class RootModeCommandSender;
class NumberedCommandSender;
class EventMessageMonitor;

class ServerSUTProtocolStack : public SUTProtocolStack {
 public:
  ServerSUTProtocolStack() {}
  virtual ~ServerSUTProtocolStack() {}

  InsertCommand* GetInsertCommand() {
    return insert_command_.get();
  }

  UpdateCommand* GetUpdateCommand() {
    return update_command_.get();
  }

  DeleteCommand* GetDeleteCommand() {
    return delete_command_.get();
  }

  VerifyCommand* GetVerifyCommand() {
    return verify_command_.get();
  }

  RootModeCommandSender* GetRootModeCommandSender() {
    return root_mode_command_sender_;
  }

 protected:
  virtual void SetupCommands();

 private:
  /// This is owned by proto_manager. We don't need to free it.
  NumberedCommandSender* nc_sender_;
  std::auto_ptr<InsertCommand> insert_command_;
  std::auto_ptr<UpdateCommand> update_command_;
  std::auto_ptr<DeleteCommand> delete_command_;
  std::auto_ptr<VerifyCommand> verify_command_;
  EventMessageMonitor* eventmsg_monitor_;
  /// This is owned by the protocol manager so no need to free it.
  RootModeCommandSender* root_mode_command_sender_;
};

#endif
