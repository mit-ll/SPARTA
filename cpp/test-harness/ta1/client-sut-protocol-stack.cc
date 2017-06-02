//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ClientSUTProtocolStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

#include "client-sut-protocol-stack.h"

#include "test-harness/common/agg-numbered-command-sender.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/event-message-monitor.h"

using std::string;

void ClientSUTProtocolStack::SetupCommands() {
  DCHECK(GetReadyMonitor() != nullptr);
  eventmsg_monitor_ = new EventMessageMonitor();
  nc_sender_ = new AggNumberedCommandSender(GetReadyMonitor(), 
                                            eventmsg_monitor_);
  GetProtocolManager()->AddHandler("RESULTS", nc_sender_);
  GetProtocolManager()->AddHandler("EVENTMSG", eventmsg_monitor_);

  query_command_.reset(new QueryCommand(nc_sender_, eventmsg_monitor_));
  root_mode_command_sender_ = new RootModeCommandSender(GetReadyMonitor());
  GetProtocolManager()->AddHandler("DONE", root_mode_command_sender_);
}
