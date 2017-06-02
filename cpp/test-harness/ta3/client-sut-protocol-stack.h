//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Class that manages the stack of protocol parsers needed
//                     to control a client SUT from the test harness.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   njh            Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_CLIENT_SUT_PROTOCOL_STACK_H_
#define CPP_TEST_HARNESS_TA3_CLIENT_SUT_PROTOCOL_STACK_H_

#include <memory>

#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/sut-protocol-stack.h"
#include "test-harness/ta3/commands/unsubscribe-command.h"
#include "test-harness/ta3/commands/subscribe-command.h"

class DisconnectionReceivedHandler;
class PublicationReceivedHandler;
class SlaveHarnessNetworkStack;
class RootModeCommandSender;
class NumberedCommandSender;
class GeneralLogger;

class ClientSUTProtocolStack : public SUTProtocolStack {
 public:
  ClientSUTProtocolStack(size_t sut_id, 
                         SlaveHarnessNetworkStack* network_stack,
                         GeneralLogger* logger) : 
    sut_id_(sut_id), network_stack_(network_stack), logger_(logger) {}

  virtual ~ClientSUTProtocolStack() {}
  
  RootModeCommandSender* GetRootModeCommandSender() {
    return root_mode_command_sender_;
  }

  NumberedCommandSender* GetNumberedCommandSender() {
    return nc_sender_;
  }

  SubscribeCommand* GetSubscribeCommand() {
    return subscribe_command_.get();
  }

  UnsubscribeCommand* GetUnsubscribeCommand() {
    return unsubscribe_command_.get();
  }

  PublicationReceivedHandler* GetPublicationReceivedHandler() {
    return pub_recv_handler_;
  }

 protected:
  /// Adds test harness commands to the protocol stack.
  virtual void SetupCommands();

 private:
  size_t sut_id_;
  SlaveHarnessNetworkStack* network_stack_;
  std::unique_ptr<UnsubscribeCommand> unsubscribe_command_;
  std::unique_ptr<SubscribeCommand> subscribe_command_;
  GeneralLogger* logger_;
  /// These are owned by this stack's protocol manager, so no need to free them.
  RootModeCommandSender* root_mode_command_sender_;
  NumberedCommandSender* nc_sender_;
  DisconnectionReceivedHandler* disconn_recv_handler_;
  PublicationReceivedHandler* pub_recv_handler_;
};

#endif
