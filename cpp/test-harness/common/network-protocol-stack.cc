//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NetworkProtocolStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Sep 2012   omd            Original Version
//*****************************************************************

#include "network-protocol-stack.h"

#include <boost/bind.hpp>

#include "test-harness/common/multi-numbered-command-sender.h"
#include "common/network-connection.h"
#include "common/protocol-extension-manager.h"
#include "test-harness/common/ready-monitor.h"
#include "common/line-raw-parser.h"

NetworkProtocolStack::NetworkProtocolStack(NetworkConnection* connection)
    : connection_(connection), extension_manager_(new ProtocolExtensionManager),
      ready_monitor_(new ReadyMonitor(connection->GetWriteQueue())),
      nc_sender_(new MultiNumberedCommandSender(ready_monitor_)),
      lr_parser_(new LineRawParser(extension_manager_)) {
  extension_manager_->AddHandler("READY", ready_monitor_);
  extension_manager_->AddHandler("RESULTS", nc_sender_);

  connection->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, lr_parser_.get(), _1));
}
