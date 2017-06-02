//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation for OutputHandler and
//                     OutputHandlerRegistry 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 16 May 2012   omd            Original Version
//*****************************************************************

#include "output-handler.h"
#include "statics.h"

#include <utility>

using std::ostream;
using std::map;

OutputHandlerRegistry::~OutputHandlerRegistry() {
  map<ostream*, OutputHandler*>::iterator i;
  for (i = handler_map_.begin(); i != handler_map_.end(); ++i) {
    delete i->second;
  }
}

OutputHandler* OutputHandlerRegistry::GetHandler(ostream* stream) {
  boost::lock_guard<boost::mutex> l(handler_map_tex_);

  map<ostream*, OutputHandler*>::iterator i = handler_map_.find(stream);
  if (i == handler_map_.end()) {
    OutputHandler* new_handler = new OutputHandler(stream);
    handler_map_.insert(std::make_pair(stream, new_handler));
    return new_handler;
  } else {
    return i->second;
  }
}

OutputHandler* OutputHandler::GetHandler(ostream* stream) {
  return handler_registry_.get()->GetHandler(stream);
}

std::auto_ptr<OutputHandlerRegistry> OutputHandler::handler_registry_;

void InitializeHandlerRegistry() {
  OutputHandler::handler_registry_.reset(new OutputHandlerRegistry);
}
ADD_INITIALIZER("OutputHandler", &InitializeHandlerRegistry);
