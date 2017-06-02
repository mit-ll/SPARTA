//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ExtensibleReadyHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 08 May 2012   omd            Original Version
//*****************************************************************

#include "extensible-ready-handler.h"

#include <cstring>

#include "common/check.h"

using std::map;
using std::string;

const char kReadyToken[] = "READY\n";
const int kReadyTokenLen = strlen(kReadyToken);

ExtensibleReadyHandler::ExtensibleReadyHandler(WriteQueue* output_queue)
    : output_queue_(output_queue) {
  ready_knot_.AppendOwned(kReadyToken, kReadyTokenLen);

  // TODO(odain) Is this always guaranteed to work? What if the event loop
  // hasn't been started yet??
  CHECK(output_queue_->Write(new Knot(ready_knot_)));
}

ExtensibleReadyHandler::~ExtensibleReadyHandler() {
}

void ExtensibleReadyHandler::Done() {
  Knot* this_ready_knot = new Knot(ready_knot_);
  if (!output_queue_->Write(this_ready_knot)) {
     LOG(DEBUG) << "Output queue full. Calling WriteWithBlock.";
     output_queue_->WriteWithBlock(this_ready_knot);
  }
  ProtocolExtensionManager::Done();
}
