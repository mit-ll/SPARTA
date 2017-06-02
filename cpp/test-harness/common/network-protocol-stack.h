//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for managing the protocol stack of connected
//                     clients.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_NETWORK_PROTOCOL_STACK_H_
#define CPP_TEST_HARNESS_COMMON_NETWORK_PROTOCOL_STACK_H_

#include <memory>

#include "ready-monitor.h"

class ProtocolExtensionManager;
class ReadyMonitor;
class MultiNumberedCommandSender;
class NetworkConnection;
class LineRawParser;

/// A NetworkServer listens on a port and gets a callback when a client connects.
/// If that server is a test harness component it then needs to build a protocol
/// stack to be used for communicating with the other end of the network
/// connection. This class serves as a good base class for any network server
/// that needs to do this. Subclasses implement AddProtocols to layer additional
/// harness-type specific protocols on top of the basic set.
///
/// The general use case is that the callback that gets called when a new
/// connection is made constructs one of these and this then sets up the entire
/// protocol stack.
class NetworkProtocolStack {
 public:
  NetworkProtocolStack(NetworkConnection* connection);
  virtual ~NetworkProtocolStack() {}

  ReadyMonitor* GetReadyMonitor() {
    return ready_monitor_;
  }

 protected:
  ProtocolExtensionManager* GetExtensionManager() {
    return extension_manager_;
  }

  MultiNumberedCommandSender* GetNumberedCommandSender() {
    return nc_sender_;
  }

 private:
  /// This is owned by a NetworkServer - doesn't need to be freed.
  NetworkConnection* connection_;
  /// Will be owned by lr_parser_.
  ProtocolExtensionManager* extension_manager_;
  /// Will be owned by extension_manager_.
  ReadyMonitor* ready_monitor_;
  /// Will be owned by extension_manager_.
  MultiNumberedCommandSender* nc_sender_;
  std::auto_ptr<LineRawParser> lr_parser_;
};

#endif
