//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of ServerSUTProtocolStack. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

#include "server-sut-protocol-stack.h"

#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/event-message-monitor.h"

void ServerSUTProtocolStack::SetupCommands() {
  DCHECK(GetReadyMonitor() != nullptr);
  eventmsg_monitor_ = new EventMessageMonitor();
  nc_sender_ = new NumberedCommandSender(GetReadyMonitor(), eventmsg_monitor_);
  GetProtocolManager()->AddHandler("RESULTS", nc_sender_);
  GetProtocolManager()->AddHandler("EVENTMSG", eventmsg_monitor_);

  insert_command_.reset(new InsertCommand(nc_sender_, eventmsg_monitor_));
  update_command_.reset(new UpdateCommand(nc_sender_, eventmsg_monitor_));
  delete_command_.reset(new DeleteCommand(nc_sender_, eventmsg_monitor_));
  verify_command_.reset(new VerifyCommand(nc_sender_, eventmsg_monitor_));
  root_mode_command_sender_ = new RootModeCommandSender(GetReadyMonitor());
  GetProtocolManager()->AddHandler("DONE", root_mode_command_sender_);
}
