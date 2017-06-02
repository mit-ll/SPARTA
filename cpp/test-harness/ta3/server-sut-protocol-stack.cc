//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implmentation of ServerSUTProtocolStack. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#include "server-sut-protocol-stack.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/ready-monitor.h"

void ServerSUTProtocolStack::SetupCommands() {
  DCHECK(GetReadyMonitor() != nullptr);
  nc_sender_ = new NumberedCommandSender(GetReadyMonitor());
  GetProtocolManager()->AddHandler("RESULTS", nc_sender_);
  
  // Set up numbered command handling.
  DCHECK(GetNumberedCommandSender() != nullptr);
  publish_command_.reset(new PublishCommand(GetNumberedCommandSender()));

  // Set up root mode command handling.
  root_mode_command_sender_ = new RootModeCommandSender(GetReadyMonitor());
  GetProtocolManager()->AddHandler("DONE", root_mode_command_sender_);
}
