//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Sets up a protocol stack for the test harness component
//                     that acts as the "master" 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_MASTER_HARNESS_NETWORK_LISTENER_H_
#define CPP_TEST_HARNESS_TA1_MASTER_HARNESS_NETWORK_LISTENER_H_

#include <boost/thread.hpp>
#include <memory>

#include "common/network-server.h"
#include "test-harness/common/network-protocol-stack.h"
#include "test-harness/common/th-run-script-command.h"
#include "common/conditions.h"

class EventLoop;
class ProtocolExtensionManager;
class ReadyMonitor;
class NumberedCommandSender;

/// The set of commands we need to support on our network connection.
class MasterHarnessProtocolStack : public NetworkProtocolStack {
  public:
   MasterHarnessProtocolStack(NetworkConnection* connection);
   virtual ~MasterHarnessProtocolStack() {}

   THRunScriptCommand* GetRunScriptCommand() {
     return run_script_command_.get();
   }

  private:
   std::unique_ptr<THRunScriptCommand> run_script_command_;
};

/// One test harness component is the "master". It initiates all tests scripts
/// either by starting them itself or by asking other test harness components
/// to do things. In order to do that it has to communicate over the network
/// with the other components. This sets up a server that listens on a port for
/// connections for other network components. When a connection is established
/// this builds a protocol stack with a set of command handlers "at the top"
/// that can send commands to other test harness components.
class MasterHarnessNetworkListener {
 public:
  MasterHarnessNetworkListener();
  virtual ~MasterHarnessNetworkListener() {}
  void StartServer(EventLoop* event_loop, HostPort listen_addr_port);

  /// Blocks until the other test harness component has connected.
  void WaitForConnection();

  MasterHarnessProtocolStack* GetProtocolStack() {
    return protocols_.get();
  }

  void StopListening() const {
    network_server_->StopListening();
  }

 private:
  /// Called when a client connects to this server.
  void ConnectionMade(size_t connection_id, NetworkConnection* connection);

  EventLoop* event_loop_;
  std::auto_ptr<NetworkServer> network_server_;
  /// For TA1 we expect only a single network connection so we have only a single
  /// one of these.
  std::auto_ptr<MasterHarnessProtocolStack> protocols_;
  SimpleCondition<bool> client_connected_;
};


#endif
