//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD, ni24039
// Description:        Implementaton of SlaveHarnessNetworkStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#include <boost/bind.hpp>

#include "slave-harness-network-stack.h"

#include "harness-info-request-handler.h"
#include "baseline/common/numbered-command-receiver.h"
#include "baseline/common/extensible-ready-handler.h"
#include "test-harness/common/th-run-script-handler.h"
#include "test-harness/common/script-manager.h"
#include "common/string-algo.h"

using namespace std;

SlaveHarnessNetworkStack::SlaveHarnessNetworkStack(
    string harness_id, size_t num_suts,
    std::shared_ptr<NetworkConnection> connection,
    ScriptManager* script_manager)
    : harness_id_(harness_id), num_suts_(num_suts), connection_(connection) {

  DCHECK(connection_ != nullptr); 

  ExtensibleReadyHandler* ready_handler =
      new ExtensibleReadyHandler(connection_->GetWriteQueue());
  nc_receiver_ =
      new NumberedCommandReceiver(connection_->GetWriteQueue());

  nc_receiver_->AddHandler("HARNESS_INFO", 
                          boost::bind(HarnessInfoRequestHandlerFactory,
                                      &harness_id_, &num_suts_));
  nc_receiver_->AddHandler("RUNSCRIPT",
                          boost::bind(ConstructTHRunScriptHandler,
                                      script_manager));

  ready_handler->AddHandler("COMMAND", nc_receiver_);

  lr_parser_.reset(new LineRawParser(ready_handler));
}

void SlaveHarnessNetworkStack::Start() {
  // Note that if this gets called more than once, 
  // NetworkConnection::RegisterDataCallback should eventually fail a DCHECK 
  // since more than one callback would be registered to a single file 
  // descriptor.
  DCHECK(connection_ != nullptr); 
  DCHECK(lr_parser_ != nullptr); 
  connection_->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, lr_parser_.get(), _1));
}

void SlaveHarnessNetworkStack::SUTDisconnected(size_t sut_id) {
  // TODO(njhwang) propagate DISCONNECTION message with harness/SUT ID
  // information to master harness so test can automatically abort?
  LOG(WARNING) << "DISCONNECTION received for harness " << harness_id_
            << " and SUT " << sut_id;
}

void SlaveHarnessNetworkStack::Shutdown() {
  connection_->Shutdown();
}
