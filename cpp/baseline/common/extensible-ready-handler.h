//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Accepts input, recognizes the "subprotocol" and hands off
//                     stream to a handler specific to that protocol. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 08 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_EXTENSIBLE_READY_HANDLER_H_
#define CPP_COMMON_EXTENSIBLE_READY_HANDLER_H_

#include <iostream>
#include <map>
#include <string>

#include "common/event-loop.h"
#include "common/protocol-extension-manager.h"

/// The main extensible handler. To use, construct the handler, call AddHandler
/// as appropriate to set up handlers for various commands and then call Start().
/// Once start is called this will send the READY token and then wait for
/// commands. ExtensibleReadyHandler expects to receive a single line that
/// triggers an extension (as per AddHandler calls). Once the trigger is received
/// all input is directed to the extension until the extension calls Done at
/// which point the ExtensibleReadyHandler again looks for a line containing a
/// trigger for a handler.
class ExtensibleReadyHandler : public ProtocolExtensionManager {
 public:
  /// Construct a handler that reads from input_stream and writes the READY token
  /// to output_queue. This does not take ownership of output_queue.
  ExtensibleReadyHandler(WriteQueue* output_queue);
  virtual ~ExtensibleReadyHandler();

  virtual void Done();

 private:
  /// The output queue provided to the constructor.
  WriteQueue* output_queue_;
  /// We keep having to write READY via a Knot so we construct one once here.
  /// Then copy construct it when we need to write something. That's faster, and
  /// less code, then constructing a new knot each time.
  Knot ready_knot_;
};

#endif
