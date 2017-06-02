//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of ClientSUTProtocolStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   njh            Tailored for TA3
//*****************************************************************

#include "slave-harness-network-stack.h"
#include "client-sut-protocol-stack.h"
#include "test-harness/ta3/disconnection-received-handler.h"
#include "test-harness/ta3/publication-received-handler.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/ready-monitor.h"
#include "common/general-logger.h"

void ClientSUTProtocolStack::SetupCommands() {
  DCHECK(GetReadyMonitor() != nullptr);
  nc_sender_ = new NumberedCommandSender(GetReadyMonitor());
  GetProtocolManager()->AddHandler("RESULTS", nc_sender_);

  // Set up numbered command handling.
  DCHECK(GetNumberedCommandSender() != nullptr);
  unsubscribe_command_.reset(new UnsubscribeCommand(GetNumberedCommandSender()));
  subscribe_command_.reset(new SubscribeCommand(GetNumberedCommandSender()));

  // Set up root mode command handling.
  root_mode_command_sender_ = new RootModeCommandSender(GetReadyMonitor());
  GetProtocolManager()->AddHandler("DONE", root_mode_command_sender_);

  // Set up other token handling.
  pub_recv_handler_ = new PublicationReceivedHandler(sut_id_, logger_);
  GetProtocolManager()->AddHandler("PUBLICATION", pub_recv_handler_);
  disconn_recv_handler_ = 
    new DisconnectionReceivedHandler(sut_id_, network_stack_, logger_);
  GetProtocolManager()->AddHandler("DISCONNECTION", disconn_recv_handler_);
}

