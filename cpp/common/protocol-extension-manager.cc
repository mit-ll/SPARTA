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

#include "protocol-extension-manager.h"

#include "check.h"

using std::map;
using std::string;

void ProtocolExtension::Done() {
  master_->Done();
}

ProtocolExtensionManager::~ProtocolExtensionManager() {
  map<string, ProtocolExtension*>::iterator i;
  for (i = handler_map_.begin(); i != handler_map_.end(); ++i) {
    delete i->second;
  }
}

void ProtocolExtensionManager::LineReceived(Knot data) {
  if (current_handler_ == NULL) {
    Knot::iterator token_end = data.Find(' ');
    map<string, ProtocolExtension*>::iterator handler_it;
    if (token_end == data.end()) {
      // No space in string so search for the entire line
      handler_it = handler_map_.find(data.ToString());
    } else {
      Knot token = data.SubKnot(data.begin(), token_end);
      handler_it = handler_map_.find(token.ToString());
    }
    CHECK(handler_it != handler_map_.end())
        << "The following unexpected line was received:\n"
        << data << "\nThis line was not associated with any protocol "
        << "and it does not begin a new one.";
    current_handler_ = handler_it->second;
    current_handler_->OnProtocolStart(data);
  } else {
    current_handler_->LineReceived(data);
  }
}

void ProtocolExtensionManager::RawReceived(Knot data) {
  // We should never receive raw data. Protocol extensions should always be
  // active when raw data is received.
  CHECK(current_handler_ != NULL);
  current_handler_->RawReceived(data);
}

void ProtocolExtensionManager::AddHandler(const string& trigger_token,
                                        ProtocolExtension* extension) {
  CHECK(handler_map_.find(trigger_token) == handler_map_.end());
  extension->SetMaster(this);
  handler_map_[trigger_token] = extension;
}

void ProtocolExtensionManager::Done() {
  current_handler_ = NULL;
}
