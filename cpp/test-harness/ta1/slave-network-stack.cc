//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementaton of SlaveNetworkStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

#include "slave-network-stack.h"

#include <boost/bind.hpp>

#include "test-harness/common/script-manager.h"
#include "test-harness/common/th-run-script-handler.h"

SlaveNetworkStack::SlaveNetworkStack(
    std::shared_ptr<NetworkConnection> connection,
    ScriptManager* script_manager)
    : connection_(connection) {
  ExtensibleReadyHandler* ready_handler =
      new ExtensibleReadyHandler(connection_->GetWriteQueue());
  nc_receiver =
      new NumberedCommandReceiver(connection_->GetWriteQueue());

  nc_receiver->AddHandler("RUNSCRIPT",
                          boost::bind(ConstructTHRunScriptHandler,
                                      script_manager));
  ready_handler->AddHandler("COMMAND", nc_receiver);
  lr_parser_.reset(new LineRawParser(ready_handler));
  connection_->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, lr_parser_.get(), _1));
}
