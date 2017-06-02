//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Accepts input, recognizes the "subprotocol" and
//                     hands off stream to a handler specific to
//                     that protocol. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 08 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_PROTOCOL_EXTENSION_MANAGER_H_
#define CPP_COMMON_PROTOCOL_EXTENSION_MANAGER_H_

#include <iostream>
#include <map>
#include <string>

#include "line-raw-parser.h"
#include "types.h"

class ProtocolExtensionManager;

/// An ProtocolExtensionManager manages a set of ProtocolExtension subclasses.
/// Each subclass handles a specific type of protocol. A protocol extension is
/// triggered by a line that starts with a particular value (the value of the
/// line is provided in ProtocolExtensionManager::AddHandler). Once triggered
/// all input is sent to the extension until the extension calls Done. 
class ProtocolExtension {
 public:
  virtual ~ProtocolExtension() {}
  /// This is called by ProtocolExtensionManager::AddHandler so that the Done
  /// method knows what object to inform.
  void SetMaster(ProtocolExtensionManager* master) {
    master_ = master;
  }

  /// One of the virtual methods below must call this to exit the protocol
  /// extension. Until this is called all received input is directed to the
  /// extension.
  void Done();

  /// Extensions that want to implement some functionality immediately when
  /// their mode becomes active should implement this. start_line is the full
  /// line that triggered the extension.
  virtual void OnProtocolStart(Knot start_line) {}
  /// Extensions that need to read more input should override these methods.
  virtual void LineReceived(Knot data) {}
  virtual void RawReceived(Knot data) {}
 private:
  ProtocolExtensionManager* master_;
};

/// The ProtocolExtensionManager class. To use, construct the manager, call
/// AddHandler as appropriate to set up handlers for various commands and then
/// connect this to a LineRawParser instance so it starts receiving data.
/// ProtocolExtensionManager expects to receive a single line that triggers an
/// extension (as per AddHandler calls). Once the trigger is received all input
/// is directed to the extension until the extension calls Done at which point
/// the ProtocolExtensionManager again looks for a line containing a trigger for
/// a handler.
class ProtocolExtensionManager : public LineRawParseHandler {
 public:
  ProtocolExtensionManager() : current_handler_(NULL) {}
  virtual ~ProtocolExtensionManager();

  /// When a line that starts with the trigger_token followed by a space is
  /// received all input will be directed to extension. Specifically, when the
  /// line is received then extension's OnProtocolStart method will be called
  /// with the line that triggered the extension. Then any lines received and
  /// any raw data received will be directed to the extension by calling
  /// LineReceived or RawReceived as appropriate. This continues until the
  /// extension calls Done().  This class takes ownership of the extension and
  /// will free it in the destructor.
  void AddHandler(const std::string& tigger_token,
                  ProtocolExtension* extension);
  virtual void Done();

  /// Overriding methods from LineRawParseHandler
  virtual void LineReceived(Knot data);
  virtual void RawReceived(Knot data);

 private:
  /// Points to the current protocol handler. This is NULL if there is no
  /// current handler. If NULL we expect the next item received to be line mode
  /// and the line should == one of the trigger tokens for an extension.
  ProtocolExtension* current_handler_;
  /// A map from token to the ProtocolExtension that should be triggered.
  std::map<std::string, ProtocolExtension*> handler_map_;
};

#endif
