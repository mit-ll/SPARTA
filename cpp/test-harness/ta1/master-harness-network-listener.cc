//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of MasterHarnessNetworkListener
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

#include "master-harness-network-listener.h"

////////////////////////////////////////////////////////////////////////////////
// MasterHarnessProtocolStack
////////////////////////////////////////////////////////////////////////////////

MasterHarnessProtocolStack::MasterHarnessProtocolStack(
    NetworkConnection* connection)
    : NetworkProtocolStack(connection),
      run_script_command_(new THRunScriptCommand(GetNumberedCommandSender())) {
}

////////////////////////////////////////////////////////////////////////////////
// MasterHarnessNetworkListener
////////////////////////////////////////////////////////////////////////////////

MasterHarnessNetworkListener::MasterHarnessNetworkListener()
    : client_connected_(false) {
}

void MasterHarnessNetworkListener::StartServer(EventLoop* event_loop,
                                               HostPort listen_addr_port) {
  event_loop_ = event_loop;

  network_server_.reset(
      new NetworkServer(
          listen_addr_port, event_loop_,
          boost::bind(&MasterHarnessNetworkListener::ConnectionMade,
                      this, _1, _2)));
}

void MasterHarnessNetworkListener::ConnectionMade(
    size_t connection_id, NetworkConnection* connection) {
  CHECK(protocols_.get() == NULL)
    << "There is already an active connection to this test harness server.";
  protocols_.reset(new MasterHarnessProtocolStack(connection));
  client_connected_.Set(true);
}

void MasterHarnessNetworkListener::WaitForConnection() {
  client_connected_.Wait(true);
}
